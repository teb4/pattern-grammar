"""
Unit-тесты для покрытия непокрытых веток BNFParser.

Цель — достичь 100% покрытия parser.py.
Непокрытые строки: 67-68, 118-119, 144-146, 154, 168-170, 178, 184, 192-194, 208-215
"""
import pytest
from pattern_grammar.parser import BNFParser


# =====================================================================
# parse: ветка экранирования в комментарии (строки 67-68)
# =====================================================================

class TestParseEscapeInComment:
    """Покрытие ветки экранирования в комментарии (строки 67-68)."""

    def test_parse_with_backslash_before_hash(self):
        """Строка с экранированным символом перед # в комментарии."""
        parser = BNFParser()
        # \\ перед # → ветка 67-68: ch == '\\' и i + 1 < len(line)
        grammar = r'rule ::= [a-z]+ \\# comment'
        parser.parse(grammar)
        rules = parser.get_rules()
        assert 'rule' in rules

    def test_parse_backslash_in_comment_context(self):
        """Экранированный символ в контексте комментария."""
        parser = BNFParser()
        grammar = r'rule ::= [a-z]+ \# [a-z]+'
        parser.parse(grammar)
        rules = parser.get_rules()
        assert 'rule' in rules


# =====================================================================
# parse: обработка исключений SyntaxError (строки 118-119)
# =====================================================================

class TestParseExceptions:
    """Покрытие веток обработки исключений (строки 118-119)."""

    def test_syntax_error_reraised(self, parser):
        """SyntaxError должен быть переброшен, а не обернут."""
        with pytest.raises(SyntaxError):
            parser.parse(" ::=")

    def test_syntax_error_unclosed_class(self):
        """Незакрытый символьный класс поднимает SyntaxError."""
        parser = BNFParser()
        with pytest.raises(SyntaxError, match="Незакрытый символьный класс"):
            parser.parse("rule ::= [a-z+")


# =====================================================================
# _tokenize: конец с current (строки 144-146)
# =====================================================================

class TestTokenizeEndWithCurrent:
    """Покрытие ветки конца токенизации с current (строки 144-146)."""

    def test_tokenize_ends_with_current(self, parser):
        """Токенизация, где после цикла есть оставшийся current."""
        parser.parse("rule ::= abc")
        rules = parser.get_rules()
        assert 'abc' in rules['rule']

    def test_tokenize_no_trailing_current(self, parser):
        """Токенизация без оставшегося current (заканчивается на пробел)."""
        parser.parse("rule ::= abc ")
        rules = parser.get_rules()
        assert 'abc' in rules['rule']


# =====================================================================
# _tokenize: char class depth check (строка 154)
# =====================================================================

class TestTokenizeCharClassDepth:
    """Покрытие ветки depth > 0 для char class (строка 154)."""

    def test_nested_char_class(self, parser):
        """Вложенный символьный класс."""
        parser.parse("rule ::= [[a-z]]")
        rules = parser.get_rules()
        assert '[[a-z]]' in rules['rule']


# =====================================================================
# _tokenize: quantifier branch (строки 168-170, 178, 184)
# =====================================================================

class TestTokenizeQuantifier:
    """Покрытие ветки квантификатора { (строки 168-170, 178, 184)."""

    def test_tokenize_quantifier_brace(self, parser):
        """Квантификатор {3}."""
        parser.parse("rule ::= [a-z]{3}")
        rules = parser.get_rules()
        assert '[a-z]' in rules['rule']
        assert '{3}' in rules['rule']

    def test_tokenize_nested_braces(self, parser):
        """Вложенные фигурные скобки в квантификаторе."""
        parser.parse("rule ::= [a-z]{ {3} }")
        rules = parser.get_rules()
        assert '[a-z]' in rules['rule']

    def test_unclosed_quantifier_raises(self, parser):
        """Незакрытый квантификатор."""
        with pytest.raises(SyntaxError, match="Незакрытый квантификатор"):
            parser.parse("rule ::= [a-z]{3")


# =====================================================================
# _tokenize: in_quotes ветка (строки 192-194)
# =====================================================================

class TestTokenizeInQuotes:
    """Покрытие ветки in_quotes (строки 192-194)."""

    def test_tokenize_single_word_in_quotes(self, parser):
        """Одно слово в кавычках."""
        parser.parse('rule ::= "hello"')
        rules = parser.get_rules()
        assert '"hello"' in rules['rule']

    def test_tokenize_multi_word_in_quotes(self, parser):
        """Многословное выражение в кавычках."""
        parser.parse('rule ::= "hello world"')
        rules = parser.get_rules()
        assert '"hello world"' in rules['rule']


# =====================================================================
# _tokenize: экранирование внутри кавычек (строки 208-215)
# =====================================================================

class TestTokenizeEscapeInQuotes:
    """Покрытие ветки экранирования внутри кавычек (строки 208-215)."""

    def test_escape_quote_inside_double_quotes(self, parser):
        """Экранированная кавычка \\" внутри двойных кавычек."""
        parser.parse(r'rule ::= "say \"hi\""')
        rules = parser.get_rules()
        assert 'say' in rules['rule'][0]

    def test_escape_backslash_inside_quotes(self, parser):
        """Экранированный бэкслэш \\\\ внутри кавычек."""
        parser.parse(r'rule ::= "a\\b"')
        rules = parser.get_rules()
        assert 'a' in rules['rule'][0]

    def test_escape_other_char_inside_quotes(self, parser):
        """Экранирование другого символа внутри кавычек."""
        parser.parse(r'rule ::= "a\!b"')
        rules = parser.get_rules()
        assert len(rules['rule']) >= 1


# =====================================================================
# restore_special_chars: edge cases
# =====================================================================

class TestRestoreSpecialCharsEdgeCases:
    """Edge cases для restore_special_chars."""

    def test_restore_only_dollar(self, parser):
        """Восстановление только $."""
        result = parser.restore_special_chars("test ___DOLLAR___ end")
        assert result == "test $ end"

    def test_restore_only_ampersand(self, parser):
        """Восстановление только &."""
        result = parser.restore_special_chars("test ___AMP___ end")
        assert result == "test & end"

    def test_restore_all_special(self, parser):
        """Восстановление всех спецсимволов."""
        result = parser.restore_special_chars("___HASH___ ___DOLLAR___ ___AMP___")
        assert result == "# $ &"

    def test_restore_all_for_regex(self, parser):
        """Восстановление всех спецсимволов для regex."""
        result = parser.restore_special_chars("___HASH___ ___DOLLAR___ ___AMP___", for_regex=True)
        assert result == r"\# $ &"

    def test_restore_empty_string(self, parser):
        """Восстановление для пустой строки."""
        result = parser.restore_special_chars("")
        assert result == ""

    def test_restore_no_placeholders(self, parser):
        """Восстановление когда нет плейсхолдеров."""
        result = parser.restore_special_chars("просто текст")
        assert result == "просто текст"
