"""
Тесты для edge-case, описанных в audit.md.
"""
import pytest
import re
from pattern_grammar import Pattern
from pattern_grammar.parser import BNFParser


# =====================================================================
# Hash-символы
# =====================================================================

class TestHashChars:
    """Обработка хеш-символа (#)."""

    def test_hash_in_char_class_replaced(self):
        """Хеш внутри символьного класса заменяется на плейсхолдер — баг из audit 3.1."""
        grammar = "rule ::= [a#z]+"
        p = Pattern(grammar)
        # После замены # → ___HASH___ класс становится [a___HASH___]+
        # Это не совпадает с 'abc', так как хеш не экранирован
        result = p.match('rule', 'abc')
        assert result is False

    def test_hash_as_comment(self):
        grammar = """
rule ::= [a-z]+ # это комментарий
"""
        p = Pattern(grammar)
        result = p.match('rule', 'test')
        assert result is True

    def test_multiline_rule_with_inline_comment(self):
        """Многострочное правило с inline-комментариями."""
        grammar = """
rule ::= [a-z]+ # начало
       [0-9]+ # конец
"""
        p = Pattern(grammar)
        result = p.match('rule', 'abc123')
        assert result is True

    def test_special_chars_map_has_all(self):
        # Исправление бага 3.1: $ и & теперь обрабатываются
        assert '$' in BNFParser.SPECIAL_CHARS_MAP
        assert '&' in BNFParser.SPECIAL_CHARS_MAP


# =====================================================================
# Кавычные литералы
# =====================================================================

class TestQuotedLiterals:
    """Кавычные литералы."""

    def test_double_quote_literal(self):
        grammar = 'rule ::= "hello" " " "world"'
        p = Pattern(grammar)
        result = p.match('rule', 'hello world')
        assert result is True

    def test_double_quote_literal_match(self, quoted_grammar):
        result = quoted_grammar.match('greeting', 'hello world')
        assert result is True

    def test_double_quote_literal_no_match(self, quoted_grammar):
        result = quoted_grammar.match('greeting', 'helloearth')
        assert result is False

    def test_single_quote_literal(self):
        grammar = "rule ::= 'hello' ' ' 'world'"
        p = Pattern(grammar)
        result = p.match('rule', 'hello world')
        assert result is True

    def test_escaped_quote_in_literal(self):
        grammar = 'rule ::= "say \\"hi\\""'
        p = Pattern(grammar)
        result = p.match('rule', 'say "hi"')
        assert result is True


# =====================================================================
# Пустые альтернативы
# =====================================================================

class TestEmptyAlternatives:
    """Пустые альтернативы в грамматике."""

    def test_empty_alt_single_quote(self):
        grammar = 'rule ::= "a" | \'\''
        p = Pattern(grammar)
        result = p.match('rule', 'a')
        assert result is True

    def test_empty_alt_double_quote(self):
        grammar = 'rule ::= "a" | " "'
        p = Pattern(grammar)
        result = p.match('rule', 'a')
        assert result is True

    def test_option_with_empty(self, empty_alternative_grammar):
        result = empty_alternative_grammar.match('option', 'hello')
        assert result is True

    def test_option_empty_string(self, empty_alternative_grammar):
        result = empty_alternative_grammar.match('option', '')
        assert result is True


# =====================================================================
# Многострочные правила
# =====================================================================

class TestMultiLineRules:
    """Многострочные (continued) правила."""

    def test_multiline_rule_parsed(self, multi_line_grammar):
        assert 'rule1' in multi_line_grammar.rules
        assert 'rule2' in multi_line_grammar.rules

    def test_multiline_rule_matches(self, multi_line_grammar):
        result = multi_line_grammar.match('rule2', 'test')
        assert result is True


# =====================================================================
# Рекурсивные правила
# =====================================================================

class TestRecursiveRules:
    """Рекурсивные правила."""

    def test_recursive_list(self):
        grammar = """
list ::= item ("," item)*
item ::= [a-z]+
"""
        p = Pattern(grammar)
        result = p.match('list', 'a,b,c')
        assert result is True

    def test_recursive_list_single(self):
        grammar = """
list ::= item ("," item)*
item ::= [a-z]+
"""
        p = Pattern(grammar)
        result = p.match('list', 'a')
        assert result is True

    def test_recursive_list_empty(self):
        grammar = """
list ::= item ("," item)*
item ::= [a-z]+
"""
        p = Pattern(grammar)
        result = p.match('list', '')
        assert result is False


# =====================================================================
# Квантификаторы
# =====================================================================

class TestQuantifiers:
    """Квантификаторы в грамматике."""

    def test_star_quantifier(self):
        grammar = "rule ::= [a-z]*"
        p = Pattern(grammar)
        assert p.match('rule', '') is True
        assert p.match('rule', 'abc') is True
        assert p.match('rule', '123') is False

    def test_plus_quantifier(self):
        grammar = "rule ::= [a-z]+"
        p = Pattern(grammar)
        assert p.match('rule', '') is False
        assert p.match('rule', 'a') is True

    def test_question_quantifier(self):
        grammar = "rule ::= [a-z]?"
        p = Pattern(grammar)
        assert p.match('rule', '') is True
        assert p.match('rule', 'a') is True

    def test_braced_quantifier(self):
        grammar = "rule ::= [a-z]{3}"
        p = Pattern(grammar)
        assert p.match('rule', 'abc') is True
        assert p.match('rule', 'ab') is False
        assert p.match('rule', 'abcd') is False

    def test_braced_range_quantifier(self):
        grammar = "rule ::= [a-z]{2,4}"
        p = Pattern(grammar)
        assert p.match('rule', 'ab') is True
        assert p.match('rule', 'abc') is True
        assert p.match('rule', 'abcd') is True
        assert p.match('rule', 'a') is False


# =====================================================================
# Группировка
# =====================================================================

class TestGrouping:
    """Группировка скобками."""

    def test_group_with_star(self):
        grammar = 'rule ::= ("a" "b")*'
        p = Pattern(grammar)
        assert p.match('rule', '') is True
        assert p.match('rule', 'ab') is True
        assert p.match('rule', 'abab') is True

    def test_group_with_plus(self):
        grammar = 'rule ::= ("a" "b")+'
        p = Pattern(grammar)
        assert p.match('rule', '') is False
        assert p.match('rule', 'ab') is True
        assert p.match('rule', 'abab') is True


# =====================================================================
# Альтернативы
# =====================================================================

class TestAlternatives:
    """Альтернативы через |."""

    def test_simple_alternative(self):
        grammar = 'rule ::= "a" | "b"'
        p = Pattern(grammar)
        assert p.match('rule', 'a') is True
        assert p.match('rule', 'b') is True
        assert p.match('rule', 'c') is False

    def test_alternative_with_char_class(self):
        grammar = 'rule ::= "a" | [0-9]+'
        p = Pattern(grammar)
        assert p.match('rule', 'a') is True
        assert p.match('rule', '123') is True


# =====================================================================
# Валидация входных данных
# =====================================================================

class TestInputValidation:
    """Валидация входных данных."""

    def test_match_with_int_rule_raises(self, simple_pattern):
        """Audit 2.1: валидация типов — int для rule_name вызывает TypeError."""
        with pytest.raises(TypeError, match="rule_name должен быть строкой"):
            simple_pattern.match(123, 'test')

    def test_match_with_none_text_raises(self, simple_pattern):
        """Audit 2.1: валидация типов — None для text вызывает TypeError."""
        with pytest.raises(TypeError):
            simple_pattern.match('username', None)

    def test_parse_with_int_rule_raises(self, simple_pattern):
        """Audit 2.1: валидация типов."""
        with pytest.raises(TypeError, match="rule_name должен быть строкой"):
            simple_pattern.parse(123, 'test')

    def test_findall_with_int_rule_raises(self, simple_pattern):
        """Audit 2.1: валидация типов."""
        with pytest.raises(TypeError, match="rule_name должен быть строкой"):
            simple_pattern.findall(123, 'test')


# =====================================================================
# Regex engines
# =====================================================================

class TestRegexEngines:
    """Проверка regex-движков."""

    def test_match_pattern_compiled(self, simple_pattern):
        engines = simple_pattern.regex_engines['username']
        assert 'match' in engines
        assert isinstance(engines['match'], re.Pattern)

    def test_findall_pattern_compiled(self, simple_pattern):
        engines = simple_pattern.regex_engines['username']
        assert 'findall' in engines
        assert isinstance(engines['findall'], re.Pattern)

    def test_match_vs_findall_different(self, simple_pattern):
        engines = simple_pattern.regex_engines['username']
        match_pat = engines['match'].pattern
        findall_pat = engines['findall'].pattern
        assert match_pat.startswith('^')
        assert match_pat.endswith('$')
        assert not findall_pat.startswith('^')
        assert not findall_pat.endswith('$')


# =====================================================================
# Комбинированные сценарии
# =====================================================================

class TestCombinedScenarios:
    """Комбинированные сценарии использования."""

    def test_email_full_flow(self, simple_pattern):
        assert simple_pattern.match('email', 'test@example.com') is True
        assert simple_pattern.match('email', 'invalid') is False

    def test_findall_in_sentence(self, simple_pattern):
        result = simple_pattern.findall('username', 'user1 and user2 and user3')
        # 'and' тоже совпадает с [a-zA-Z0-9._%+-]+, поэтому 5, а не 3
        assert len(result) == 5
        assert 'user1' in result
        assert 'user2' in result
        assert 'user3' in result

    def test_parse_and_match_same_text(self, simple_pattern):
        text = 'testuser'
        match_result = simple_pattern.match('username', text)
        parse_result = simple_pattern.parse('username', text)
        assert match_result is True
        assert parse_result is not None

    def test_info_matches_state(self, simple_pattern):
        info = simple_pattern.get_info()
        assert info['total_rules'] == len(simple_pattern.rules)
        assert set(info['regex_rules']) == simple_pattern.regex_rules
        assert set(info['parser_rules']) == simple_pattern.recursive_rules
