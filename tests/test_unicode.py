"""
Тесты для модуля unicode.py

Проверяют:
- resolve_unicode_class() — корректная трансляция имени класса в regex
- has_unicode_classes() — обнаружение UNICODE.* в списке токенов
- expand_unicode_in_char_class() — замена UNICODE.* внутри [...]
- Ошибки при неизвестном классе
"""

import pytest

from pattern_grammar.unicode import (
    _UNICODE_CLASSES,
    resolve_unicode_class,
    has_unicode_classes,
    expand_unicode_in_char_class,
)


# --- resolve_unicode_class ---

class TestResolveUnicodeClass:
    """Проверяют трансляцию Unicode-имён в regex-паттерны."""

    def test_letter(self):
        assert resolve_unicode_class("Letter") == r"\p{L}"

    def test_lowercase(self):
        assert resolve_unicode_class("Lowercase") == r"\p{Ll}"

    def test_uppercase(self):
        assert resolve_unicode_class("Uppercase") == r"\p{Lu}"

    def test_digit(self):
        assert resolve_unicode_class("Digit") == r"\p{Nd}"

    def test_number(self):
        assert resolve_unicode_class("Number") == r"\p{N}"

    def test_punctuation(self):
        assert resolve_unicode_class("Punctuation") == r"\p{P}"

    def test_separator(self):
        assert resolve_unicode_class("Separator") == r"\p{Z}"

    def test_symbol(self):
        assert resolve_unicode_class("Symbol") == r"\p{S}"

    def test_mark(self):
        assert resolve_unicode_class("Mark") == r"\p{M}"

    def test_latin(self):
        assert resolve_unicode_class("Latin") == r"\p{Script=Latin}"

    def test_cyrillic(self):
        assert resolve_unicode_class("Cyrillic") == r"\p{Script=Cyrillic}"

    def test_han(self):
        assert resolve_unicode_class("Han") == r"\p{Script=Han}"

    def test_arabic(self):
        assert resolve_unicode_class("Arabic") == r"\p{Script=Arabic}"

    def test_devanagari(self):
        assert resolve_unicode_class("Devanagari") == r"\p{Script=Devanagari}"

    def test_hangul(self):
        assert resolve_unicode_class("Hangul") == r"\p{Script=Hangul}"

    def test_hiragana(self):
        assert resolve_unicode_class("Hiragana") == r"\p{Script=Hiragana}"

    def test_katakana(self):
        assert resolve_unicode_class("Katakana") == r"\p{Script=Katakana}"

    def test_thai(self):
        assert resolve_unicode_class("Thai") == r"\p{Script=Thai}"

    def test_hebrew(self):
        assert resolve_unicode_class("Hebrew") == r"\p{Script=Hebrew}"

    def test_alphanum(self):
        assert resolve_unicode_class("AlphaNum") == r"[\p{L}\p{Nd}]"

    def test_word(self):
        assert resolve_unicode_class("Word") == r"[\p{L}\p{Nd}_]"

    def test_unknown_class_raises(self):
        with pytest.raises(ValueError) as exc_info:
            resolve_unicode_class("Klingon")
        error_msg = str(exc_info.value)
        assert "Неизвестный Unicode-класс: UNICODE.Klingon" in error_msg
        assert "Доступные:" in error_msg
        assert "Letter" in error_msg

    def test_all_21_classes_resolvable(self):
        """Проверяют, что все 21 класс разрешимы."""
        assert len(_UNICODE_CLASSES) == 21
        for name in _UNICODE_CLASSES:
            result = resolve_unicode_class(name)
            assert result == _UNICODE_CLASSES[name]


# --- has_unicode_classes ---

class TestHasUnicodeClasses:
    """Проверяют обнаружение UNICODE.* в списке токенов."""

    def test_no_unicode(self):
        tokens = ["[a-z]", "+", '"hello"', "(", "a", ")"]
        assert has_unicode_classes(tokens) is False

    def test_single_unicode(self):
        tokens = ["[UNICODE.Cyrillic]+"]
        assert has_unicode_classes(tokens) is True

    def test_unicode_inside_char_class(self):
        tokens = ["[UNICODE.Letter UNICODE.Digit _.-]+"]
        assert has_unicode_classes(tokens) is True

    def test_unicode_as_separate_token(self):
        tokens = ["[abc]", "UNICODE.Cyrillic", "+" ]
        assert has_unicode_classes(tokens) is True

    def test_empty_list(self):
        tokens: list = []
        assert has_unicode_classes(tokens) is False

    def test_mixed_unicode_and_normal(self):
        tokens = ["[a-z]", "UNICODE.Letter", "+", '"test"']
        assert has_unicode_classes(tokens) is True


# --- expand_unicode_in_char_class ---

class TestExpandUnicodeInCharClass:
    """Проверяют замену UNICODE.* внутри символьных классов."""

    def test_simple_unicode(self):
        result = expand_unicode_in_char_class("[UNICODE.Letter]")
        assert result == r"[\p{L}]"

    def test_unicode_with_space(self):
        result = expand_unicode_in_char_class("[UNICODE.Letter +]")
        assert result == r"[\p{L} +]"

    def test_multiple_unicode(self):
        result = expand_unicode_in_char_class("[UNICODE.Letter UNICODE.Digit]")
        assert result == r"[\p{L} \p{Nd}]"

    def test_unicode_with_literal_chars(self):
        result = expand_unicode_in_char_class("[UNICODE.Letter _.-]")
        assert result == r"[\p{L} _.-]"

    def test_cyrillic(self):
        result = expand_unicode_in_char_class("[UNICODE.Cyrillic -]")
        assert result == r"[\p{Script=Cyrillic} -]"

    def test_alpha_num(self):
        result = expand_unicode_in_char_class("[UNICODE.AlphaNum]")
        assert result == r"[[\p{L}\p{Nd}]]"

    def test_word(self):
        result = expand_unicode_in_char_class("[UNICODE.Word]")
        assert result == r"[[\p{L}\p{Nd}_]]"

    def test_non_char_class_unchanged(self):
        result = expand_unicode_in_char_class("UNICODE.Letter")
        assert result == "UNICODE.Letter"

    def test_empty_char_class(self):
        result = expand_unicode_in_char_class("[]")
        assert result == "[]"

    def test_complex_char_class(self):
        result = expand_unicode_in_char_class("[UNICODE.Letter UNICODE.Digit ._%+-]")
        assert r"\p{L}" in result
        assert r"\p{Nd}" in result
        assert "." in result

    def test_unknown_unicode_raises_error(self):
        with pytest.raises(ValueError):
            expand_unicode_in_char_class("[UNICODE.Unknown]")
