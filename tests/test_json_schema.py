"""
Unit-тесты для Pattern.to_json_schema().

Фаза 2 плана Pydantic-интеграции: генерация JSON Schema
из грамматики pattern-grammar.
"""
import pytest
from pattern_grammar import Pattern, PatternError


class TestToJsonSchemaRegexRule:
    """to_json_schema для нерекурсивных (regex) правил."""

    def test_simple_regex_rule(self):
        """Простое regex-правило должно вернуть pattern."""
        grammar = '''
digit ::= [0-9]
'''
        p = Pattern(grammar)
        schema = p.to_json_schema('digit')
        assert schema["type"] == "string"
        assert "pattern" in schema
        assert "description" not in schema

    def test_complex_regex_rule(self):
        """Сложное regex-правило с под-правилами."""
        grammar = '''
username ::= [a-z]+
domain   ::= [a-z]+
email    ::= username "@" domain "." [a-z]{2,}
'''
        p = Pattern(grammar)
        schema = p.to_json_schema('email')
        assert schema["type"] == "string"
        assert "pattern" in schema
        assert "description" not in schema
        # pattern не должен содержать ^ и $
        assert not schema["pattern"].startswith('^')
        assert not schema["pattern"].endswith('$')

    def test_regex_rule_no_outer_fail(self):
        """Правило без @fail тоже должно работать."""
        grammar = '''
word ::= [a-z]+
'''
        p = Pattern(grammar)
        schema = p.to_json_schema('word')
        assert "pattern" in schema


class TestToJsonSchemaParserRule:
    """to_json_schema для рекурсивных (parser) правил."""

    def test_recursive_rule_has_no_pattern(self):
        """Рекурсивное правило НЕ должно содержать pattern."""
        grammar = '''
expr ::= term (("+" | "-") term)*
term ::= factor (("*" | "/") factor)*
factor ::= NUMBER | "(" expr ")"
NUMBER ::= [0-9]+
'''
        p = Pattern(grammar)
        schema = p.to_json_schema('expr')
        assert schema["type"] == "string"
        assert "pattern" not in schema
        assert "description" in schema

    def test_recursive_rule_description_contains_bnf(self):
        """Описание рекурсивного правила должно содержать BNF."""
        grammar = '''
expr ::= term ("+" | "-") term
term ::= factor ("*" | "/") factor
factor ::= NUMBER | "(" expr ")"
NUMBER ::= [0-9]+
'''
        p = Pattern(grammar)
        schema = p.to_json_schema('expr')
        assert "description" in schema
        assert "+" in schema["description"]

    def test_non_recursive_has_pattern_not_description(self):
        """Нерекурсивное правило НЕ должно содержать description."""
        grammar = '''
expr ::= term ("+" | "-") term
term ::= factor ("*" | "/") factor
factor ::= NUMBER | "(" expr ")"
NUMBER ::= [0-9]+
'''
        p = Pattern(grammar)
        schema = p.to_json_schema('NUMBER')
        assert "pattern" in schema
        assert "description" not in schema


class TestToJsonSchemaEdgeCases:
    """Краевые случаи."""

    def test_unknown_rule_raises(self):
        """Неизвестное правило должно вызвать PatternError."""
        grammar = '''
word ::= [a-z]+
'''
        p = Pattern(grammar)
        with pytest.raises(PatternError, match="не найдено"):
            p.to_json_schema('unknown')

    def test_invalid_rule_name_type(self):
        """Некорректный тип rule_name должен вызвать TypeError."""
        grammar = '''
word ::= [a-z]+
'''
        p = Pattern(grammar)
        with pytest.raises(TypeError):
            p.to_json_schema(123)  # type: ignore

    def test_builtin_class_rule(self):
        """Правило с встроенным классом."""
        grammar = '''
mydigit ::= digit
'''
        p = Pattern(grammar)
        schema = p.to_json_schema('mydigit')
        assert schema["type"] == "string"
        assert "pattern" in schema
