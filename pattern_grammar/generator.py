"""
Генерация случайных данных для Pattern Grammar.

Позволяет генерировать случайные строки, соответствующие правилам грамматики.

Пример:
    from pattern_grammar import Pattern

    pattern = Pattern('''
        digit ::= [0-9]
        pin   ::= digit{4}
    ''')
    print(pattern.generate('pin'))  # "3847"
    print(pattern.generate('pin', count=5))  # ["1234", "5678", ...]
"""

import random
from typing import Dict, List, Optional, Set

from .constants import BUILTIN_CLASSES, GENERATOR_UNICODE_WEIGHT, GENERATOR_MAX_DEPTH
from .parser import BNFParser
from .generator_helpers import GeneratorHelpers


class GrammarGenerator:
    """
    Генератор случайных строк по правилам Pattern Grammar.

    Работает с уже распарсенными правилами (без компиляции в regex/Lark).
    Для каждого правила генерация идёт рекурсивно через BNF-токены.

    Вспомогательная логика вынесена в классы-хелперы:
    - CharClassGenerator — символьные классы [abc]
    - SimpleGenerator — встроенные классы и escape-последовательности
    - UnicodeGenerator — UNICODE.* классы (требует модуль 'regex')
    """

    def __init__(
        self,
        rules: Dict[str, List[str]],
        regex_rules: Set[str],
        recursive_rules: Set[str],
        parser: BNFParser,
    ):
        self.rules = rules
        self.regex_rules = regex_rules
        self.recursive_rules = recursive_rules
        self.parser = parser
        self._depth = 0
        self._max_depth = GENERATOR_MAX_DEPTH  # Защита от бесконечной рекурсии
        self._generators = GeneratorHelpers()

    def generate(
        self,
        rule_name: str,
        count: int = 1,
        max_depth: Optional[int] = None,
    ) -> List[str]:
        """
        Генерирует случайные строки для правила.

        :param rule_name: Имя правила
        :param count: Количество строк для генерации
        :param max_depth: Максимальная глубина рекурсии (по умолчанию 20)
        :return: Список сгенерированных строк
        """
        if max_depth is not None:
            self._max_depth = max_depth

        results: list = []
        for _ in range(count):
            self._depth = 0
            result = self._generate_rule(rule_name, set())
            results.append(result)

        return results

    def _generate_rule(self, rule_name: str, visited: Set[str]) -> str:
        """Генерирует строку для правила."""
        if rule_name in visited:
            # Циклическая зависность — возвращаем пустую строку
            return ''

        new_visited = visited | {rule_name}

        if rule_name in self.regex_rules:
            return self._generate_regex_rule(rule_name, new_visited)

        if rule_name in self.recursive_rules:
            return self._generate_recursive_rule(rule_name, new_visited)

        return ''

    def _generate_regex_rule(self, rule_name: str, visited: Set[str]) -> str:
        """Генерирует строку для нерекурсивного правила."""
        tokens = self.rules.get(rule_name, [])
        if not tokens:
            return ''

        parts: list = []
        i = 0

        while i < len(tokens):
            token = tokens[i]

            if token == '|':
                i += 1
                continue

            next_token = tokens[i + 1] if i + 1 < len(tokens) else None

            # Обработка квантификаторов
            if next_token in ('*', '+', '?'):
                generated = self._generate_token(token, visited)
                if next_token == '*':
                    count = random.randint(0, 3)
                    parts.append(generated * count if count > 0 else '')
                elif next_token == '+':
                    count = random.randint(1, 3)
                    parts.append(generated * count)
                else:  # ?
                    if random.random() < GENERATOR_UNICODE_WEIGHT:
                        parts.append(generated)
                i += 2
                continue

            # Обработка braced квантификаторов {n}, {n,m}
            is_braced_token = (next_token and next_token.startswith('{') and next_token.endswith('}'))
            if is_braced_token:
                generated = self._generate_token(token, visited)
                content = next_token[1:-1]
                if ',' in content:
                    parts_str = content.split(',')
                    min_val = int(parts_str[0].strip())
                    max_val = int(parts_str[1].strip())
                    count = random.randint(min_val, max_val)
                else:
                    count = int(content)
                parts.append(generated * count)
                i += 2
                continue

            # Обработка группировки
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

                group_result = self._generate_tokens_list(group_tokens, visited)
                group_result = group_result.replace(' ', '')

                next_tok = tokens[j] if j < len(tokens) else None
                if next_tok == '*':
                    count = random.randint(0, 3)
                    parts.append(group_result * count if count > 0 else '')
                elif next_tok == '+':
                    count = random.randint(1, 3)
                    parts.append(group_result * count)
                elif next_tok == '?':
                    if random.random() < GENERATOR_UNICODE_WEIGHT:
                        parts.append(group_result)
                else:
                    parts.append(group_result)

                i = j + 1
                continue

            parts.append(self._generate_token(token, visited))
            i += 1

        return ''.join(parts)

    def _generate_recursive_rule(
        self, rule_name: str, visited: Set[str]
    ) -> str:
        """Генерирует строку для рекурсивного правила."""
        if self._depth >= self._max_depth:
            return ''

        self._depth += 1
        result = self._generate_regex_rule(rule_name, visited)
        self._depth -= 1
        return result

    def _generate_tokens_list(
        self, tokens: List[str], visited: Set[str]
    ) -> str:
        """Генерирует строку из списка токенов (для группировки)."""
        parts: list = []
        i = 0

        while i < len(tokens):
            token = tokens[i]

            if token == '|':
                # Выбираем одну альтернативу
                i += 1
                continue

            next_token = tokens[i + 1] if i + 1 < len(tokens) else None

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

                inner_result = self._generate_tokens_list(inner_tokens, visited)
                inner_result = inner_result.replace(' ', '')

                next_tok = tokens[j] if j < len(tokens) else None
                if next_tok == '*':
                    count = random.randint(0, 2)
                    parts.append(inner_result * count if count > 0 else '')
                elif next_tok == '+':
                    count = random.randint(1, 2)
                    parts.append(inner_result * count)
                elif next_tok == '?':
                    if random.random() < GENERATOR_UNICODE_WEIGHT:
                        parts.append(inner_result)
                else:
                    parts.append(inner_result)

                i = j + 1
                continue

            if next_token in ('*', '+', '?'):
                generated = self._generate_token(token, visited)
                if next_token == '*':
                    count = random.randint(0, 2)
                    parts.append(generated * count if count > 0 else '')
                elif next_token == '+':
                    count = random.randint(1, 2)
                    parts.append(generated * count)
                else:
                    if random.random() < GENERATOR_UNICODE_WEIGHT:
                        parts.append(generated)
                i += 2
                continue

            is_braced_token = (next_token and next_token.startswith('{') and next_token.endswith('}'))
            if is_braced_token:
                generated = self._generate_token(token, visited)
                content = next_token[1:-1]
                if ',' in content:
                    parts_str = content.split(',')
                    min_val = int(parts_str[0].strip())
                    max_val = int(parts_str[1].strip())
                    count = random.randint(min_val, max_val)
                else:
                    count = int(content)
                parts.append(generated * count)
                i += 2
                continue

            parts.append(self._generate_token(token, visited))
            i += 1

        return ''.join(parts)

    def _generate_token(self, token: str, visited: Set[str]) -> str:
        """Генерирует строку для одного токена (делегирование хелперам)."""
        # Ссылка на правило
        if token in self.rules:
            return self._generate_rule(token, visited)

        # Встроенный класс
        if token.lower() in BUILTIN_CLASSES:
            return self._generators.simple.generate_builtin(token.lower())

        # Символьный класс [...]
        is_char_class = (token.startswith('[') and token.endswith(']'))
        if is_char_class:
            return self._generators.char_class.generate_char_class(token)

        # Escape-последовательность
        if token.startswith('\\'):
            return self._generators.simple.generate_escape(token)

        # Строковый литерал
        is_string_literal = ((token.startswith('"') and token.endswith('"')) or \
           (token.startswith("'") and token.endswith("'")))
        if is_string_literal:
            content = token[1:-1]
            return content

        # Квантификатор/braced — пропускаем (обрабатываются выше)
        is_braced_token = (token.startswith('{') and token.endswith('}'))
        if is_braced_token:
            return token

        # Одиночные спецсимволы — пропускаем
        return ''
