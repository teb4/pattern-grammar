"""
Конвертер Pattern Grammar → Lark грамматика

Ключевое исправление: regex_rules объявляются как ТЕРМИНАЛЫ (ЗАГЛАВНЫЕ),
а не как правила (строчные), что соответствует синтаксису Lark.
"""
from typing import Dict, List, Set, Optional

from .regex_converter import RegexConverter
from .unicode import expand_unicode_in_char_class
from .constants import (
    EMPTY_DOUBLE_QUOTE,
    EMPTY_SINGLE_QUOTE,
    LARK_ESCAPED_CHARS,
    LARK_IGNORE_DIRECTIVE,
    LARK_ALT_SEPARATOR,
    REGEX_RULE_DELIM,
    RULE_PREFIX,
    RULE_NOT_FOUND,
)


class LarkConverter:
    """Конвертер БНФ → Lark грамматика"""

    def __init__(self, rules: Dict[str, List[str]],
                 recursive_rules: Optional[Set[str]] = None,
                 regex_rules: Optional[Set[str]] = None,
                 parser=None):
        self.rules = rules
        self.recursive_rules = recursive_rules or set()
        self.regex_rules = regex_rules or set()
        self.parser = parser
        self.empty_counter = 0
        self._regex_cache: Dict[str, str] = {}

    def convert(self, rule_name: str) -> str:
        if rule_name not in self.rules:
            raise ValueError(f"{RULE_PREFIX}'{rule_name}'{RULE_NOT_FOUND}")

        # Собрать все зависимости (встроено вместо _collect_all_dependencies)
        visited: Set[str] = set()
        dependencies: Set[str] = set()
        stack = [rule_name]
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            for token in self.rules.get(current, []):
                if token in self.rules:
                    dependencies.add(token)
                    stack.append(token)
        dependencies.add(rule_name)

        grammar_lines: list = []
        grammar_lines.append(LARK_IGNORE_DIRECTIVE)
        grammar_lines.append("")

        for dep in sorted(dependencies):
            if dep in self.regex_rules:
                continue

            tokens = self.rules.get(dep, [])

            is_simple_char_class = len(tokens) == 1 and tokens[0].startswith('[') and tokens[0].endswith(']')

            if is_simple_char_class:
                continue

            rule_def = self._expand_rule(dep, set())
            rule_def = self._handle_empty_alternatives(rule_def)
            if rule_def:
                grammar_lines.append(f"{dep}: {rule_def}")

        grammar_lines.append("")

        for dep in sorted(dependencies):
            if dep in self.regex_rules:
                # Regex через RegexConverter (встроено вместо _get_regex)
                try:
                    if dep not in self._regex_cache:
                        converter = RegexConverter(self.rules, self.regex_rules, self.parser)
                        raw = converter.convert(dep)
                        if self.parser:
                            raw = self.parser.restore_special_chars(raw)
                        self._regex_cache[dep] = raw
                    regex_str = self._regex_cache[dep]
                    grammar_lines.append(f"{dep.upper()}{REGEX_RULE_DELIM}{regex_str}/")
                except Exception:
                    tokens = self.rules.get(dep, [])
                    if len(tokens) == 1:
                        grammar_lines.append(f"{dep.upper()}{REGEX_RULE_DELIM}{tokens[0]}/")
                continue

            tokens = self.rules.get(dep, [])
            is_simple_char_class = len(tokens) == 1 and tokens[0].startswith('[') and tokens[0].endswith(']')

            if is_simple_char_class:
                grammar_lines.append(f"{dep.upper()}{REGEX_RULE_DELIM}{tokens[0]}/")

        return '\n'.join(grammar_lines)

    def _handle_empty_alternatives(self, rule_def: str) -> str:
        """Обрабатывает пустые альтернативы в правиле"""
        has_empty_pipe = ' | " "' in rule_def or " | ''" in rule_def
        is_only_empty = rule_def == EMPTY_DOUBLE_QUOTE or rule_def == EMPTY_SINGLE_QUOTE

        needs_processing = (not has_empty_pipe and not is_only_empty)
        if needs_processing:
            return rule_def

        parts = rule_def.split(LARK_ALT_SEPARATOR)
        non_empty_parts = [p.strip() for p in parts if p.strip() and p.strip() not in [EMPTY_DOUBLE_QUOTE, EMPTY_SINGLE_QUOTE]]

        if not non_empty_parts:
            raise ValueError(f"Правило содержит только пустые альтернативы: {rule_def}")
        is_single_alt = (len(non_empty_parts) == 1 and len(parts) == 2)
        if is_single_alt:
            return f'({non_empty_parts[0]})?'
        else:
            return LARK_ALT_SEPARATOR.join(non_empty_parts)

    def _expand_rule(self, rule_name: str, visited: Set[str]) -> str:
        if rule_name in visited:
            return rule_name

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

                next_token = tokens[j] if j < len(tokens) else None
                group_str = self._process_tokens(group_tokens, visited)
                current_alt.append(f'({group_str})')

                is_quantifier = next_token in ('*', '+', '?')

                if is_quantifier:
                    current_alt[-1] += next_token
                    i = j + 1
                else:
                    i = j
                continue

            next_token = tokens[i + 1] if i + 1 < len(tokens) else None

            is_double_quote = (token.startswith('"') and token.endswith('"'))
            is_single_quote = (token.startswith("'") and token.endswith("'"))
            is_string_literal = is_double_quote or is_single_quote

            if is_string_literal:
                lark_token = self._token_to_lark(token, visited)
                if lark_token is not None:
                    current_alt.append(lark_token)
                i += 1
                continue

            is_quantifier = next_token in ('*', '+', '?')

            if is_quantifier:
                current_alt.append(self._handle_quantifier(token, next_token, visited))
                i += 2
                continue

            lark_token = self._token_to_lark(token, visited)
            if lark_token is not None:
                current_alt.append(lark_token)
            i += 1

        if current_alt:
            expr_parts.append(current_alt)

        visited.discard(rule_name)

        if len(expr_parts) == 1:
            result = ' '.join(expr_parts[0])
        else:
            alts = [' '.join(alt) for alt in expr_parts]
            result = LARK_ALT_SEPARATOR.join(alts)

        return result

    def _process_tokens(self, tokens: List[str], visited: Set[str]) -> str:
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
                    result.append(f'({inner_str}){next_token}')
                    i = j + 1
                else:
                    result.append(f'({inner_str})')
                    i = j
                continue

            next_token = tokens[i + 1] if i + 1 < len(tokens) else None

            is_double_quote = (token.startswith('"') and token.endswith('"'))
            is_single_quote = (token.startswith("'") and token.endswith("'"))
            is_string_literal = is_double_quote or is_single_quote

            if is_string_literal:
                lark_token = self._token_to_lark(token, visited)
                if lark_token is not None:
                    result.append(lark_token)
                i += 1
                continue

            is_quantifier = next_token in ('*', '+', '?')

            if is_quantifier:
                result.append(self._handle_quantifier(token, next_token, visited))
                i += 2
                continue

            lark_token = self._token_to_lark(token, visited)
            if lark_token is not None:
                result.append(lark_token)
            i += 1

        return ' '.join(result)

    def _handle_quantifier(self, token: str, next_token: Optional[str], visited: Set[str]) -> str:
        is_char_class = token.startswith('[') and token.endswith(']')

        if is_char_class:
            return f'/{token}{next_token}/'
        else:
            sub_expr = self._token_to_lark(token, visited)
            return f'{sub_expr}{next_token}'

    def _token_to_lark(self, token: str, visited: Optional[Set[str]] = None) -> Optional[str]:
        is_rule = token in self.rules

        if is_rule:
            if token in self.regex_rules:
                return token.upper()

            tokens = self.rules[token]
            is_simple_class = len(tokens) == 1 and tokens[0].startswith('[') and tokens[0].endswith(']')

            if is_simple_class:
                return token.upper()
            return token

        is_empty = token == EMPTY_DOUBLE_QUOTE or token == EMPTY_SINGLE_QUOTE

        if is_empty:
            return None

        is_char_class = token.startswith('[') and token.endswith(']')

        if is_char_class:
            expanded = expand_unicode_in_char_class(token)
            return f'/{expanded}/'

        is_escape = token.startswith('\\')

        if is_escape:
            return f'/{token}/'

        is_double_quote = token.startswith('"') and token.endswith('"') and len(token) >= 2

        if is_double_quote:
            content = token[1:-1]
            if not content:
                return None
            if content == '"':
                return '"\\""'
            elif content == '\\':
                return '"\\\\"'
            else:
                return f'"{content}"'

        is_single_quote = token.startswith("'") and token.endswith("'") and len(token) >= 2

        if is_single_quote:
            content = token[1:-1]
            if not content:
                return None
            return f'"{content}"'

        is_special = len(token) == 1 and token in LARK_ESCAPED_CHARS

        if is_special:
            return f'"{token}"'

        return token
