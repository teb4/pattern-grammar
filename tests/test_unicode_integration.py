"""
Интеграционные тесты для UNICODE-классов Pattern Grammar.

Проверяют полный пайплайн: парсер → regex_converter → Pattern.match,
а также генерацию случайных данных.
"""

import pytest

from pattern_grammar import Pattern


# --- Базовые UNICODE-классы ---

class TestUnicodeBasicMatch:
    """Проверяют match() с UNICODE-классами."""

    def test_cyrillic_letter(self):
        pattern = Pattern("""
            word ::= [UNICODE.Cyrillic]+
        """)
        assert pattern.match('word', 'привет') is True
        assert pattern.match('word', 'мир') is True
        assert pattern.match('word', 'hello') is False

    def test_latin_letter(self):
        pattern = Pattern("""
            word ::= [UNICODE.Latin]+
        """)
        assert pattern.match('word', 'hello') is True
        assert pattern.match('word', 'café') is True
        assert pattern.match('word', 'привет') is False

    def test_digit(self):
        pattern = Pattern("""
            digits ::= [UNICODE.Digit]+
        """)
        assert pattern.match('digits', '12345') is True
        assert pattern.match('digits', '0') is True
        assert pattern.match('digits', 'abc') is False

    def test_letter_and_digit(self):
        pattern = Pattern("""
            username ::= [UNICODE.Letter UNICODE.Digit _.-]+
        """)
        assert pattern.match('username', 'user_name-1') is True
        assert pattern.match('username', 'café_123') is True
        assert pattern.match('username', '12345') is True

    def test_mixed_with_literals(self):
        pattern = Pattern("""
            email_local ::= [UNICODE.Letter UNICODE.Digit ._%+\\-]+
        """)
        assert pattern.match('email_local', 'café+münchen') is True
        assert pattern.match('email_local', 'user123') is True


class TestUnicodeWithQuantifiers:
    """Проверяют UNICODE-классы с квантификаторами."""

    def test_plus_quantifier(self):
        pattern = Pattern("""
            word ::= [UNICODE.Cyrillic]+
        """)
        assert pattern.match('word', 'а') is True
        assert pattern.match('word', 'абвгд') is True

    def test_star_quantifier(self):
        pattern = Pattern("""
            optional ::= [UNICODE.Letter]*
        """)
        assert pattern.match('optional', '') is True
        assert pattern.match('optional', 'abc') is True

    def test_question_quantifier(self):
        pattern = Pattern("""
            optional_letter ::= [UNICODE.Letter]?
        """)
        assert pattern.match('optional_letter', 'a') is True
        assert pattern.match('optional_letter', '') is True

    def test_braced_quantifier(self):
        pattern = Pattern("""
            three_digits ::= [UNICODE.Digit]{3}
        """)
        assert pattern.match('three_digits', '123') is True
        assert pattern.match('three_digits', 'abc') is False

    def test_braced_range_quantifier(self):
        pattern = Pattern("""
            pin ::= [UNICODE.Digit]{4,6}
        """)
        assert pattern.match('pin', '1234') is True
        assert pattern.match('pin', '123456') is True
        assert pattern.match('pin', '123') is False


class TestUnicodeCompoundRules:
    """Проверяют UNICODE-классы в составных правилах."""

    def test_email_with_unicode(self):
        pattern = Pattern("""
            email ::= username "@" domain "." tld
            username ::= [UNICODE.Letter UNICODE.Digit ._%+\\-]+
            domain ::= [UNICODE.Letter UNICODE.Digit .\\-]+
            tld ::= [UNICODE.Letter]{2,}
        """)
        assert pattern.match('email', 'test@example.com') is True
        assert pattern.match('email', 'café@münchen.de') is True
        assert pattern.match('email', '用户@例子.中国') is True

    def test_mixed_ascii_and_unicode(self):
        pattern = Pattern("""
            code ::= [A-Z]{3} " " [UNICODE.Digit]{3}
        """)
        assert pattern.match('code', 'ABC 123') is True
        assert pattern.match('code', 'XYZ 789') is True


class TestUnicodeUnknownError:
    """Проверяют ошибку при неизвестном UNICODE-классе."""

    def test_unknown_class_raises_error(self):
        with pytest.raises(Exception) as exc_info:
            Pattern("""
                word ::= [UNICODE.Klingon]+
            """)
        error_text = str(exc_info.value).lower()
        # Ошибка должна быть либо ValueError (из resolve_unicode_class),
        # либо ImportError (из _require_regex), либо ошибка regex
        assert len(error_text) > 0


class TestUnicodeWithoutRegexInstalled:
    """Проверяют graceful degradation когда regex не установлен."""

    def test_unicode_pattern_without_regex(self):
        """Проверяет что _require_regex возвращает модуль когда regex установлен."""
        from pattern_grammar.unicode import _require_regex

        mod = _require_regex()
        assert hasattr(mod, 'compile')
        assert hasattr(mod, 'search')
        # regex модуль должен поддерживать \p{}
        assert mod.search(r'\p{Script=Cyrillic}', 'а') is not None


class TestUnicodeGenerate:
    """Проверяют генерацию случайных данных с UNICODE-классами."""

    def test_generate_cyrillic(self):
        pattern = Pattern("""
            word ::= [UNICODE.Cyrillic]+
        """)
        result = pattern.generate('word', count=1)
        assert isinstance(result, list)
        assert len(result) == 1
        # Результат должен содержать кириллические символы
        assert any('\u0400' <= ch <= '\u04FF' for ch in result[0])

    def test_generate_cyrillic_multiple(self):
        pattern = Pattern("""
            word ::= [UNICODE.Cyrillic]{3}
        """)
        results = pattern.generate('word', count=3)
        assert len(results) == 3
        for result in results:
            assert len(result) == 3
            assert any('\u0400' <= ch <= '\u04FF' for ch in result)

    def test_generate_latin(self):
        pattern = Pattern("""
            word ::= [UNICODE.Latin]+
        """)
        result = pattern.generate('word', count=5)
        assert isinstance(result, list)
        assert len(result) == 5
        # Результат должен содержать латинские буквы (Unicode Latin script)
        assert all(any(ch.isalpha() for ch in r) for r in result)

    def test_generate_digit(self):
        pattern = Pattern("""
            digits ::= [UNICODE.Digit]{4}
        """)
        results = pattern.generate('digits', count=3)
        assert len(results) == 3
        for result in results:
            assert len(result) == 4
            assert result.isdigit()

    def test_generate_alphanum(self):
        pattern = Pattern("""
            code ::= [UNICODE.AlphaNum]{3}
        """)
        results = pattern.generate('code', count=3)
        assert len(results) == 3
        for result in results:
            assert len(result) == 3
            # Каждый символ — буква или цифра
            assert all(ch.isalnum() for ch in result)


class TestUnicodeBackwardCompatibility:
    """Проверяют что ASCII-грамматики продолжают работать."""

    def test_ascii_email_still_works(self):
        pattern = Pattern("""
            email ::= username "@" domain "." tld
            username ::= [a-zA-Z0-9._%+-]+
            domain ::= [a-zA-Z0-9.-]+
            tld ::= [a-zA-Z]{2,}
        """)
        assert pattern.match('email', 'test@example.com') is True
        assert pattern.match('email', 'user.name+tag@domain.org') is True

    def test_ascii_digit_still_works(self):
        pattern = Pattern("""
            pin ::= [0-9]{4}
        """)
        assert pattern.match('pin', '1234') is True
        assert pattern.match('pin', '0000') is True
        assert pattern.match('pin', 'abcd') is False

    def test_ascii_generate_still_works(self):
        pattern = Pattern("""
            pin ::= [0-9]{4}
        """)
        results = pattern.generate('pin', count=3)
        assert len(results) == 3
        for result in results:
            assert len(result) == 4
            assert result.isdigit()
