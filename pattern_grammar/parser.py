"""
Парсер Pattern Grammar с поддержкой:
Символьных классов [abc] как единого токена
Квантификаторов {n,m} как единого токена
Литералов в кавычках "текст" как единого токена
Директив импорта import "путь"
"""
from typing import Dict, List, Optional

from .constants import (
    AMPERSAND_CHAR,
    AMPERSAND_PLACEHOLDER,
    DOLLAR_CHAR,
    DOLLAR_PLACEHOLDER,
    FAIL_ANNOTATION,
    HASH_CHAR,
    HASH_PLACEHOLDER,
    RULE_SEPARATOR_DOUBLE,
    RULE_SEPARATOR_SINGLE,
    TEXT_PREFIX,
)
from .importer import (
    _extract_import_name,
    _is_import_directive,
    _merge_grammar,
    _remove_imports,
    resolve_import,
)


def _strip_comment(line: str) -> str:
    """Удаляет комментарий из строки, игнорируя # внутри кавычек и символьных классов."""
    bracket_depth = 0
    in_str = False
    str_char = None
    comment_pos = -1
    i = 0
    while i < len(line):
        ch = line[i]
        if in_str:
            is_escaped_char = (ch == '\\' and i + 1 < len(line))
            if is_escaped_char:
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
        else:
            is_hash_comment = (ch == HASH_CHAR and bracket_depth == 0)
            if is_hash_comment:
                comment_pos = i
                break
        i += 1
    if comment_pos >= 0:
        return line[:comment_pos]
    return line


class BNFParser:
    """Парсер БНФ-грамматики"""

    # Карта замены проблемных символов на плейсхолдеры
    SPECIAL_CHARS_MAP: Dict[str, str] = {
        HASH_CHAR: HASH_PLACEHOLDER,
        DOLLAR_CHAR: DOLLAR_PLACEHOLDER,
        AMPERSAND_CHAR: AMPERSAND_PLACEHOLDER,
    }

    def __init__(self):
        self.rules: Dict[str, List[str]] = {}
        self.raw_rules: Dict[str, str] = {}
        self.fail_messages: Dict[str, Optional[str]] = {}


    def parse(self, grammar_text: str, base_path: Optional[str] = None):
        """
        Парсит текст грамматики в правила.

        Поддерживает директивы import:
            import "path/to/file.pg"

        :param grammar_text: Текст грамматики
        :param base_path: Базовый путь для разрешения относительных импортов
        """
        self.rules.clear()
        self.raw_rules.clear()

        # Разрешить все импорты до парсинга
        if base_path is None:
            base_path = ''

        grammar_text = self._resolve_imports(grammar_text, base_path)

        raw_lines = grammar_text.strip().split('\n')

        # Удалить комментарии из каждой строки до объединения
        cleaned_lines: list = []
        for raw_line in raw_lines:
            cleaned_lines.append(_strip_comment(raw_line))

        merged_lines: list = []
        for raw_line in cleaned_lines:
            stripped = raw_line.strip()
            if not stripped:
                merged_lines.append((len(merged_lines) + 1, ''))
                continue
            is_line_continuation = (raw_line[0].isspace() and RULE_SEPARATOR_DOUBLE not in raw_line \
                    and RULE_SEPARATOR_SINGLE not in raw_line)
            if is_line_continuation:
                if merged_lines:
                    prev_num, prev_line = merged_lines[-1]
                    merged_lines[-1] = (prev_num, prev_line + ' ' + stripped)
                    continue
            merged_lines.append((len(merged_lines) + 1, raw_line))

        for line_num, line in merged_lines:
            line = line.strip()

            if not line:
                continue

            for original, placeholder in self.SPECIAL_CHARS_MAP.items():
                line = line.replace(original, placeholder)

            if RULE_SEPARATOR_DOUBLE in line:
                sep = RULE_SEPARATOR_DOUBLE
            elif RULE_SEPARATOR_SINGLE in line:
                sep = RULE_SEPARATOR_SINGLE
            else:
                continue

            try:
                name, body = line.split(sep, 1)
                name = name.strip()
                body = body.strip()

                if not name:
                    raise SyntaxError(f"{TEXT_PREFIX}{line_num}: пустое имя правила")

                if not body:
                    raise SyntaxError(f"{TEXT_PREFIX}{line_num}: пустое тело правила '{name}'")

                tokens = self._tokenize(body)

                # Извлечь @fail аннотацию, если есть
                fail_message: Optional[str] = None
                has_fail_annotation = (tokens and tokens[-1].startswith(FAIL_ANNOTATION))
                if has_fail_annotation:
                    fail_token = tokens[-1]
                    # Извлечь сообщение: @fail "текст" или @fail 'текст'
                    payload = fail_token[len(FAIL_ANNOTATION):].strip()
                    quoted_payload = (payload and payload[0] in ('"', "'"))
                    if quoted_payload:
                        quote = payload[0]
                        end = payload.rfind(quote)
                        if end > 0:
                            fail_message = payload[1:end]
                        else:
                            fail_message = payload[1:]
                    else:
                        fail_message = payload
                    tokens = tokens[:-1]

                self.rules[name] = tokens
                self.raw_rules[name] = body
                self.fail_messages[name] = fail_message

            except SyntaxError:
                raise
            except Exception as e:
                raise SyntaxError(f"{TEXT_PREFIX}{line_num}: ошибка парсинга - {e}")

    def _resolve_imports(self, grammar_text: str, base_path: str) -> str:
        """
        Разрешает все директивы import в тексте грамматики.

        :param grammar_text: Исходный текст грамматики
        :param base_path: Базовый путь для относительных импортов
        :return: Текст с разрешёнными импортами
        """
        lines = grammar_text.split('\n')
        import_lines: list = []
        remaining_lines: list = []

        for line in lines:
            if _is_import_directive(line):
                import_name = _extract_import_name(line)
                if import_name:
                    import_lines.append(import_name)
            remaining_lines.append(line)

        if not import_lines:
            return grammar_text

        # Собираем основную грамматику без импортов
        base_grammar = _remove_imports(grammar_text)

        # Последовательно разрешаем импорты
        result = base_grammar
        for import_name in import_lines:
            try:
                imported_text = resolve_import(import_name, base_path)
                result = _merge_grammar(result, imported_text, base_path)
            except FileNotFoundError as e:
                raise SyntaxError(f"Не удалось импортировать: {e}")

        return result

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
        tokens: List[str] = []
        current = ''
        i = 0
        length = len(body)
        in_quotes = False
        quote_char = None

        while i < length:
            char = body[i]

            # @fail аннотация — проверяем сразу, до всех остальных проверок
            is_fail_marker = (char == '@' and not in_quotes)
            if is_fail_marker:
                rest = body[i:]
                if rest.startswith(FAIL_ANNOTATION):
                    after_fail = rest[len(FAIL_ANNOTATION):]
                    fail_has_space = (after_fail and after_fail[0].isspace())
                    if fail_has_space:
                        annotation = FAIL_ANNOTATION
                        i += len(FAIL_ANNOTATION)

                        skip_ws = i < length and body[i].isspace()
                        while skip_ws:
                            i += 1
                            skip_ws = i < length and body[i].isspace()

                        quote_char_found = (i < length and body[i] in ('"', "'"))
                        if quote_char_found:
                            quote = body[i]
                            i += 1
                            msg_parts: list = []
                            read_msg = i < length and body[i] != quote
                            while read_msg:
                                msg_parts.append(body[i])
                                i += 1
                                read_msg = i < length and body[i] != quote
                            if i < length:
                                i += 1
                            annotation += ' ' + quote + ''.join(msg_parts) + quote

                        tokens.append(annotation)
                        continue

                tokens.append(char)
                i += 1
                continue

            open_char_class = (not in_quotes and char == '[')
            if open_char_class:
                if current:
                    parts = current.split()
                    tokens.extend(parts)
                    current = ''

                class_start = i
                depth = 1
                i += 1

                scan_cc = i < length and depth > 0
                while scan_cc:
                    if body[i] == '[':
                        depth += 1
                    elif body[i] == ']':
                        depth -= 1
                    i += 1
                    scan_cc = i < length and depth > 0

                if depth > 0:
                    raise SyntaxError(f"Незакрытый символьный класс: {body[class_start:]}")

                char_class = body[class_start:i]
                tokens.append(char_class)
                continue

            open_quantifier = (not in_quotes and char == '{')
            if open_quantifier:
                if current:
                    parts = current.split()
                    tokens.extend(parts)
                    current = ''

                quant_start = i
                depth = 1
                i += 1

                scan_q = i < length and depth > 0
                while scan_q:
                    if body[i] == '{':
                        depth += 1
                    elif body[i] == '}':
                        depth -= 1
                    i += 1
                    scan_q = i < length and depth > 0

                if depth > 0:
                    raise SyntaxError(f"Незакрытый квантификатор: {body[quant_start:]}")

                quantifier = body[quant_start:i]
                tokens.append(quantifier)
                continue

            string_delimiter = (not in_quotes and char in ('"', "'"))
            if string_delimiter:
                if current:
                    parts = current.split()
                    tokens.extend(parts)
                    current = ''

                in_quotes = True
                quote_char = char
                i += 1
                continue

            if in_quotes:
                is_escaped_char = (char == '\\' and i + 1 < length)
                if is_escaped_char:
                    next_char = body[i + 1]
                    if next_char == quote_char:
                        current += next_char
                        i += 2
                        continue
                    elif next_char == '\\':
                        current += '\\'
                        i += 2
                        continue
                    else:
                        current += body[i:i+2]
                        i += 2
                        continue

                if char == quote_char:
                    if quote_char == '"':
                        tokens.append(f'"{current}"')
                    else:
                        tokens.append(f"'{current}'")
                    current = ''
                    in_quotes = False
                    quote_char = None
                    i += 1
                    continue

                current += char
                i += 1
                continue

            unquoted_space = (char.isspace() and not in_quotes)
            if unquoted_space:
                if current:
                    parts = current.split()
                    tokens.extend(parts)
                    current = ''
                i += 1
                continue

            if char in '()|*+?':
                if current:
                    parts = current.split()
                    tokens.extend(parts)
                    current = ''

                tokens.append(char)
                i += 1
                continue

            current += char
            i += 1

        if in_quotes:
            raise SyntaxError(f"Незакрытая кавычка: {quote_char}{current}")

        if current:
            parts = current.split()
            tokens.extend(parts)

        return tokens

    def get_rules(self) -> Dict[str, List[str]]:
        """Возвращает распарсенные правила"""
        return self.rules

    def get_fail_messages(self) -> Dict[str, Optional[str]]:
        """Возвращает сообщения об ошибках для правил с @fail"""
        return self.fail_messages

    def restore_special_chars(self, text: str, for_regex: bool = False) -> str:
        """Восстанавливает оригинальные символы из плейсхолдеров"""
        if for_regex:
            text = text.replace(HASH_PLACEHOLDER, r'\#')
        else:
            text = text.replace(HASH_PLACEHOLDER, HASH_CHAR)

        text = text.replace(DOLLAR_PLACEHOLDER, DOLLAR_CHAR)
        text = text.replace(AMPERSAND_PLACEHOLDER, AMPERSAND_CHAR)

        return text
