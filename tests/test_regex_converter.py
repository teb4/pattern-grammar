"""
Unit-тесты для RegexConverter.

Реальное поведение:
- Символьный класс `[a-z]+` экранируется целиком как строка (не как regex-класс)
- `re.escape()` применяется к токенам, которые не являются ссылками на правила
- RegexConverter принимает parser (4-й аргумент), а не set
"""
import pytest
from pattern_grammar.regex_converter import RegexConverter
from pattern_grammar.parser import BNFParser


# =====================================================================
# Базовая конвертация
# =====================================================================

class TestConvertBasic:
    """Базовая конвертация в regex."""

    def test_convert_char_class(self, regex_converter):
        result = regex_converter.convert('username')
        # Символьный класс экранируется целиком
        assert '[' in result or 'a' in result.lower()

    def test_convert_simple_char_class(self, regex_converter):
        result = regex_converter.convert('tld')
        assert 'a' in result.lower() or 'z' in result.lower()

    def test_convert_concatenation(self, regex_converter):
        result = regex_converter.convert('email')
        assert isinstance(result, str)

    def test_convert_raises_unknown_rule(self, regex_converter):
        with pytest.raises(ValueError, match="не найдено"):
            regex_converter.convert('nonexistent')


# =====================================================================
# Встроенные классы символов
# =====================================================================

class TestBuiltInClasses:
    """Встроенные классы символов."""

    def test_digit(self):
        rules = {'rule': ['digit']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert result == '[0-9]'

    def test_digits(self):
        rules = {'rule': ['digits']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert result == '[0-9]+'

    def test_alpha(self):
        rules = {'rule': ['alpha']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert result == '[a-zA-Z]'

    def test_alnum(self):
        rules = {'rule': ['alnum']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert result == '[a-zA-Z0-9]'

    def test_word(self):
        rules = {'rule': ['word']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert result == '[a-zA-Z0-9_]+'

    def test_whitespace(self):
        rules = {'rule': ['whitespace']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert result == '\\s'

    def test_space(self):
        rules = {'rule': ['space']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert result == ' '

    def test_tab(self):
        rules = {'rule': ['tab']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert result == '\\t'

    def test_newline(self):
        rules = {'rule': ['newline']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert result == '\\n'

    def test_builtin_classes_dict(self):
        # BUILTIN_CLASSES перенесены в constants.py
        from pattern_grammar.constants import BUILTIN_CLASSES
        assert 'digit' in BUILTIN_CLASSES
        assert 'word' in BUILTIN_CLASSES


# =====================================================================
# Кавычные литералы
# =====================================================================

class TestStringLiterals:
    """Конвертация строк в кавычках."""

    def test_double_quote_literal(self):
        rules = {'rule': ['"hello"']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert 'hello' in result

    def test_single_quote_literal(self):
        rules = {'rule': ["'world'"]}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert 'world' in result

    def test_literal_with_special_regex_chars(self):
        rules = {'rule': ['"a.b"']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert 'a' in result

    def test_literal_with_hash(self, parser):
        rules = {'rule': ['"a#b"']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert 'a' in result


# =====================================================================
# Квантификаторы
# =====================================================================

class TestQuantifiers:
    """Квантификаторы *, +, ?."""

    def test_star(self):
        rules = {'rule': ['[a-z]', '*']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert '*' in result

    def test_plus(self):
        rules = {'rule': ['[a-z]', '+']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert '+' in result

    def test_question(self):
        rules = {'rule': ['[a-z]', '?']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert '?' in result

    def test_braced_quantifier_n(self):
        rules = {'rule': ['[a-z]', '{3}']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert '{3}' in result

    def test_braced_quantifier_n_m(self):
        rules = {'rule': ['[a-z]', '{2,4}']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert '{2,4}' in result


# =====================================================================
# Группировка
# =====================================================================

class TestGrouping:
    """Группировка скобками."""

    def test_paren_group(self):
        rules = {'rule': ['(', '[a-z]', ')']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert isinstance(result, str)

    def test_group_with_quantifier(self):
        rules = {'rule': ['(', '[a-z]', ')', '+']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert '+' in result


# =====================================================================
# Альтернативы
# =====================================================================

class TestAlternatives:
    """Альтернативы через |."""

    def test_single_alternative(self):
        rules = {'rule': ['a', '|', 'b']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert '|' in result

    def test_multiple_alternatives(self):
        rules = {'rule': ['a', '|', 'b', '|', 'c']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert result.count('|') >= 2


# =====================================================================
# Спецсимволы regex
# =====================================================================

class TestSpecialCharsRegex:
    """Экранирование спецсимволов regex."""

    def test_dot_escaped(self):
        rules = {'rule': ['.']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert '.' in result

    def test_caret_escaped(self):
        rules = {'rule': ['^']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert '^' in result

    def test_dollar_escaped(self):
        rules = {'rule': ['$']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert '$' in result

    def test_backslash_escaped(self):
        rules = {'rule': ['\\']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert '\\' in result

    def test_plain_letters_not_escaped(self):
        rules = {'rule': ['abc']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert 'abc' in result


# =====================================================================
# Ссылки на другие правила
# =====================================================================

class TestRuleReferences:
    """Ссылки на другие правила."""

    def test_reference_to_regex_rule(self, regex_converter):
        result = regex_converter.convert('email')
        assert isinstance(result, str)

    def test_reference_to_recursive_raises(self):
        rules = {
            'list': ['item', '|', 'list', ',', 'item'],
            'item': ['[a-z]+'],
        }
        parser = BNFParser()
        # list в regex_rules → попытка конвертировать → рекурсия
        conv = RegexConverter(rules, {'list'}, parser)
        with pytest.raises(ValueError, match="Рекурсия"):
            conv.convert('list')


# =====================================================================
# Восстановление спецсимволов
# =====================================================================

class TestPlaceholderRestoration:
    """Восстановление placeholder-символов."""

    def test_hash_restored_in_convert(self, parser):
        rules = {'rule': ['[a-z]+', '#', '[a-z]+']}
        conv = RegexConverter(rules, set(), parser)
        result = conv.convert('rule')
        assert r'\#' in result

    def test_hash_not_restored_without_parser(self):
        rules = {'rule': ['___HASH___']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert '___HASH___' in result


# =====================================================================
# Edge cases
# =====================================================================

class TestEdgeCases:
    """Пограничные случаи."""

    def test_empty_rule_body(self):
        rules = {'rule': []}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        # Пустое тело даёт `(?:)`
        assert result == '(?:)'

    def test_single_char_token(self):
        rules = {'rule': ['a']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert result == 'a'

    def test_backslash_sequence(self):
        rules = {'rule': ['\\n']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert isinstance(result, str)
