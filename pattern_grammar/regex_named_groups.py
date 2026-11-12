"""
Конвертер Pattern Grammar → Регулярное выражение с именованными группами.

Ветка обработки вложенных правил с @fail: оборачивает ссылки на такие
правила в именованные группы Lark/regex (?P<name>...).
"""
import re
from typing import Dict, List, Optional, Set

from .constants import BUILTIN_CLASSES, REGEX_SPECIAL_CHARS, REGEX_NONCAP_GROUP, RULE_PREFIX, RULE_NOT_FOUND
from .unicode import expand_unicode_in_char_class, has_unicode_classes


class RegexNamedGroupsConverter:
    """Конвертер regex с именованными группами для вложенных @fail правил."""

    def __init__(
        self,
        parent,
        rules: Dict[str, List[str]],
        regex_rules: Set[str],
        fail_messages: Optional[Dict[str, Optional[str]]] = None,
        parser=None,
    ):
        self._parent = parent
        self.rules = rules
        self.regex_rules = regex_rules
        self.fail_messages = fail_messages or {}
        self.parser = parser
        self._has_unicode: bool = False

    @property
    def has_unicode(self) -> bool:
        """Возвращает True если хотя бы одно правило содержало UNICODE-класс."""
        return self._has_unicode

    def _collect_inner_fail_rules(
        self, rule_name: str
    ) -> List[str]:
        """
        Возвращает список имён вложенных правил с @fail
        в порядке их появления в токенах.
        """
        results: list = []
        seen: set = set()
        for token in self.rules.get(rule_name, []):
            if token in ('|', '(', ')'):
                continue
            if token.startswith(('"', "'", '{', '\\')):
                continue
            is_char_class = (token.startswith('[') and token.endswith(']'))
            if is_char_class:
                continue
            if token.lower() in BUILTIN_CLASSES:
                continue
            is_inner_fail_rule = (token in self.regex_rules
                and token not in seen
                and token in self.fail_messages
                and self.fail_messages[token])
            if is_inner_fail_rule:
                seen.add(token)
                results.append(token)
        return results

    def _token_to_regex_with_named_groups(
        self, token: str, visited: Set[str], named_groups: Set[str]
    ) -> str:
        """
        Преобразует токен в regex.
        Если токен — ссылка на правило с @fail, оборачивает в именованную группу.
        """
        is_rule_ref = token in self.rules and token in self.regex_rules
        is_named_group_ref = (is_rule_ref and token in named_groups)
        if is_named_group_ref:
            expanded = self._parent._expand(token, visited)
            return f"(?P<{token}>{expanded})"

        is_builtin = token.lower() in BUILTIN_CLASSES
        if is_builtin:
            return BUILTIN_CLASSES[token.lower()]

        is_char_class = token.startswith('[') and token.endswith(']')
        if is_char_class:
            return expand_unicode_in_char_class(token)

        is_escape = token.startswith('\\')
        if is_escape:
            return token

        is_double_quote = token.startswith('"') and token.endswith('"')
        is_single_quote = token.startswith("'") and token.endswith("'")
        is_string_literal = (is_double_quote or is_single_quote)
        if is_string_literal:
            return re.escape(token[1:-1])

        is_braced = token.startswith('{') and token.endswith('}')
        if is_braced:
            content = token[1:-1]
            if ',' in content:
                parts = content.split(',')
                is_repeat_quantifier = (len(parts) == 2 and all(p.strip().isdigit() for p in parts))
                if is_repeat_quantifier:
                    return token
            elif content.isdigit():
                return token

        is_special = len(token) == 1 and token in REGEX_SPECIAL_CHARS
        if is_special:
            return re.escape(token)

        return re.escape(token)

    def convert_with_named_groups(
        self, rule_name: str
    ) -> tuple:
        """
        Конвертирует правило в regex с именованными группами
        для вложенных правил с @fail.

        Возвращает (regex_str, group_map), где group_map —
        словарь {inner_rule_name: inner_rule_name}.
        """
        if rule_name not in self.rules:
            raise ValueError(f"{RULE_PREFIX}'{rule_name}'{RULE_NOT_FOUND}")

        has_unicode = has_unicode_classes(self.rules[rule_name])
        if has_unicode:
            self._has_unicode = True

        inner_fails = self._collect_inner_fail_rules(rule_name)
        named_groups: set = set(inner_fails)

        if not named_groups:
            expr = self._parent.convert(rule_name)
            return expr, {}

        visited: set = set()
        tokens = self.rules[rule_name]
        expr_parts: list = []
        current_alt: list = []

        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token == '|':
                if current_alt:
                    expr_parts.append(current_alt)
                current_alt = []
                i += 1
                continue

            if token == '(':
                depth = 1
                j = i + 1
                group_tokens: list = []
                scanning = j < len(tokens) and depth > 0
                while scanning:
                    if tokens[j] == '(':
                        depth += 1
                    elif tokens[j] == ')':
                        depth -= 1
                    if depth > 0:
                        group_tokens.append(tokens[j])
                    j += 1
                    scanning = j < len(tokens) and depth > 0

                group_str = self._process_tokens_with_named_groups(
                    group_tokens, visited, named_groups
                )

                next_token = tokens[j] if j < len(tokens) else None
                is_quantifier = next_token in ('*', '+', '?')
                if is_quantifier:
                    current_alt.append(f'{REGEX_NONCAP_GROUP}{group_str}){next_token}')
                    i = j + 1
                else:
                    current_alt.append(f'{REGEX_NONCAP_GROUP}{group_str})')
                    i = j
                continue

            next_token = tokens[i + 1] if i + 1 < len(tokens) else None
            is_quantifier = next_token in ('*', '+', '?')

            if is_quantifier:
                sub_expr = self._token_to_regex_with_named_groups(
                    token, visited, named_groups
                )
                needs_group = len(sub_expr) > 1 and not (
                    sub_expr.startswith('[') and sub_expr.endswith(']')
                )
                if needs_group:
                    sub_expr = f'{REGEX_NONCAP_GROUP}{sub_expr})'
                current_alt.append(f'{sub_expr}{next_token}')
                i += 2
                continue

            is_braced = (
                next_token
                and next_token.startswith('{')
                and next_token.endswith('}')
            )
            if is_braced:
                sub_expr = self._token_to_regex_with_named_groups(
                    token, visited, named_groups
                )
                needs_group = len(sub_expr) > 1 and not (
                    sub_expr.startswith('[') and sub_expr.endswith(']')
                )
                if needs_group:
                    sub_expr = f'{REGEX_NONCAP_GROUP}{sub_expr})'
                current_alt.append(f'{sub_expr}{next_token}')
                i += 2
                continue

            current_alt.append(
                self._token_to_regex_with_named_groups(
                    token, visited, named_groups
                )
            )
            i += 1

        if current_alt:
            expr_parts.append(current_alt)

        if len(expr_parts) == 1:
            result = ''.join(expr_parts[0])
        else:
            alts = [''.join(alt) for alt in expr_parts]
            result = f'{REGEX_NONCAP_GROUP}{"|".join(alts)})'

        if self.parser:
            result = self.parser.restore_special_chars(result, for_regex=True)

        group_map = {rule: rule for rule in inner_fails}
        return result, group_map

    def _process_tokens_with_named_groups(
        self,
        tokens: List[str],
        visited: Set[str],
        named_groups: Set[str],
    ) -> str:
        """Обрабатывает токены внутри группировки с именованными группами."""
        result: list = []
        i = 0

        while i < len(tokens):
            token = tokens[i]

            if token == '|':
                result.append('|')
                i += 1
                continue

            if token == '(':
                depth = 1
                j = i + 1
                inner_tokens: list = []
                scanning = j < len(tokens) and depth > 0
                while scanning:
                    if tokens[j] == '(':
                        depth += 1
                    elif tokens[j] == ')':
                        depth -= 1
                    if depth > 0:
                        inner_tokens.append(tokens[j])
                    j += 1
                    scanning = j < len(tokens) and depth > 0

                inner_str = self._process_tokens_with_named_groups(
                    inner_tokens, visited, named_groups
                )

                next_token = tokens[j] if j < len(tokens) else None
                is_quantifier = next_token in ('*', '+', '?')
                if is_quantifier:
                    result.append(f'{REGEX_NONCAP_GROUP}{inner_str}){next_token}')
                    i = j + 1
                else:
                    result.append(f'{REGEX_NONCAP_GROUP}{inner_str})')
                    i = j
                continue

            next_token = tokens[i + 1] if i + 1 < len(tokens) else None
            is_quantifier = next_token in ('*', '+', '?')

            if is_quantifier:
                sub_expr = self._token_to_regex_with_named_groups(
                    token, visited, named_groups
                )
                needs_group = len(sub_expr) > 1 and not (
                    sub_expr.startswith('[') and sub_expr.endswith(']')
                )
                if needs_group:
                    sub_expr = f'{REGEX_NONCAP_GROUP}{sub_expr})'
                result.append(f'{sub_expr}{next_token}')
                i += 2
                continue

            is_braced = (
                next_token
                and next_token.startswith('{')
                and next_token.endswith('}')
            )
            if is_braced:
                sub_expr = self._token_to_regex_with_named_groups(
                    token, visited, named_groups
                )
                needs_group = len(sub_expr) > 1 and not (
                    sub_expr.startswith('[') and sub_expr.endswith(']')
                )
                if needs_group:
                    sub_expr = f'{REGEX_NONCAP_GROUP}{sub_expr})'
                result.append(f'{sub_expr}{next_token}')
                i += 2
                continue

            result.append(
                self._token_to_regex_with_named_groups(
                    token, visited, named_groups
                )
            )
            i += 1

        return ''.join(result)
