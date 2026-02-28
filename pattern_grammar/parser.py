"""
Парсер Pattern Grammar с поддержкой:
Символьных классов [abc] как единого токена
Квантификаторов {n,m} как единого токена
Литералов в кавычках "текст" как единого токена
"""
from typing import Dict, List

class BNFParser:
    """Парсер БНФ-грамматики"""

    # Карта замены проблемных символов на плейсхолдеры
    SPECIAL_CHARS_MAP = {
        '#': '___HASH___',
        # Можно добавить другие символы при необходимости
        # '$': '___DOLLAR___',
        # '&': '___AMP___',
    }

    def __init__(self):
        self.rules: Dict[str, List[str]] = {}  # Имя → токены тела
        self.raw_rules: Dict[str, str] = {}    # Имя → исходный текст

    def parse(self, grammar_text: str):
        """Парсит текст грамматики в правила"""
        self.rules.clear()
        self.raw_rules.clear()

        raw_lines = grammar_text.strip().split('\n')

        # Склеиваем многострочные правила: строки с отступом — продолжение предыдущего
        merged_lines = []
        for raw_line in raw_lines:
            stripped = raw_line.strip()
            if not stripped:
                merged_lines.append((len(merged_lines) + 1, ''))
                continue
            # Строка с отступом и без ::= — продолжение предыдущего правила
            if raw_line[0].isspace() and '::=' not in raw_line and ':=' not in raw_line:
                if merged_lines:
                    prev_num, prev_line = merged_lines[-1]
                    merged_lines[-1] = (prev_num, prev_line + ' ' + stripped)
                    continue
            merged_lines.append((len(merged_lines) + 1, raw_line))

        for line_num, line in merged_lines:
            # Удаляем комментарии — только вне символьных классов и строковых литералов
            if '#' in line:
                bracket_depth = 0
                in_str = False
                str_char = None
                comment_pos = -1
                i = 0
                while i < len(line):
                    ch = line[i]
                    if in_str:
                        if ch == '\\' and i + 1 < len(line):
                            i += 2
                            continue
                        if ch == str_char:
                            in_str = False
                    elif ch in ('"', "'"):
                        in_str = True
                        str_char = ch
                    elif ch == '[':
                        bracket_depth += 1
                    elif ch == ']':
                        bracket_depth -= 1
                    elif ch == '#' and bracket_depth == 0:
                        comment_pos = i
                        break
                    i += 1
                if comment_pos >= 0:
                    line = line[:comment_pos]

            line = line.strip()

            if not line:
                continue

            # Заменяем проблемные символы на плейсхолдеры
            for original, placeholder in self.SPECIAL_CHARS_MAP.items():
                line = line.replace(original, placeholder)

            # Ищем оператор ::= или :=
            if '::=' in line:
                sep = '::='
            elif ':=' in line:
                sep = ':='
            else:
                continue

            try:
                name, body = line.split(sep, 1)
                name = name.strip()
                body = body.strip()

                if not name:
                    raise SyntaxError(f"Строка {line_num}: пустое имя правила")

                if not body:
                    raise SyntaxError(f"Строка {line_num}: пустое тело правила '{name}'")

                tokens = self._tokenize(body)

                self.rules[name] = tokens
                self.raw_rules[name] = body

            except SyntaxError:
                raise
            except Exception as e:
                raise SyntaxError(f"Строка {line_num}: ошибка парсинга - {e}")

    def _tokenize(self, body: str) -> List[str]:
        """
        Разбивает тело правила на токены.

        Особенности:
        - Символьные классы [abc] → один токен '[abc]'
        - Квантификаторы {n}, {n,m} → один токен '{n,m}'
        - Литералы в кавычках "текст" → один токен "текст" (в кавычках)
        - Экранированные кавычки внутри литералов: "\"" → токен '"'
        - Спецсимволы ()|*+? → отдельные токены
        """
        tokens = []
        current = ''
        i = 0
        length = len(body)
        in_quotes = False
        quote_char = None

        while i < length:
            char = body[i]

            # 1. Обработка символьных классов [ ... ]
            if not in_quotes and char == '[':
                if current:
                    parts = current.split()
                    tokens.extend(parts)
                    current = ''

                class_start = i
                depth = 1
                i += 1

                while i < length and depth > 0:
                    if body[i] == '[':
                        depth += 1
                    elif body[i] == ']':
                        depth -= 1
                    i += 1

                if depth > 0:
                    raise SyntaxError(f"Незакрытый символьный класс: {body[class_start:]}")

                char_class = body[class_start:i]
                tokens.append(char_class)
                continue

            # 2. Обработка квантификаторов { ... }
            if not in_quotes and char == '{':
                if current:
                    parts = current.split()
                    tokens.extend(parts)
                    current = ''

                quant_start = i
                depth = 1
                i += 1

                while i < length and depth > 0:
                    if body[i] == '{':
                        depth += 1
                    elif body[i] == '}':
                        depth -= 1
                    i += 1

                if depth > 0:
                    raise SyntaxError(f"Незакрытый квантификатор: {body[quant_start:]}")

                quantifier = body[quant_start:i]
                tokens.append(quantifier)
                continue

            # 3. Обработка литералов в кавычках
            if not in_quotes and char in ('"', "'"):
                if current:
                    parts = current.split()
                    tokens.extend(parts)
                    current = ''

                in_quotes = True
                quote_char = char
                i += 1
                continue

            if in_quotes:
                # Экранированный символ: \X → добавляем X в содержимое
                # (backslash не сохраняем — он служебный)
                if char == '\\' and i + 1 < length:
                    next_char = body[i + 1]
                    if next_char == quote_char:
                        # Экранированная закрывающая кавычка → добавляем кавычку
                        current += next_char
                        i += 2
                        continue
                    elif next_char == '\\':
                        # Экранированный backslash → добавляем один backslash
                        current += '\\'
                        i += 2
                        continue
                    else:
                        # Прочие экранированные последовательности → сохраняем как есть
                        current += body[i:i+2]
                        i += 2
                        continue

                if char == quote_char:
                    # Конец литерала
                    if quote_char == '"':
                        tokens.append(f'"{current}"')
                    else:
                        tokens.append(f"'{current}'")
                    current = ''
                    in_quotes = False
                    quote_char = None
                    i += 1
                    continue

                # Обычный символ внутри литерала
                current += char
                i += 1
                continue

            # 4. Обработка пробелов
            if char.isspace() and not in_quotes:
                if current:
                    parts = current.split()
                    tokens.extend(parts)
                    current = ''
                i += 1
                continue

            # 5. Обработка спецсимволов
            if char in '()|*+?':
                if current:
                    parts = current.split()
                    tokens.extend(parts)
                    current = ''

                tokens.append(char)
                i += 1
                continue

            # 6. Обычный символ
            current += char
            i += 1

        # Обработка остатка после цикла
        if in_quotes:
            raise SyntaxError(f"Незакрытая кавычка: {quote_char}{current}")

        if current:
            parts = current.split()
            tokens.extend(parts)

        return tokens

    def get_rules(self) -> Dict[str, List[str]]:
        """Возвращает распарсенные правила"""
        return self.rules

    def restore_special_chars(self, text: str, for_regex: bool = False) -> str:
        """Восстанавливает оригинальные символы из плейсхолдеров

        :param text: Текст с плейсхолдерами
        :param for_regex: Если True, экранирует спецсимволы для regex
        """
        if for_regex:
            text = text.replace('___HASH___', r'\#')
        else:
            text = text.replace('___HASH___', '#')

        return text
