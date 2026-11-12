"""
Генерация символов для символьных классов [abc] для GrammarGenerator.

Обрабатывает простые наборы, диапазоны a-z и UNICODE-классы.
"""
import random
from typing import List

from .generator_unicode import UnicodeGenerator
from .constants import UNICODE_PREFIX


class CharClassGenerator:
    """Генератор символов для символьных классов [abc]."""

    def __init__(self, unicode_generator: "UnicodeGenerator"):
        self._unicode_generator = unicode_generator

    def generate_char_class(self, char_class: str) -> str:
        """Генерирует символ для символьного класса [abc]."""
        inner = char_class[1:-1]  # Убираем [...]

        # Проверяем, есть ли UNICODE-классы
        if UNICODE_PREFIX in inner:
            return self._generate_unicode_char_class(inner)

        # Проверяем negation [^...]
        if inner.startswith('^'):
            inner = inner[1:]

        # Проверяем диапазоны [a-z]
        if '-' in inner:
            return self._generate_range(inner)

        # Простой набор символов
        chars = list(inner)
        return random.choice(chars)

    def _generate_unicode_char_class(self, inner: str) -> str:
        """
        Генерирует символ из символьного класса, содержащего UNICODE.* токены.

        Разбирает содержимое на UNICODE-классы, обычные символы и диапазоны,
        выбирает один случайный элемент для генерации.
        """
        # Извлекаем все токены из inner
        tokens = self._parse_char_class_inner(inner)

        # Собираем все возможные символы
        all_chars: list = []
        for token in tokens:
            if token.startswith(UNICODE_PREFIX):
                chars = self._unicode_generator.generate_unicode_token(token[8:])
                all_chars.extend(chars)
            elif len(token) == 1:
                all_chars.append(token)
            else:
                is_range_marker = (len(token) == 3 and token[1] == '-')
                if is_range_marker:
                    start_ord = ord(token[0])
                    end_ord = ord(token[2])
                    if start_ord <= end_ord:
                        all_chars.extend(
                            chr(i) for i in range(start_ord, end_ord + 1)
                        )
                    else:
                        all_chars.append(token)
                else:
                    all_chars.append(token)

        if not all_chars:
            return ''

        return random.choice(all_chars)

    def _generate_range(self, range_str: str) -> str:
        """Генерирует символ из диапазона [a-z0-9_]."""
        chars: list = []
        i = 0
        while i < len(range_str):
            has_range_sep = (i + 2 < len(range_str) and range_str[i + 1] == '-')
            if has_range_sep:
                start = range_str[i]
                end = range_str[i + 2]
                # Поддержка unicode (например, [а-я])
                start_ord = ord(start)
                end_ord = ord(end)
                if start_ord <= end_ord:
                    chars.append(
                        chr(random.randint(start_ord, end_ord))
                    )
                else:
                    chars.append(start)
                i += 3
            else:
                chars.append(range_str[i])
                i += 1

        return random.choice(chars) if chars else ''

    @staticmethod
    def _parse_char_class_inner(inner: str) -> List[str]:
        """
        Разбирает содержимое символьного класса на токены.

        UNICODE.<name> — один токен.
        Обычные символы и диапазоны a-z — отдельные токены.
        """
        tokens: list = []
        remaining = inner

        while remaining:
            idx = remaining.find(UNICODE_PREFIX)
            if idx == -1:
                # Нет больше UNICODE — разбираем остаток по символам/диапазонам
                tokens.extend(
                    CharClassGenerator._split_range_tokens(remaining)
                )
                break

            # Добавляем часть до UNICODE (по символам)
            if idx > 0:
                tokens.extend(
                    CharClassGenerator._split_range_tokens(remaining[:idx])
                )

            # Извлекаем имя класса после UNICODE.
            suffix = remaining[idx + 8:]  # 8 = len("UNICODE.")
            name_end = 0
            for i, ch in enumerate(suffix):
                is_valid_char = (ch.isalnum() or ch == '_')
                if is_valid_char:
                    name_end = i + 1
                else:
                    break

            if name_end > 0:
                tokens.append(f"UNICODE.{suffix[:name_end]}")
                remaining = suffix[name_end:]
            else:
                tokens.append(UNICODE_PREFIX)
                remaining = suffix

        return tokens

    @staticmethod
    def _split_range_tokens(s: str) -> List[str]:
        """
        Разбивает строку на токены с учётом диапазонов a-z.

        Пример: "a-z09_" → ["a-z", "09", "_"]
        """
        tokens: list = []
        i = 0
        while i < len(s):
            # Проверяем диапазон a-z
            is_range_separator = (i + 2 < len(s)
                and s[i + 1] == '-'
                and s[i] != '\\'
                and s[i + 2] != '\\')
            if is_range_separator:
                tokens.append(s[i:i + 3])
                i += 3
            else:
                tokens.append(s[i])
                i += 1
        return tokens
