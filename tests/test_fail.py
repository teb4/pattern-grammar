"""
Unit-тесты для @fail аннотации.

Реальное поведение @fail:
- `@fail "сообщение"` добавляет сообщение об ошибке в fail_messages
- При несовпадении текста с правилом бросается PatternError с сообщением
- При совпадении — ошибка не бросается
- Сообщение извлекается из кавычек (двойных или одинарных)
"""
import pytest
from pattern_grammar import Pattern, PatternError
from pattern_grammar.parser import BNFParser


# =====================================================================
# Парсинг @fail
# =====================================================================

class TestFailParse:
    """Парсинг @fail аннотации."""

    def test_fail_message_extracted(self):
        grammar = 'rule ::= [a-z]+ @fail "описание ошибки"'
        p = Pattern(grammar)
        assert p._fail_messages['rule'] == 'описание ошибки'

    def test_fail_single_quotes(self):
        grammar = "rule ::= [a-z]+ @fail 'описание ошибки'"
        p = Pattern(grammar)
        assert p._fail_messages['rule'] == 'описание ошибки'

    def test_fail_rule_tokens_clean(self):
        """Токены правила не должны содержать @fail."""
        grammar = 'rule ::= [a-z]+ @fail "описание ошибки"'
        p = Pattern(grammar)
        assert '@fail' not in p.rules['rule']
        assert p.rules['rule'] == ['[a-z]', '+']

    def test_fail_no_message_no_at(self):
        """Правило без @fail не должно иметь сообщение."""
        grammar = 'rule ::= [a-z]+'
        p = Pattern(grammar)
        assert p._fail_messages.get('rule') is None

    def test_multiple_rules_one_with_fail(self):
        grammar = '''
rule1 ::= [a-z]+
rule2 ::= [0-9]+ @fail "число не допустимо"
'''
        p = Pattern(grammar)
        assert p._fail_messages['rule2'] == 'число не допустимо'
        assert p._fail_messages.get('rule1') is None


# =====================================================================
# Поведение match с @fail
# =====================================================================

class TestFailMatch:
    """Поведение match() с @fail аннотацией."""

    def test_fail_on_mismatch(self):
        """При несовпадении должна бросаться PatternError с сообщением."""
        grammar = 'rule ::= [a-z]+ @fail "ожидалась буква"'
        p = Pattern(grammar)
        with pytest.raises(PatternError, match="ожидалась буква"):
            p.match('rule', '123')

    def test_fail_no_error_on_match(self):
        """При совпадении ошибка не бросается."""
        grammar = 'rule ::= [a-z]+ @fail "ожидалась буква"'
        p = Pattern(grammar)
        result = p.match('rule', 'abc')
        assert result is True

    def test_fail_empty_text(self):
        """Пустой текст не совпадает с [a-z]+."""
        grammar = 'rule ::= [a-z]+ @fail "пустой текст"'
        p = Pattern(grammar)
        with pytest.raises(PatternError, match="пустой текст"):
            p.match('rule', '')

    def test_fail_complex_rule(self):
        grammar = 'email ::= [a-z]+ "@" [a-z]+ ".com" @fail "неверный email"'
        p = Pattern(grammar)
        # Совпадение
        assert p.match('email', 'user@example.com') is True
        # Несовпадение
        with pytest.raises(PatternError, match="неверный email"):
            p.match('email', 'invalid')

    def test_fail_preserves_original_behavior(self):
        """Правило без @fail должно работать как раньше."""
        grammar = 'rule ::= [a-z]+'
        p = Pattern(grammar)
        assert p.match('rule', 'abc') is True
        assert p.match('rule', '123') is False


# =====================================================================
# Токенизация @fail
# =====================================================================

class TestFailTokenize:
    """Токенизация @fail аннотации."""

    def test_fail_as_single_token(self):
        parser = BNFParser()
        tokens = parser._tokenize('[a-z]+ @fail "ошибка"')
        # @fail "ошибка" должен быть одним токеном
        assert any(t.startswith('@fail') for t in tokens)

    def test_fail_not_split(self):
        """@fail не должен разбиваться на отдельные токены."""
        parser = BNFParser()
        tokens = parser._tokenize('[a-z]+ @fail "ошибка"')
        assert '@' not in tokens or tokens.count('@') == 0

    def test_at_symbol_without_fail(self):
        """@ без fail должен оставаться как отдельный токен."""
        parser = BNFParser()
        tokens = parser._tokenize('a @ b')
        assert '@' in tokens
