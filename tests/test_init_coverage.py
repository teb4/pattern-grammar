"""
Unit-тесты для покрытия непокрытых веток Pattern (__init__.py).

Цель — достичь 100% покрытия __init__.py.
Непокрытые строки: 135, 144, 149-150, 170, 179-186, 192, 219
"""
import pytest
from pattern_grammar import Pattern, PatternError


# =====================================================================
# _match_regex: not engines ветка (строка 135)
# =====================================================================

class TestMatchRegexNoEngines:
    """Покрытие ветки no engines в _match_regex (строка 135)."""

    def test_match_regex_no_engines_raises(self):
        """Удаление правила из regex_engines → PatternError."""
        grammar = "rule ::= [a-z]+"
        p = Pattern(grammar)
        p.regex_engines.clear()
        with pytest.raises(PatternError, match="не скомпилировано"):
            p.match('rule', 'test')


# =====================================================================
# _match_lark: not parser ветка (строка 144)
# =====================================================================

class TestMatchLarkNoParser:
    """Покрытие ветки no parser в _match_lark (строка 144)."""

    def test_match_lark_no_parser_raises(self):
        """Удаление парсера из parser_engines → PatternError."""
        grammar = "expr ::= term '+' expr | term\nterm ::= [0-9]+"
        p = Pattern(grammar)
        p.parser_engines.clear()
        with pytest.raises(PatternError, match="не создан"):
            p.match('expr', '1+2')


# =====================================================================
# _match_lark: try/except ветка (строки 149-150)
# =====================================================================

class TestMatchLarkTryExcept:
    """Покрытие ветки try/except в _match_lark (строки 149-150)."""

    def test_match_lark_parse_success(self, arithmetic_pattern):
        """Успешный парсинг через Lark → True."""
        result = arithmetic_pattern.match('expr', '1+2')
        assert result is True

    def test_match_lark_parse_failure(self, arithmetic_pattern):
        """Неуспешный парсинг через Lark → False (except Exception)."""
        result = arithmetic_pattern.match('expr', 'abc')
        assert result is False


# =====================================================================
# _parse_regex: Tree return (строка 170)
# =====================================================================

class TestParseRegexTree:
    """Покрытие ветки возврата Tree в _parse_regex (строка 170)."""

    def test_parse_regex_returns_tree(self, simple_pattern):
        """Парсинг regex-правила возвращает Tree."""
        from lark import Tree, Token
        result = simple_pattern.parse('username', 'testuser')
        assert isinstance(result, Tree)
        assert result.data == 'match'
        assert len(result.children) == 1
        child = result.children[0]
        assert isinstance(child, Token)
        assert child.type == 'VALUE'
        assert child.value == 'testuser'


# =====================================================================
# _parse_recursive: not parser ветка (строки 179-180)
# =====================================================================

class TestParseRecursiveNoParser:
    """Покрытие ветки no parser в _parse_recursive (строки 179-180)."""

    def test_parse_recursive_no_parser_raises(self):
        """Удаление парсера из parser_engines → PatternError."""
        grammar = "expr ::= term '+' expr | term\nterm ::= [0-9]+"
        p = Pattern(grammar)
        p.parser_engines.clear()
        with pytest.raises(PatternError, match="не создан"):
            p.parse('expr', '1+2')


# =====================================================================
# _parse_recursive: except ветка (строки 185-186)
# =====================================================================

class TestParseRecursiveExcept:
    """Покрытие ветки except в _parse_recursive (строки 185-186)."""

    def test_parse_recursive_error_raises_pattern_error(self, arithmetic_pattern):
        """Ошибка парсинга Lark → PatternError с сообщением."""
        with pytest.raises(PatternError, match="Ошибка парсинга"):
            arithmetic_pattern.parse('expr', 'abc')


# =====================================================================
# findall: not engines ветка (строка 192)
# =====================================================================

class TestFindallNoEngines:
    """Покрытие ветки no engines в findall."""

    def test_findall_no_engines_raises(self):
        """Удаление из regex_engines → PatternError."""
        grammar = "rule ::= [a-z]+"
        p = Pattern(grammar)
        p.regex_engines.clear()
        with pytest.raises(PatternError, match="не скомпилировано"):
            p.findall('rule', 'test')


# =====================================================================
# _parse_regex: return None ветка (строка 219)
# =====================================================================

class TestParseRegexNoMatch:
    """Покрытие ветки return None в _parse_regex (строка 219)."""

    def test_parse_regex_no_match_returns_none(self, simple_pattern):
        """Отсутствие совпадения → None."""
        result = simple_pattern.parse('username', '')
        assert result is None


# =====================================================================
# get_info: formatted_rules с пустыми токенами
# =====================================================================

class TestGetInfoEdgeCases:
    """Edge cases для get_info."""

    def test_get_info_with_empty_rule(self):
        """Правило с пустыми токенами."""
        grammar = "rule ::="
        with pytest.raises(SyntaxError):
            Pattern(grammar)

    def test_get_info_rules_formatted(self, simple_pattern):
        """Проверка форматированных правил в get_info."""
        info = simple_pattern.get_info()
        assert 'email' in info['rules']
        assert '@' in info['rules']['email']
