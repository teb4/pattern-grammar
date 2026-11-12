"""
Конвертер Pattern Grammar → Регулярное выражение
"""
import re
from typing import Dict, List, Optional, Set

from .constants import BUILTIN_CLASSES, REGEX_SPECIAL_CHARS, REGEX_NONCAP_GROUP, RULE_PREFIX, RULE_NOT_FOUND
from .unicode import expand_unicode_in_char_class, has_unicode_classes
from .regex_named_groups import RegexNamedGroupsConverter


class RegexConverter:
    """Конвертер БНФ → Регулярное выражение"""

    def __init__(
        self,
        rules: Dict[str, List[str]],
        regex_rules: Set[str],
        parser=None,
        fail_messages: Optional[Dict[str, Optional[str]]] = None,
    ):
        """
        :param rules: Словарь {имя_правила: список_токенов}
        :param regex_rules: Множество имён правил, конвертируемых в regex
        :param parser: BNFParser для восстановления спецсимволов
        :param fail_messages: Словарь {имя_правила: сообщение_ошибки}
        """
        self.rules = rules
        self.regex_rules = regex_rules
        self.parser = parser
        self.fail_messages = fail_messages or {}
        self._has_unicode: bool = False
        self._named_groups_converter = RegexNamedGroupsConverter(
            self, rules, regex_rules, fail_messages, parser
        )

    def convert(self, rule_name: str) -> str:
        """Конвертирует правило в регулярное выражение"""
        if rule_name not in self.rules:
            raise ValueError(f"{RULE_PREFIX}'{rule_name}'{RULE_NOT_FOUND}")

        # Проверяем, есть ли UNICODE-классы в этом правиле
        if has_unicode_classes(self.rules[rule_name]):
            self._has_unicode = True

        expr = self._expand(rule_name, set())

        if self.parser:
            expr = self.parser.restore_special_chars(expr, for_regex=True)

        return expr

    @property
    def has_unicode(self) -> bool:
        """Возвращает True если хотя бы одно правило содержало UNICODE-класс."""
        return self._has_unicode or self._named_groups_converter.has_unicode


    def convert_with_named_groups(self, rule_name: str) -> tuple:
        """
        Конвертирует правило в regex с именованными группами для вложенных
        правил с @fail. Реализация вынесена в RegexNamedGroupsConverter.

        :return: (regex_str, group_map)
        """
        return self._named_groups_converter.convert_with_named_groups(rule_name)
    def _expand(self, rule_name: str, visited: Set[str]) -> str:
        """Рекурсивно разворачивает правило"""
        if rule_name in visited:
            raise ValueError(f"Рекурсия в правиле '{rule_name}' при конвертации в regex")

        visited.add(rule_name)

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

                group_str = self._process_tokens(group_tokens, visited)

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
                sub_expr = self._token_to_regex(token, visited)
                needs_group = len(sub_expr) > 1 and not (sub_expr.startswith('[') and sub_expr.endswith(']'))
                if needs_group:
                    sub_expr = f'{REGEX_NONCAP_GROUP}{sub_expr})'
                current_alt.append(f'{sub_expr}{next_token}')
                i += 2
                continue

            is_braced = next_token and next_token.startswith('{') and next_token.endswith('}')

            if is_braced:
                sub_expr = self._token_to_regex(token, visited)
                needs_group = len(sub_expr) > 1 and not (sub_expr.startswith('[') and sub_expr.endswith(']'))
                if needs_group:
                    sub_expr = f'{REGEX_NONCAP_GROUP}{sub_expr})'
                current_alt.append(f'{sub_expr}{next_token}')
                i += 2
                continue

            current_alt.append(self._token_to_regex(token, visited))
            i += 1

        if current_alt:
            expr_parts.append(current_alt)

        visited.remove(rule_name)

        if len(expr_parts) == 1:
            return ''.join(expr_parts[0])
        else:
            alts = [''.join(alt) for alt in expr_parts]
            return f'{REGEX_NONCAP_GROUP}{"|".join(alts)})'

    def _process_tokens(self, tokens: List[str], visited: Set[str]) -> str:
        """Обрабатывает список токенов внутри группировки"""
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

                inner_str = self._process_tokens(inner_tokens, visited)

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
                sub_expr = self._token_to_regex(token, visited)
                needs_group = len(sub_expr) > 1 and not (sub_expr.startswith('[') and sub_expr.endswith(']'))
                if needs_group:
                    sub_expr = f'{REGEX_NONCAP_GROUP}{sub_expr})'
                result.append(f'{sub_expr}{next_token}')
                i += 2
                continue

            is_braced = next_token and next_token.startswith('{') and next_token.endswith('}')

            if is_braced:
                sub_expr = self._token_to_regex(token, visited)
                needs_group = len(sub_expr) > 1 and not (sub_expr.startswith('[') and sub_expr.endswith(']'))
                if needs_group:
                    sub_expr = f'{REGEX_NONCAP_GROUP}{sub_expr})'
                result.append(f'{sub_expr}{next_token}')
                i += 2
                continue

            result.append(self._token_to_regex(token, visited))
            i += 1

        return ''.join(result)

    def _token_to_regex(self, token: str, visited: Set[str]) -> str:
        """Преобразует токен в регулярное выражение"""

        is_rule_ref = token in self.rules and token in self.regex_rules

        if is_rule_ref:
            expanded = self._expand(token, visited)
            needs_group = '|' in expanded
            is_bracket = expanded.startswith('[') and expanded.endswith(']')
            needs_named_group = (needs_group and not is_bracket)
            if needs_named_group:
                return f'{REGEX_NONCAP_GROUP}{expanded})'
            return expanded

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
            content = token[1:-1]
            return re.escape(content)

        is_braced = token.startswith('{') and token.endswith('}')

        if is_braced:
            content = token[1:-1]
            if ',' in content:
                parts = content.split(',')
                is_valid_range = len(parts) == 2 and all(p.strip().isdigit() for p in parts)
                if is_valid_range:
                    return token
            elif content.isdigit():
                return token

        is_special = len(token) == 1 and token in REGEX_SPECIAL_CHARS

        if is_special:
            return re.escape(token)

        return re.escape(token)
