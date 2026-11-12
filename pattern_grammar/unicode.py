"""
Unicode-классы для Pattern Grammar.

Предоставляет 21 встроенный класс, который транслируется
в соответствующие свойства Unicode для движка regex.

Пример использования:
    from pattern_grammar import Pattern

    pattern = Pattern('''
        cyrillic_word ::= [UNICODE.Cyrillic]+
        letter        ::= [UNICODE.Letter]+
    ''')
    print(pattern.match('cyrillic_word', 'привет'))  # True
    print(pattern.match('letter', 'café'))           # True
"""

from typing import Dict, List
from .constants import UNICODE_PREFIX


def _require_regex() -> "object":
    """
    Проверяет доступность модуля regex и возвращает его.

    :raises ImportError: Если модуль regex не установлен
    """
    try:
        import regex
        return regex
    except ImportError:
        raise ImportError(
            "Грамматика использует UNICODE-классы, но модуль 'regex' не установлен.\n"
            "Установите его командой: pip install regex\n"
            "Подробнее: https://pypi.org/project/regex/"
        )

# Таблица соответствия Unicode-классов их regex-эквивалентам
# Ключи — имена классов без префикса "UNICODE."
# Значения — эквиваленты для движка regex (Python)
_UNICODE_CLASSES: Dict[str, str] = {
    # Общие категории
    "Letter":      r"\p{L}",
    "Lowercase":   r"\p{Ll}",
    "Uppercase":   r"\p{Lu}",
    "Digit":       r"\p{Nd}",
    "Number":      r"\p{N}",
    "Punctuation": r"\p{P}",
    "Separator":   r"\p{Z}",
    "Symbol":      r"\p{S}",
    "Mark":        r"\p{M}",
    # Письменности (скрипты)
    "Latin":       r"\p{Script=Latin}",
    "Cyrillic":    r"\p{Script=Cyrillic}",
    "Han":         r"\p{Script=Han}",
    "Arabic":      r"\p{Script=Arabic}",
    "Devanagari":  r"\p{Script=Devanagari}",
    "Hangul":      r"\p{Script=Hangul}",
    "Hiragana":    r"\p{Script=Hiragana}",
    "Katakana":    r"\p{Script=Katakana}",
    "Thai":        r"\p{Script=Thai}",
    "Hebrew":      r"\p{Script=Hebrew}",
    # Комбинированные
    "AlphaNum":    r"[\p{L}\p{Nd}]",
    "Word":        r"[\p{L}\p{Nd}_]",
}


def resolve_unicode_class(name: str) -> str:
    """
    Преобразует имя Unicode-класса (без префикса UNICODE.) в regex-эквивалент.

    :param name: Имя класса, например "Letter", "Cyrillic", "AlphaNum"
    :returns: regex-паттерн, например "\\p{L}", "\\p{Script=Cyrillic}"
    :raises ValueError: Если имя класса не найдено в таблице
    """
    if name in _UNICODE_CLASSES:
        return _UNICODE_CLASSES[name]

    available = ", ".join(sorted(_UNICODE_CLASSES.keys()))
    raise ValueError(
        f"Неизвестный Unicode-класс: UNICODE.{name}\n"
        f"Доступные: {available}"
    )


def has_unicode_classes(tokens: List[str]) -> bool:
    """
    Проверяет, содержит ли список токенов хотя бы один UNICODE-класс.

    UNICODE-класс выглядит как "UNICODE.<имя>" и встречается внутри
    символьных классов [...].

    :param tokens: Список токенов правила (из BNFParser)
    :returns: True если хотя бы один токен содержит "UNICODE."
    """
    for token in tokens:
        if UNICODE_PREFIX in token:
            return True
    return False


def expand_unicode_in_char_class(char_class: str) -> str:
    """
    Заменяет UNICODE.<имя> внутри символьного класса на regex-эквивалент.

    Вход: "[UNICODE.Letter UNICODE.Digit _.-]+" -> не меняет (только часть [...])
    Вход: "[UNICODE.Letter UNICODE.Digit _.-]" -> "[\\p{L} \\p{Nd} _.-]"

    :param char_class: Символьный класс в виде строки "[...]"
    :returns: Символьный класс с заменёнными UNICODE-токенами
    """
    not_char_class = (not (char_class.startswith('[') and char_class.endswith(']')))
    if not_char_class:
        return char_class

    inner = char_class[1:-1]
    result_parts: list = []
    remaining = inner

    while remaining:
        idx = remaining.find(UNICODE_PREFIX)
        if idx == -1:
            result_parts.append(remaining)
            break

        # Добавляем часть до UNICODE.
        result_parts.append(remaining[:idx])

        # Извлекаем имя класса после UNICODE.
        suffix = remaining[idx + 8:]  # 8 = len("UNICODE.")
        name_end = 0
        for i, ch in enumerate(suffix):
            is_valid_char = (ch.isalnum() or ch == '_')
            if is_valid_char:
                name_end = i + 1
            else:
                break

        if name_end == 0:
            result_parts.append(UNICODE_PREFIX)
            remaining = suffix
            continue

        class_name = suffix[:name_end]
        remaining = suffix[name_end:]

        replacement = resolve_unicode_class(class_name)
        result_parts.append(replacement)

    expanded = ''.join(result_parts)
    return f"[{expanded}]"
