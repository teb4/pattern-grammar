"""
Константы для Pattern Grammar

Все магические числа, строки и символы вынесены сюда,
чтобы соответствовать правилу №6 (rules.md).
"""

# Операторы определения правил
RULE_SEPARATOR_DOUBLE = '::='
RULE_SEPARATOR_SINGLE = ':='

# Символы, заменяемые на плейсхолдеры
HASH_CHAR = '#'
HASH_PLACEHOLDER = '___HASH___'
DOLLAR_CHAR = '$'
DOLLAR_PLACEHOLDER = '___DOLLAR___'
AMPERSAND_CHAR = '&'
AMPERSAND_PLACEHOLDER = '___AMP___'

# Спецсимволы регулярных выражений, требующие экранирования
REGEX_SPECIAL_CHARS = '.^$*+?[]\\|()'

# Спецсимволы, разделяющие токены в БНФ
BNF_SPECIAL_CHARS = '()|*+?-'

# Пустые альтернативы в Lark
EMPTY_DOUBLE_QUOTE = '" "'
EMPTY_SINGLE_QUOTE = "''"

# Квантификаторы
QUANTIFIERS = ('*', '+', '?')

# Встроенные классы символов для regex
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

# Спецсимволы Lark, требующие экранирования в строковых литералах
LARK_ESCAPED_CHARS = '+-*/%=<>!&|.,;:^'

# Максимальная глубина рекурсии для предотвращения RecursionError
MAX_RECURSION_DEPTH = 100

# Минимальная версия Python
MIN_PYTHON_VERSION = '>=3.9'

# --- Магические строки/числы со смыслом (Rule 6) ---

# Расширения и ключевые слова импорта в тексте грамматики
PG_EXTENSION = '.pg'          # суффикс файлов грамматик pattern-grammar
PG_GLOB_PATTERN = '*.pg'      # glob для поиска файлов грамматик
IMPORT_KEYWORD = 'import '    # ключевое слово импорта в тексте грамматики

# Ключевое слово аннотации ожидаемой ошибки в BNF-грамматике
FAIL_ANNOTATION = '@fail'     # аннотация ожидаемого исключения

# Директива синтаксиса Lark: пропуск пробельных символов
LARK_IGNORE_DIRECTIVE = '%ignore /\\s+/'

# Вероятность выбора UNICODE-класса при генерации (generator.py)

# Имя опциональной зависимости для интеграции с Pydantic
PYDANTIC_PACKAGE = 'pydantic'
GENERATOR_UNICODE_WEIGHT = 0.5

# Максимальная глубина генератора для предотвращения бесконечной рекурсии
GENERATOR_MAX_DEPTH = 20

# --- Rule 7: магические строки, используемые в логике (вынесены из кода) ---

# Префикс UNICODE.-классов внутри символьных классов
UNICODE_PREFIX = 'UNICODE.'

# Начало unicode-регулярной группы \p{...}
REGEX_UNICODE_OPEN = '\\p{'
REGEX_PATTERN_ATTR = 'pattern'

# Имена методов движка regex, используемые как ключи
METHOD_MATCH = 'match'
METHOD_FINDALL = 'findall'

# Ключи внутренних словарей и JSON Schema
KEY_PATTERN = 'pattern'
JSON_KEY_TYPE = 'type'
JSON_KEY_STRING = 'string'

# Кодировка файлов грамматик
ENCODING_UTF8 = 'utf-8'

# Разделитель альтернатив в Lark/regex
LARK_ALT_SEPARATOR = ' | '

# Сообщения об ошибках проверки типов
RULE_NAME_TYPE_ERROR = 'rule_name должен быть строкой'
TEXT_TYPE_ERROR = 'text должен быть строкой'

# --- Rule 7 (Tier 1b): фрагменты regex-синтаксиса в f-строках ---
REGEX_NONCAP_GROUP = '(?:'          # непоймающая (non-capturing) группа в regex
REGEX_RULE_DELIM = ': /'            # разделитель имени правила и regex в Lark (name: /regex/)

# --- Rule 7 (Tier 1b): префиксы и суффиксы сообщений об ошибках ---
RULE_PREFIX = 'Правило '            # префикс: "Правило 'name' ..."
PARSER_PREFIX = 'Парсер для правила '  # префикс: "Парсер для правила 'name' ..."
TEXT_PREFIX = 'Строка '             # префикс: "Строка N ..."
RULE_NOT_FOUND = ' не найдено'
RULE_NOT_COMPILED = ' не скомпилировано'
RULE_NOT_CREATED = ' не создан'
