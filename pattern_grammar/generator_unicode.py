"""
Генерация UNICODE-символов для GrammarGenerator.

Обрабатывает UNICODE.<классы> (\\p{L}, \\p{Script=...} и т.д.) через
движок 'regex' и бинарный поиск по кодовым точкам.
"""
from typing import Any, List

from .unicode import resolve_unicode_class
from .constants import REGEX_UNICODE_OPEN


def _require_regex_for_generator() -> Any:
    """
    Проверяет доступность модуля regex и возвращает его.

    :raises ImportError: Если модуль regex не установлен
    """
    try:
        import regex
        return regex
    except ImportError:
        raise ImportError(
            "Генерация UNICODE-классов требует модуль 'regex'.\n"
            "Установите его командой: pip install regex\n"
            "Подробнее: https://pypi.org/project/regex/"
        )


class UnicodeGenerator:
    """Генератор UNICODE-символов для символьных классов."""

    def generate_unicode_token(self, name: str) -> List[str]:
        """
        Генерирует список символов для UNICODE-класса.

        Использует regex-движок для получения диапазана кодовых точек.
        """
        try:
            regex_mod = _require_regex_for_generator()
        except ImportError:
            # Если regex не установлен — возвращаем ASCII-заглушку
            return ['?']

        try:
            pattern_str = resolve_unicode_class(name)
        except ValueError:
            return ['?']

        # Используем regex.search для поиска первого совпадения в большом диапазоне
        # и извлекаем кодовые точки
        chars = self._extract_unicode_chars(pattern_str, regex_mod)
        return chars if chars else ['?']

    def _extract_unicode_chars(
        self, pattern_str: str, regex_mod: Any
    ) -> List[str]:
        """
        Извлекает кодовые точки из Unicode-паттерна для генерации.

        Для категорий (\\p{L}) — берём случайные точки из диапазона.
        Для скриптов (\\p{Script=...}) — берём из диапазона скрипта.
        """
        # Для комбинированных классов (AlphaNum, Word) — рекурсивно
        is_char_class_unicode = (pattern_str.startswith("[\\p{") and pattern_str.endswith("]"))
        if is_char_class_unicode:
            inner = pattern_str[2:-1]
            parts = inner.split("}")
            results: list = []
            for part in parts:
                if part.startswith(REGEX_UNICODE_OPEN):
                    sub_pattern = part + "}"
                    results.extend(
                        self._extract_unicode_chars(sub_pattern, regex_mod)
                    )
            return results if results else []

        # Для скриптов: \p{Script=Cyrillic}, и т.д.
        # (должно быть ПЕРЕД общей проверкой \p{...})
        is_script_unicode = (pattern_str.startswith(r"\p{Script=")
            and pattern_str.endswith("}"))
        if is_script_unicode:
            script = pattern_str[10:-1]
            return self._generate_from_script(script, regex_mod, pattern_str)

        # Для категорий: \p{L}, \p{Ll}, и т.д.
        is_class_unicode = (pattern_str.startswith(REGEX_UNICODE_OPEN) and pattern_str.endswith("}"))
        if is_class_unicode:
            category = pattern_str[3:-1]
            return self._generate_from_category(category, regex_mod, pattern_str)

        return []

    def _generate_from_category(
        self, category: str, regex_mod: Any, pattern_str: str
    ) -> List[str]:
        """
        Генерирует символы для Unicode-категории.

        Использует бинарный поиск по кодовым точкам для нахождения
        диапазона символов данной категории.
        """
        # Определяем диапазон для поиска
        if category == "Nd":
            # Десятичные цифры — ограничиваемся базовыми
            start, end = 0x0030, 0x0039  # 0-9
        elif category == "Ll":
            start, end = 0x0061, 0x0250  # строчные буквы
        elif category == "Lu":
            start, end = 0x0041, 0x0220  # заглавные буквы
        elif category == "L":
            start, end = 0x0041, 0x2FFFF  # все буквы
        elif category == "N":
            start, end = 0x0030, 0x10195  # все числа
        elif category == "P":
            start, end = 0x0021, 0x203F  # пунктуация
        elif category == "Z":
            start, end = 0x0020, 0x2060  # разделители
        elif category == "S":
            start, end = 0x0024, 0x2B300  # символы
        elif category == "M":
            start, end = 0x0300, 0x036F  # комбинируемые знаки
        else:
            start, end = 0x0041, 0x007A  # fallback: ASCII

        # Собираем символы категории
        chars: list = []
        step = max(1, (end - start) // 100)  # Шагаем для эффективности
        for code_point in range(start, end + 1, step):
            test_char = chr(code_point)
            if regex_mod.search(pattern_str, test_char):
                chars.append(test_char)
                if len(chars) >= 10:  # Ограничиваем количество
                    break

        return chars

    def _generate_from_script(
        self, script: str, regex_mod: Any, pattern_str: str
    ) -> List[str]:
        """
        Генерирует символы для Unicode-скрипта.

        Использует бинарный поиск по кодовым точкам для нахождения
        диапазона символов данного скрипта.
        """
        # Определяем диапазон для поиска по скрипту
        script_ranges = {
            "Latin": (0x0041, 0x024F),
            "Cyrillic": (0x0400, 0x04FF),
            "Han": (0x4E00, 0x9FFF),
            "Arabic": (0x0600, 0x06FF),
            "Devanagari": (0x0900, 0x097F),
            "Hangul": (0xAC00, 0xD7AF),
            "Hiragana": (0x3040, 0x309F),
            "Katakana": (0x30A0, 0x30FF),
            "Thai": (0x0E00, 0x0E7F),
            "Hebrew": (0x0590, 0x05FF),
        }

        start, end = script_ranges.get(script, (0x0041, 0x024F))

        chars: list = []
        step = max(1, (end - start) // 50)
        for code_point in range(start, end + 1, step):
            test_char = chr(code_point)
            if regex_mod.search(pattern_str, test_char):
                chars.append(test_char)
                if len(chars) >= 10:
                    break

        return chars
