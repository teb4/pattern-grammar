"""
Конвертер Pattern Grammar → Регулярное выражение
ИСПРАВЛЕННАЯ ВЕРСИЯ (v0.1.1)
"""
import re
from typing import Dict, List, Set


class RegexConverter:
    """Конвертер БНФ → Регулярное выражение"""

    # Встроенные классы символов
    BUILTIN_CLASSES = {
        'digit': r'[0-9]',
        'digits': r'[0-9]+',
        'alpha': r'[a-zA-Z]',
        'alnum': r'[a-zA-Z0-9]',
        'word': r'[a-zA-Z0-9_]+',
        'whitespace': r'\s',
        'space': r' ',
        'tab': r'\t',
        'newline': r'\n',
    }

    def __init__(self, rules: Dict[str, List[str]], regex_rules: Set[str], parser=None):
        self.rules = rules
        self.regex_rules = regex_rules
        self.parser = parser

    def convert(self, rule_name: str) -> str:
        """Конвертирует правило в регулярное выражение"""
        if rule_name not in self.rules:
            raise ValueError(f"Правило '{rule_name}' не найдено")

        expr = self._expand(rule_name, set())
        #print(f"DEBUG convert до восстановления: {expr}")

        # Восстанавливаем оригинальные символы из плейсхолдеров
        if self.parser:
            expr = self.parser.restore_special_chars(expr, for_regex=True)

        #print(f"DEBUG convert после восстановления: {expr}")
        return expr

    def _expand(self, rule_name: str, visited: Set[str]) -> str:
        """Рекурсивно разворачивает правило"""
        if rule_name in visited:
            raise ValueError(f"Рекурсия в правиле '{rule_name}' при конвертации в regex")

        visited.add(rule_name)

        tokens = self.rules[rule_name]
        expr_parts = []
        current_alt = []

        i = 0
        while i < len(tokens):
            token = tokens[i]

            # Обработка альтернативы
            if token == '|':
                if current_alt:
                    expr_parts.append(current_alt)
                current_alt = []
                i += 1
                continue

            # Обработка группировки
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

                # Рекурсивно обрабатываем группу
                group_str = self._process_tokens(group_tokens, visited)

                # 🔧 FIX #1: Проверяем квантификатор ПОСЛЕ группы
                next_token = tokens[j] if j < len(tokens) else None
                if next_token in ['*', '+', '?']:
                    current_alt.append(f'(?:{group_str}){next_token}')
                    i = j + 1
                else:
                    current_alt.append(f'(?:{group_str})')
                    i = j
                continue

            # Обработка квантификаторов: *, +, ?
            next_token = tokens[i + 1] if i + 1 < len(tokens) else None
            if next_token in ['*', '+', '?']:
                sub_expr = self._token_to_regex(token, visited)
                if len(sub_expr) > 1 and not (sub_expr.startswith('[') and sub_expr.endswith(']')):
                    sub_expr = f'(?:{sub_expr})'
                current_alt.append(f'{sub_expr}{next_token}')
                i += 2
                continue

            # Обработка диапазонов {n}, {n,m}
            if next_token and next_token.startswith('{') and next_token.endswith('}'):
                sub_expr = self._token_to_regex(token, visited)
                if len(sub_expr) > 1 and not (sub_expr.startswith('[') and sub_expr.endswith(']')):
                    sub_expr = f'(?:{sub_expr})'
                current_alt.append(f'{sub_expr}{next_token}')
                i += 2
                continue

            # Обычный токен
            current_alt.append(self._token_to_regex(token, visited))
            i += 1

        # Добавляем последнюю альтернативу
        if current_alt:
            expr_parts.append(current_alt)

        visited.remove(rule_name)

        # Собираем результат
        if len(expr_parts) == 1:
            return ''.join(expr_parts[0])
        else:
            alts = [''.join(alt) for alt in expr_parts]
            return f'(?:{"|".join(alts)})'

    def _process_tokens(self, tokens: List[str], visited: Set[str]) -> str:
        """Обрабатывает список токенов внутри группировки"""
        result = []
        i = 0

        while i < len(tokens):
            token = tokens[i]

            if token == '|':
                result.append('|')
                i += 1
                continue

            # Обработка вложенной группы
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
                    result.append(f'(?:{inner_str}){next_token}')
                    i = j + 1
                else:
                    result.append(f'(?:{inner_str})')
                    i = j
                continue

            next_token = tokens[i + 1] if i + 1 < len(tokens) else None
            if next_token in ['*', '+', '?']:
                sub_expr = self._token_to_regex(token, visited)
                if len(sub_expr) > 1 and not (sub_expr.startswith('[') and sub_expr.endswith(']')):
                    sub_expr = f'(?:{sub_expr})'
                result.append(f'{sub_expr}{next_token}')
                i += 2
                continue

            if next_token and next_token.startswith('{') and next_token.endswith('}'):
                sub_expr = self._token_to_regex(token, visited)
                if len(sub_expr) > 1 and not (sub_expr.startswith('[') and sub_expr.endswith(']')):
                    sub_expr = f'(?:{sub_expr})'
                result.append(f'{sub_expr}{next_token}')
                i += 2
                continue

            result.append(self._token_to_regex(token, visited))
            i += 1

        return ''.join(result)

    def _token_to_regex(self, token: str, visited: Set[str]) -> str:
        """Преобразует токен в регулярное выражение"""

        #print(f"DEBUG _token_to_regex: token={repr(token)}, in_rules={token in self.rules}, in_regex_rules={token in self.regex_rules}")

        # Ссылка на другое правило
        if token in self.rules and token in self.regex_rules:
            expanded = self._expand(token, visited)
            if '|' in expanded:
                if not (expanded.startswith('(?:') and expanded.endswith(')')):
                    if not (expanded.startswith('[') and expanded.endswith(']')):
                        return f'(?:{expanded})'
            return expanded

        # Встроенные классы
        if token.lower() in self.BUILTIN_CLASSES:
            return self.BUILTIN_CLASSES[token.lower()]

        # Символьные классы — передаём как есть
        if token.startswith('[') and token.endswith(']'):
            return token

        # Экранированные последовательности
        if token.startswith('\\'):
            return token

        # 🔧 FIX #2: Литералы в кавычках — экранируем спецсимволы regex
        if (token.startswith('"') and token.endswith('"')) or (token.startswith("'") and token.endswith("'")):
            content = token[1:-1]
            return re.escape(content)

        # 🔧 FIX #4: Квантификаторы {n}, {n,m} — не экранировать
        if token.startswith('{') and token.endswith('}'):
            content = token[1:-1]
            if ',' in content:
                parts = content.split(',')
                if len(parts) == 2 and all(p.strip().isdigit() for p in parts):
                    return token
            elif content.isdigit():
                return token

        # Спецсимволы регулярных выражений
        special_chars = '.^$*+?[]\\|()'
        if len(token) == 1 and token in special_chars:
            return re.escape(token)

        # Обычный литерал
        return re.escape(token)
