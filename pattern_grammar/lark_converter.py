"""
Конвертер Pattern Grammar → Lark грамматика
ИСПРАВЛЕННАЯ ВЕРСИЯ (v0.1.4)

Ключевое исправление: regex_rules объявляются как ТЕРМИНАЛЫ (ЗАГЛАВНЫЕ),
а не как правила (строчные), что соответствует синтаксису Lark.
"""
from typing import Dict, List, Set, Optional
from .regex_converter import RegexConverter


class LarkConverter:
    """Конвертер БНФ → Lark грамматика"""

    def __init__(self, rules: Dict[str, List[str]],
                 recursive_rules: Set[str] = None,
                 regex_rules: Set[str] = None,
                 parser=None):
        self.rules = rules
        self.recursive_rules = recursive_rules or set()
        self.regex_rules = regex_rules or set()
        self.parser = parser
        self.empty_counter = 0
        # Кэш regex для regex_rules
        self._regex_cache: Dict[str, str] = {}

    def _get_regex(self, rule_name: str) -> str:
        """Получает regex для regex_rule через RegexConverter"""
        if rule_name not in self._regex_cache:
            converter = RegexConverter(self.rules, self.regex_rules, self.parser)
            raw = converter.convert(rule_name)

            #print(f"DEBUG _get_regex('{rule_name}') = {repr(raw)}")

            # Восстанавливаем спецсимволы если есть парсер
            if self.parser:
                raw = self.parser.restore_special_chars(raw)
            self._regex_cache[rule_name] = raw
        return self._regex_cache[rule_name]

    def convert(self, rule_name: str) -> str:
        if rule_name not in self.rules:
            raise ValueError(f"Правило '{rule_name}' не найдено")

        dependencies = self._collect_all_dependencies(rule_name, set())
        dependencies.add(rule_name)

        grammar_lines = []
        grammar_lines.append("%ignore /\\s+/")
        grammar_lines.append("")

        # Объявляем parser rules (строчные)
        for dep in sorted(dependencies):
            if dep in self.regex_rules:
                continue  # будут объявлены как терминалы ниже

            tokens = self.rules.get(dep, [])

            # Простые символьные классы без квантификаторов — тоже терминалы
            if len(tokens) == 1 and tokens[0].startswith('[') and tokens[0].endswith(']'):
                continue

            rule_def = self._expand_rule(dep, set())
            rule_def = self._handle_empty_alternatives(rule_def)
            if rule_def:
                grammar_lines.append(f"{dep}: {rule_def}")

        grammar_lines.append("")

        # Объявляем терминалы (ЗАГЛАВНЫЕ) для regex_rules
        for dep in sorted(dependencies):
            if dep in self.regex_rules:
                try:
                    regex_str = self._get_regex(dep)
                    grammar_lines.append(f"{dep.upper()}: /{regex_str}/")
                except Exception:
                    # Fallback: простой символьный класс
                    tokens = self.rules.get(dep, [])
                    if len(tokens) == 1:
                        grammar_lines.append(f"{dep.upper()}: /{tokens[0]}/")
                continue

            # Простые символьные классы (не regex_rules) — тоже терминалы
            tokens = self.rules.get(dep, [])
            if len(tokens) == 1 and tokens[0].startswith('[') and tokens[0].endswith(']'):
                grammar_lines.append(f"{dep.upper()}: /{tokens[0]}/")

        return '\n'.join(grammar_lines)

    def _collect_all_dependencies(self, rule_name: str, visited: Set[str]) -> Set[str]:
        if rule_name in visited:
            return set()

        visited.add(rule_name)
        dependencies = set()

        for token in self.rules.get(rule_name, []):
            if token in self.rules:
                dependencies.add(token)
                dependencies.update(self._collect_all_dependencies(token, visited.copy()))

        return dependencies

    def _handle_empty_alternatives(self, rule_def: str) -> str:
        """Обрабатывает пустые альтернативы в правиле"""
        if ' | " "' not in rule_def and " | ''" not in rule_def:
            if rule_def != '" "' and rule_def != "''":
                return rule_def

        parts = rule_def.split(' | ')
        non_empty_parts = [p.strip() for p in parts if p.strip() and p.strip() not in ['" "', "''"]]

        if not non_empty_parts:
            raise ValueError(f"Правило содержит только пустые альтернативы: {rule_def}")
        elif len(non_empty_parts) == 1 and len(parts) == 2:
            return f'({non_empty_parts[0]})?'
        else:
            return ' | '.join(non_empty_parts)

    def _expand_rule(self, rule_name: str, visited: Set[str]) -> str:
        if rule_name in visited:
            return rule_name

        visited.add(rule_name)

        tokens = self.rules[rule_name]
        expr_parts = []
        current_alt = []

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
                group_tokens = []

                while j < len(tokens) and depth > 0:
                    if tokens[j] == '(':
                        depth += 1
                    elif tokens[j] == ')':
                        depth -= 1
                    if depth > 0:
                        group_tokens.append(tokens[j])
                    j += 1

                next_token = tokens[j] if j < len(tokens) else None
                group_str = self._process_tokens(group_tokens, visited)
                current_alt.append(f'({group_str})')

                if next_token in ['*', '+', '?']:
                    current_alt[-1] += next_token
                    i = j + 1
                else:
                    i = j
                continue

            next_token = tokens[i + 1] if i + 1 < len(tokens) else None

            if (token.startswith('"') and token.endswith('"')) or \
               (token.startswith("'") and token.endswith("'")):
                lark_token = self._token_to_lark(token, visited)
                if lark_token is not None:
                    current_alt.append(lark_token)
                i += 1
                continue

            if next_token in ['*', '+', '?']:
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
            result = ' | '.join(alts)

        return result

    def _process_tokens(self, tokens: List[str], visited: Set[str]) -> str:
        result = []
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
                inner_tokens = []

                while j < len(tokens) and depth > 0:
                    if tokens[j] == '(':
                        depth += 1
                    elif tokens[j] == ')':
                        depth -= 1
                    if depth > 0:
                        inner_tokens.append(tokens[j])
                    j += 1

                inner_str = self._process_tokens(inner_tokens, visited)
                next_token = tokens[j] if j < len(tokens) else None

                if next_token in ['*', '+', '?']:
                    result.append(f'({inner_str}){next_token}')
                    i = j + 1
                else:
                    result.append(f'({inner_str})')
                    i = j
                continue

            next_token = tokens[i + 1] if i + 1 < len(tokens) else None

            if (token.startswith('"') and token.endswith('"')) or \
               (token.startswith("'") and token.endswith("'")):
                lark_token = self._token_to_lark(token, visited)
                if lark_token is not None:
                    result.append(lark_token)
                i += 1
                continue

            if next_token in ['*', '+', '?']:
                result.append(self._handle_quantifier(token, next_token, visited))
                i += 2
                continue

            lark_token = self._token_to_lark(token, visited)
            if lark_token is not None:
                result.append(lark_token)
            i += 1

        return ' '.join(result)

    def _handle_quantifier(self, token: str, next_token: str, visited: Set[str]) -> str:
        if token.startswith('[') and token.endswith(']'):
            return f'/{token}{next_token}/'
        else:
            sub_expr = self._token_to_lark(token, visited)
            return f'{sub_expr}{next_token}'

    def _token_to_lark(self, token: str, visited: Set[str] = None) -> Optional[str]:
        # Ссылка на правило
        if token in self.rules:
            if token in self.regex_rules:
                return token.upper()  # терминал
            # Простые символьные классы тоже стали терминалами
            tokens = self.rules[token]
            if len(tokens) == 1 and tokens[0].startswith('[') and tokens[0].endswith(']'):
                return token.upper()
            return token  # parser rule

        # Пустые строковые литералы
        if token == '" "' or token == "''":
            return None

        # Символьные классы inline
        if token.startswith('[') and token.endswith(']'):
            return f'/{token}/'

        # Экранированные последовательности
        if token.startswith('\\'):
            return f'/{token}/'

        # Строковые литералы в двойных кавычках
        if token.startswith('"') and token.endswith('"') and len(token) >= 2:
            content = token[1:-1]
            if not content:
                return None
            if content == '"':
                return '"\\""'
            elif content == '\\':
                return '"\\\\"'
            else:
                return f'"{content}"'

        # Строковые литералы в одинарных кавычках
        if token.startswith("'") and token.endswith("'") and len(token) >= 2:
            content = token[1:-1]
            if not content:
                return None
            return f'"{content}"'

        # Спецсимволы
        special_chars = '+-*/%=<>!&|.,;:^'
        if len(token) == 1 and token in special_chars:
            return f'"{token}"'

        return token
