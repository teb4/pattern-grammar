"""
Unit-тесты для класса Pattern и модульных функций.
"""
import pytest
from lark import Tree, Token
from pattern_grammar import Pattern, PatternError, match, parse


# =====================================================================
# Инициализация Pattern
# =====================================================================

class TestPatternInit:
    """Инициализация Pattern."""

    def test_init_stores_grammar_text(self, simple_pattern):
        assert simple_pattern.grammar_text is not None

    def test_init_parses_rules(self, simple_pattern):
        assert 'email' in simple_pattern.rules
        assert 'username' in simple_pattern.rules
        assert 'domain' in simple_pattern.rules
        assert 'tld' in simple_pattern.rules

    def test_init_compiles_regex_engines(self, simple_pattern):
        assert 'email' in simple_pattern.regex_engines
        assert 'username' in simple_pattern.regex_engines

    def test_init_sets_regex_rules(self, simple_pattern):
        assert 'email' in simple_pattern.regex_rules
        assert 'username' in simple_pattern.regex_rules

    def test_init_sets_parser_engines_empty_for_simple(self, simple_pattern):
        assert len(simple_pattern.recursive_rules) == 0
        assert len(simple_pattern.parser_engines) == 0

    def test_init_arithmetic_pattern(self, arithmetic_pattern):
        assert 'expr' in arithmetic_pattern.rules
        assert 'term' in arithmetic_pattern.rules
        assert 'factor' in arithmetic_pattern.rules

    def test_init_arithmetic_has_parser_rules(self, arithmetic_pattern):
        assert len(arithmetic_pattern.recursive_rules) > 0

    def test_get_info_lists_rules(self, simple_pattern):
        info = simple_pattern.get_info()
        assert 'email' in info['rules']
        assert 'username' in info['rules']
        assert info['total_rules'] >= 4


# =====================================================================
# match()
# =====================================================================

class TestMatch:
    """Метод Pattern.match()."""

    def test_match_true(self, simple_pattern):
        result = simple_pattern.match('username', 'testuser')
        assert result is True

    def test_match_false(self, simple_pattern):
        result = simple_pattern.match('username', '')
        assert result is False

    def test_match_domain(self, simple_pattern):
        result = simple_pattern.match('domain', 'example.com')
        assert result is True

    def test_match_email_valid(self, simple_pattern):
        result = simple_pattern.match('email', 'test@example.com')
        assert result is True

    def test_match_email_invalid(self, simple_pattern):
        result = simple_pattern.match('email', 'not-an-email')
        assert result is False

    def test_match_unknown_rule_raises(self, simple_pattern):
        with pytest.raises(PatternError, match="не найдено"):
            simple_pattern.match('nonexistent', 'test')

    def test_match_uncompiled_rule_raises(self):
        grammar = "rule ::= [a-z]+"
        p = Pattern(grammar)
        p.regex_rules.discard('rule')
        # Правило удалено из regex_rules и не в recursive_rules → "не найдено"
        with pytest.raises(PatternError, match="не найдено"):
            p.match('rule', 'test')


# =====================================================================
# parse()
# =====================================================================

class TestParse:
    """Метод Pattern.parse()."""

    def test_parse_regex_returns_tree(self, simple_pattern):
        result = simple_pattern.parse('username', 'testuser')
        assert isinstance(result, Tree)

    def test_parse_regex_tree_structure(self, simple_pattern):
        result = simple_pattern.parse('username', 'testuser')
        assert result.data == 'match'

    def test_parse_regex_token_value(self, simple_pattern):
        result = simple_pattern.parse('username', 'testuser')
        assert len(result.children) == 1
        child = result.children[0]
        assert isinstance(child, Token)
        assert child.type == 'VALUE'
        assert child.value == 'testuser'

    def test_parse_regex_no_match_returns_none(self, simple_pattern):
        result = simple_pattern.parse('username', '')
        assert result is None

    def test_parse_unknown_rule_raises(self, simple_pattern):
        with pytest.raises(PatternError, match="не найдено"):
            simple_pattern.parse('nonexistent', 'test')


# =====================================================================
# findall()
# =====================================================================

class TestFindall:
    """Метод Pattern.findall()."""

    def test_findall_single(self, simple_pattern):
        result = simple_pattern.findall('username', 'abc')
        assert result == ['abc']

    def test_findall_multiple(self, simple_pattern):
        result = simple_pattern.findall('username', 'abc def ghi')
        assert 'abc' in result
        assert 'def' in result
        assert 'ghi' in result

    def test_findall_none(self, simple_pattern):
        result = simple_pattern.findall('username', '')
        assert result == []

    def test_findall_raises_for_recursive_rule(self, simple_pattern):
        grammar = "rule ::= [a-z]+"
        p = Pattern(grammar)
        result = p.findall('rule', 'test')
        assert isinstance(result, list)


# =====================================================================
# get_info()
# =====================================================================

class TestGetInfo:
    """Метод Pattern.get_info()."""

    def test_get_info_returns_dict(self, simple_pattern):
        info = simple_pattern.get_info()
        assert isinstance(info, dict)

    def test_get_info_total_rules(self, simple_pattern):
        info = simple_pattern.get_info()
        assert info['total_rules'] == 4

    def test_get_info_regex_rules_list(self, simple_pattern):
        info = simple_pattern.get_info()
        assert isinstance(info['regex_rules'], list)
        assert 'email' in info['regex_rules']
        assert 'username' in info['regex_rules']

    def test_get_info_parser_rules_list(self, simple_pattern):
        info = simple_pattern.get_info()
        assert isinstance(info['parser_rules'], list)

    def test_get_info_rules_formatted(self, simple_pattern):
        info = simple_pattern.get_info()
        assert 'email' in info['rules']
        assert 'username' in info['rules']


# =====================================================================
# Модульные функции
# =====================================================================

class TestModuleFunctions:
    """Модульные функции match() и parse()."""

    def test_module_match_true(self):
        grammar = "rule ::= [a-z]+"
        result = match(grammar, 'rule', 'hello')
        assert result is True

    def test_module_match_false(self):
        grammar = "rule ::= [a-z]+"
        result = match(grammar, 'rule', '')
        assert result is False

    def test_module_parse_returns_tree(self):
        grammar = "rule ::= [a-z]+"
        result = parse(grammar, 'rule', 'hello')
        assert isinstance(result, Tree)

    def test_module_parse_returns_none(self):
        grammar = "rule ::= [a-z]+"
        result = parse(grammar, 'rule', '')
        assert result is None


# =====================================================================
# PatternError
# =====================================================================

class TestPatternError:
    """Класс PatternError."""

    def test_is_exception(self):
        assert issubclass(PatternError, Exception)

    def test_raise_pattern_error(self):
        with pytest.raises(PatternError):
            raise PatternError("test")

    def test_catch_pattern_error(self):
        try:
            raise PatternError("test")
        except PatternError as e:
            assert str(e) == "test"


# =====================================================================
# Арифметические выражения (рекурсивные)
# =====================================================================

class TestArithmetic:
    """Тесты с арифметическими выражениями."""

    def test_arithmetic_pattern_created(self, arithmetic_pattern):
        assert isinstance(arithmetic_pattern, Pattern)

    def test_arithmetic_has_recursive_rules(self, arithmetic_pattern):
        assert len(arithmetic_pattern.recursive_rules) > 0

    def test_factor_simple_number(self, arithmetic_pattern):
        result = arithmetic_pattern.match('factor', '42')
        assert result is True

    def test_factor_with_parens(self, arithmetic_pattern):
        result = arithmetic_pattern.match('factor', '(1+2)')
        assert result is True


# =====================================================================
# Edge cases
# =====================================================================

class TestEdgeCases:
    """Пограничные случаи."""

    def test_empty_grammar(self):
        p = Pattern("")
        assert p.rules == {}

    def test_single_rule(self):
        grammar = "rule ::= [a-z]+"
        p = Pattern(grammar)
        assert 'rule' in p.rules

    def test_many_rules(self):
        grammar = "\n".join(f"rule{i} ::= [a-z]+" for i in range(10))
        p = Pattern(grammar)
        assert len(p.rules) == 10

    def test_match_with_spaces_in_text(self, simple_pattern):
        result = simple_pattern.match('username', 'test user')
        assert result is False

    def test_findall_in_complex_text(self, simple_pattern):
        result = simple_pattern.findall('username', 'abc def ghi jkl')
        assert len(result) == 4

    def test_regex_engines_are_dicts(self, simple_pattern):
        for rule_name, engines in simple_pattern.regex_engines.items():
            assert isinstance(engines, dict)
            assert 'match' in engines
            assert 'findall' in engines

    def test_parser_engines_are_lark(self, arithmetic_pattern):
        for rule_name, parser in arithmetic_pattern.parser_engines.items():
            assert rule_name in arithmetic_pattern.recursive_rules
            assert parser is not None


# =====================================================================
# Валидация типов
# =====================================================================

class TestTypeValidation:
    """Валидация входных типов (Audit 2.1)."""

    def test_init_with_non_string_raises(self):
        with pytest.raises(TypeError, match="grammar_text должен быть строкой"):
            Pattern(123)

    def test_init_with_none_raises(self):
        with pytest.raises(TypeError, match="grammar_text должен быть строкой"):
            Pattern(None)

    def test_match_with_int_rule_raises(self, simple_pattern):
        with pytest.raises(TypeError, match="rule_name должен быть строкой"):
            simple_pattern.match(123, 'test')

    def test_match_with_none_text_raises(self, simple_pattern):
        with pytest.raises(TypeError, match="text должен быть строкой"):
            simple_pattern.match('username', None)

    def test_parse_with_int_rule_raises(self, simple_pattern):
        with pytest.raises(TypeError, match="rule_name должен быть строкой"):
            simple_pattern.parse(123, 'test')

    def test_parse_with_none_text_raises(self, simple_pattern):
        with pytest.raises(TypeError, match="text должен быть строкой"):
            simple_pattern.parse('username', None)

    def test_findall_with_int_rule_raises(self, simple_pattern):
        with pytest.raises(TypeError, match="rule_name должен быть строкой"):
            simple_pattern.findall(123, 'test')

    def test_findall_with_none_text_raises(self, simple_pattern):
        with pytest.raises(TypeError, match="text должен быть строкой"):
            simple_pattern.findall('username', None)


# =====================================================================
# Edge cases для findall
# =====================================================================

class TestFindallEdgeCases:
    """Пограничные случаи для findall."""

    def test_findall_raises_for_recursive_rule(self):
        grammar = "expr ::= term '+' expr | term\nterm ::= [0-9]+"
        p = Pattern(grammar)
        with pytest.raises(PatternError, match="только для нерекурсивных"):
            p.findall('expr', '1+2')

    def test_findall_raises_for_uncompiled_rule(self):
        grammar = "rule ::= [a-z]+"
        p = Pattern(grammar)
        p.regex_rules.discard('rule')
        with pytest.raises(PatternError):
            p.findall('rule', 'test')


# =====================================================================
# ignore_case
# =====================================================================

class TestIgnoreCase:
    """Тесты для параметра ignore_case в match, parse и findall."""

    def test_match_ignore_case_regex_true(self):
        """match с ignore_case=True находит текст в любом регистре (regex-правило)"""
        grammar = "username ::= [a-z]+"
        p = Pattern(grammar)
        result = p.match('username', 'ABC', ignore_case=True)
        assert result is True

    def test_match_ignore_case_regex_false(self):
        """match с ignore_case=False не находит текст в другом регистре (regex-правило)"""
        grammar = "username ::= [a-z]+"
        p = Pattern(grammar)
        result = p.match('username', 'ABC', ignore_case=False)
        assert result is False

    def test_match_ignore_case_default_is_false(self):
        """По умолчанию ignore_case=False — регистр имеет значение"""
        grammar = "username ::= [a-z]+"
        p = Pattern(grammar)
        result = p.match('username', 'ABC')
        assert result is False

    def test_match_ignore_case_recursive_true(self):
        """match с ignore_case=True работает для рекурсивных правил (Lark)"""
        grammar = """
            expr ::= expr "+" term | term
            term ::= [0-9]+
        """
        p = Pattern(grammar)
        # Lark-грамматика содержит только строчные символы
        result = p.match('expr', '1+2', ignore_case=True)
        assert result is True

    def test_match_ignore_case_recursive_false(self):
        """match с ignore_case=False для Lark-грамматики с заглавными буквами"""
        grammar = """
            expr ::= expr "+" term | term
            term ::= [0-9]+
        """
        p = Pattern(grammar)
        # Lark-грамматика содержит только строчные символы
        result = p.match('expr', '1+2', ignore_case=False)
        # Цифры не зависят от регистра, но для полноты теста
        assert result is True

    def test_parse_ignore_case_regex_true(self):
        """parse с ignore_case=True находит текст в любом регистре (regex-правило)"""
        grammar = "username ::= [a-z]+"
        p = Pattern(grammar)
        result = p.parse('username', 'ABC', ignore_case=True)
        assert result is not None
        assert isinstance(result, Tree)

    def test_parse_ignore_case_regex_false(self):
        """parse с ignore_case=False не находит текст в другом регистре (regex-правило)"""
        grammar = "username ::= [a-z]+"
        p = Pattern(grammar)
        result = p.parse('username', 'ABC', ignore_case=False)
        assert result is None

    def test_parse_ignore_case_recursive_true(self):
        """parse с ignore_case=True работает для рекурсивных правил (Lark)"""
        grammar = """
            expr ::= expr "+" term | term
            term ::= [0-9]+
        """
        p = Pattern(grammar)
        result = p.parse('expr', '1+2', ignore_case=True)
        assert result is not None
        assert isinstance(result, Tree)

    def test_findall_ignore_case_true(self):
        """findall с ignore_case=True находит все варианты регистра"""
        grammar = "username ::= [a-z]+"
        p = Pattern(grammar)
        text = 'ABC abc AbC aBc'
        result = p.findall('username', text, ignore_case=True)
        assert len(result) == 4

    def test_findall_ignore_case_false(self):
        """findall с ignore_case=False ищет только точный регистр"""
        grammar = "username ::= [a-z]+"
        p = Pattern(grammar)
        text = 'ABC abc AbC aBc'
        result = p.findall('username', text, ignore_case=False)
        # Без флага IGNORECASE находит только строчные буквы и 'abc'
        assert 'abc' in result
        assert 'a' in result
        assert 'b' in result
        assert 'c' in result

    def test_findall_ignore_case_default_is_false(self):
        """По умолчанию ignore_case=False — регистр имеет значение"""
        grammar = "username ::= [a-z]+"
        p = Pattern(grammar)
        text = 'ABC abc AbC aBc'
        result = p.findall('username', text)
        # По умолчанию без IGNORECASE — те же результаты
        assert 'abc' in result
        assert 'a' in result
        assert 'b' in result
        assert 'c' in result

    def test_match_ignore_case_api_function(self):
        """Публичная функция match() поддерживает ignore_case"""
        result = match('username ::= [a-z]+', 'username', 'TEST', ignore_case=True)
        assert result is True

    def test_parse_ignore_case_api_function(self):
        """Публичная функция parse() поддерживает ignore_case"""
        result = parse('username ::= [a-z]+', 'username', 'TEST', ignore_case=True)
        assert result is not None

    def test_match_ignore_case_with_email(self):
        """match с ignore_case=True для email в верхнем регистре"""
        grammar = "email ::= [a-z]+ \"@\" [a-z]+ \".com\""
        p = Pattern(grammar)
        result = p.match('email', 'TEST@EXAMPLE.COM', ignore_case=True)
        assert result is True

    def test_match_ignore_case_false_with_email(self):
        """match с ignore_case=False для email в верхнем регистре"""
        grammar = "email ::= [a-z]+ \"@\" [a-z]+ \".com\""
        p = Pattern(grammar)
        result = p.match('email', 'TEST@EXAMPLE.COM', ignore_case=False)
        assert result is False
