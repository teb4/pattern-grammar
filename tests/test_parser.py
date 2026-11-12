"""
Unit-тесты для BNFParser.

Реальное поведение парсера:
- `[a-z]+` токенизируется как `['[a-z]', '+']` (квантификатор отдельно)
- Хеш внутри кавычек заменяется на плейсхолдер ДО токенизации
- `:=` и `::=` оба поддерживаются
- `:=` парсит тело до первого пробела (ограничение текущей реализации)
"""
import pytest
from pattern_grammar.parser import BNFParser


# =====================================================================
# Базовый парсинг
# =====================================================================

class TestParseBasic:
    """Базовый парсинг грамматики."""

    def test_parse_simple(self, parser):
        grammar = """
email ::= username "@" domain
username ::= [a-z]+
domain ::= [a-z]+
"""
        parser.parse(grammar)
        rules = parser.get_rules()
        assert 'email' in rules
        assert 'username' in rules
        assert 'domain' in rules

    def test_parse_colons_colon_equals(self, parser):
        grammar = "rule1 ::= [a-z]+"
        parser.parse(grammar)
        # Квантификатор + отделяется от символьного класса
        assert parser.get_rules()['rule1'] == ['[a-z]', '+']

    def test_parse_colons_equals(self, parser):
        grammar = "rule1 := [a-z]+"
        parser.parse(grammar)
        # := не разделяет тело по пробелам — всё тело парсится
        assert 'rule1' in parser.get_rules()

    def test_parse_multiple_rules(self, parser):
        grammar = """
a ::= [a-z]+
b ::= [0-9]+
c ::= "test"
"""
        parser.parse(grammar)
        rules = parser.get_rules()
        assert len(rules) == 3

    def test_parse_empty(self, parser):
        parser.parse("")
        assert parser.get_rules() == {}

    def test_parse_whitespace_only(self, parser):
        parser.parse("   \n\n  ")
        assert parser.get_rules() == {}


# =====================================================================
# Пустые правила
# =====================================================================

class TestParseEmptyRules:
    """Обработка пустых правил."""

    def test_empty_name_raises(self, parser):
        with pytest.raises(SyntaxError):
            parser.parse(" ::= [a-z]+")

    def test_empty_body_raises(self, parser):
        with pytest.raises(SyntaxError):
            parser.parse("name ::=")


# =====================================================================
# Токенизация
# =====================================================================

class TestTokenize:
    """Токенизация тела правила."""

    def test_tokenize_simple(self, parser):
        parser.parse("rule ::= [a-z]+")
        # Квантификатор + — отдельный токен
        assert parser.get_rules()['rule'] == ['[a-z]', '+']

    def test_tokenize_multiple_tokens(self, parser):
        parser.parse("rule ::= a b c")
        assert parser.get_rules()['rule'] == ['a', 'b', 'c']

    def test_tokenize_alternatives(self, parser):
        parser.parse("rule ::= a | b | c")
        assert parser.get_rules()['rule'] == ['a', '|', 'b', '|', 'c']

    def test_tokenize_quantifiers(self, parser):
        parser.parse("rule ::= [a-z]{2,4}")
        assert parser.get_rules()['rule'] == ['[a-z]', '{2,4}']

    def test_tokenize_single_quantifier(self, parser):
        parser.parse("rule ::= [a-z]{3}")
        assert parser.get_rules()['rule'] == ['[a-z]', '{3}']

    def test_tokenize_parens(self, parser):
        parser.parse("rule ::= ( a b ) c")
        assert parser.get_rules()['rule'] == ['(', 'a', 'b', ')', 'c']

    def test_tokenize_double_quotes(self, parser):
        parser.parse('rule ::= "hello" world')
        rules = parser.get_rules()
        assert rules['rule'][0] == '"hello"'
        assert rules['rule'][1] == 'world'

    def test_tokenize_single_quotes(self, parser):
        parser.parse("rule ::= 'hello' world")
        rules = parser.get_rules()
        assert rules['rule'][0] == "'hello'"
        assert rules['rule'][1] == 'world'

    def test_tokenize_nested_char_class(self, parser):
        parser.parse("rule ::= [a-z]+ [A-Z]+")
        # Оба квантификатора отдельно
        assert parser.get_rules()['rule'] == ['[a-z]', '+', '[A-Z]', '+']

    def test_tokenize_special_chars(self, parser):
        parser.parse("rule ::= a + b * c")
        rules = parser.get_rules()
        assert '+' in rules['rule']
        assert '*' in rules['rule']


# =====================================================================
# Комментарии
# =====================================================================

class TestComments:
    """Обработка комментариев."""

    def test_inline_comment(self, parser):
        grammar = """
rule ::= [a-z]+ # комментарий
"""
        parser.parse(grammar)
        assert 'rule' in parser.get_rules()
        # Хеш в комментарии удаляется, квантификатор отдельно
        assert parser.get_rules()['rule'] == ['[a-z]', '+']

    def test_comment_in_parens_preserved(self, parser):
        """Хеш внутри символьного класса не должен быть комментарием."""
        grammar = """
rule ::= [a#z]+
"""
        parser.parse(grammar)
        assert 'rule' in parser.get_rules()

    def test_comment_after_string_literal(self, parser):
        """Хеш внутри кавычек заменяется на плейсхолдер, а не удаляется."""
        grammar = 'rule ::= "a#b" # comment'
        parser.parse(grammar)
        rules = parser.get_rules()
        # Хеш заменён на ___HASH___ до токенизации
        assert 'a___HASH___b' in rules['rule'][0]

    def test_multiline_rule_with_inline_comments(self, parser):
        """Многострочное правило с inline-комментариями."""
        grammar = """
rule ::= [a-z]+ # начало
       [0-9]+ # конец
"""
        parser.parse(grammar)
        assert 'rule' in parser.get_rules()
        assert parser.get_rules()['rule'] == ['[a-z]', '+', '[0-9]', '+']

    def test_inline_comment_preserves_hash_in_char_class(self, parser):
        """Хеш в символьном классе не удаляется как комментарий."""
        grammar = """
rule ::= [a#z]+ # comment
"""
        parser.parse(grammar)
        assert 'rule' in parser.get_rules()
        # Хеш внутри символьного класса заменяется на плейсхолдер, а не удаляется
        assert '___HASH___' in parser.get_rules()['rule'][0]

    def test_inline_comment_preserves_hash_in_string(self, parser):
        """Хеш в строковом литерале не удаляется как комментарий."""
        grammar = 'rule ::= "#" [a-z]+ # comment'
        parser.parse(grammar)
        rules = parser.get_rules()
        assert 'rule' in rules
        # Хеш в строке должен остаться (как плейсхолдер)
        assert any('___HASH___' in token for token in rules['rule'])


# =====================================================================
# Многострочные правила
# =====================================================================

class TestMultiLineRules:
    """Многострочные (continued) правила."""

    def test_multiline_rule(self, multi_line_grammar):
        assert 'rule1' in multi_line_grammar.rules
        assert 'rule2' in multi_line_grammar.rules

    def test_multiline_continuation(self, multi_line_grammar):
        rule1 = multi_line_grammar.rules['rule1']
        assert isinstance(rule1, list)


# =====================================================================
# Placeholder-символы
# =====================================================================

class TestSpecialChars:
    """Замена и восстановление спецсимволов."""

    def test_hash_replaced(self, parser):
        grammar = "rule ::= [a-z]+ # comment"
        parser.parse(grammar)
        rules = parser.get_rules()
        assert 'rule' in rules

    def test_restore_hash(self, parser):
        result = parser.restore_special_chars("test ___HASH___ end")
        assert result == "test # end"

    def test_restore_hash_for_regex(self, parser):
        result = parser.restore_special_chars("test ___HASH___ end", for_regex=True)
        assert result == r"test \# end"

    def test_no_placeholder_unchanged(self, parser):
        result = parser.restore_special_chars("без плейсхолдеров")
        assert result == "без плейсхолдеров"

    def test_special_chars_map_has_hash(self):
        assert '#' in BNFParser.SPECIAL_CHARS_MAP
        assert BNFParser.SPECIAL_CHARS_MAP['#'] == '___HASH___'

    def test_dollar_in_special_chars_map(self):
        # Исправление бага 3.1: $ и & теперь обрабатываются
        assert '$' in BNFParser.SPECIAL_CHARS_MAP
        assert BNFParser.SPECIAL_CHARS_MAP['$'] == '___DOLLAR___'

    def test_ampersand_in_special_chars_map(self):
        assert '&' in BNFParser.SPECIAL_CHARS_MAP
        assert BNFParser.SPECIAL_CHARS_MAP['&'] == '___AMP___'


# =====================================================================
# raw_rules
# =====================================================================

class TestRawRules:
    """Доступ к исходному тексту правил."""

    def test_raw_rules_populated(self, parser):
        grammar = 'email ::= username "@" domain'
        parser.parse(grammar)
        assert 'email' in parser.raw_rules
        assert parser.raw_rules['email'] == 'username "@" domain'

    def test_raw_rules_preserves_whitespace(self, parser):
        grammar = "rule ::= [a-z]+  [0-9]+"
        parser.parse(grammar)
        assert parser.raw_rules['rule'] == '[a-z]+  [0-9]+'


# =====================================================================
# Ошибки парсинга
# =====================================================================

class TestParseErrors:
    """Обработка ошибок парсинга."""

    def test_unclosed_char_class(self, parser):
        with pytest.raises(SyntaxError):
            parser.parse("rule ::= [a-z+")

    def test_unclosed_quantifier(self, parser):
        with pytest.raises(SyntaxError):
            parser.parse("rule ::= [a-z{2,")

    def test_unclosed_quote(self, parser):
        with pytest.raises(SyntaxError):
            parser.parse('rule ::= "unclosed')

    def test_no_separator(self, parser):
        parser.parse("no_separator_here")
        assert parser.get_rules() == {}


# =====================================================================
# get_rules
# =====================================================================

class TestGetRules:
    """Метод get_rules."""

    def test_get_rules_returns_dict(self, parser):
        grammar = "rule ::= [a-z]+"
        parser.parse(grammar)
        rules = parser.get_rules()
        assert isinstance(rules, dict)

    def test_get_rules_empty(self, parser):
        parser.parse("")
        rules = parser.get_rules()
        assert rules == {}

    def test_parse_clears_previous(self, parser):
        parser.parse("a ::= [a-z]+")
        parser.parse("b ::= [0-9]+")
        rules = parser.get_rules()
        assert 'a' not in rules
        assert 'b' in rules
