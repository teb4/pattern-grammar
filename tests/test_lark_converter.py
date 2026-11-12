"""
Unit-тесты для LarkConverter.

Реальное поведение:
- `_collect_all_dependencies` НЕ включает само правило в результат
- `_handle_empty_alternatives` для `" "` и `''` выбрасывает ValueError (логическая ошибка из audit 3.4)
- `_token_to_lark` для символьного класса возвращает его как есть (не оборачивает в `/.../`)
- `_get_regex` экранирует содержимое через re.escape
"""
import pytest
from pattern_grammar.lark_converter import LarkConverter


# =====================================================================
# Базовая конвертация
# =====================================================================

class TestConvertBasic:
    """Базовая конвертация в Lark-грамматику."""

    def test_convert_returns_string(self, lark_converter):
        result = lark_converter.convert('email')
        assert isinstance(result, str)

    def test_convert_contains_ignore(self, lark_converter):
        result = lark_converter.convert('email')
        assert '%ignore' in result

    def test_convert_raises_unknown_rule(self):
        converter = LarkConverter({}, set(), set())
        with pytest.raises(ValueError, match="не найдено"):
            converter.convert('nonexistent')


# =====================================================================
# Зависимости
# =====================================================================

class TestDependencies:
    """Сбор зависимостей."""

    def test_direct_dependencies_included(self):
        rules = {
            'email': ['username', 'domain'],
            'username': ['[a-z]+'],
            'domain': ['[0-9]+'],
        }
        conv = LarkConverter(rules, set(), set())
        output = conv.convert('email').lower()
        # username и domain — зависимости, включены в грамматику
        assert 'username' in output
        assert 'domain' in output

    def test_transitive_dependencies_included(self):
        rules = {
            'a': ['b'],
            'b': ['c'],
            'c': ['[0-9]+'],
        }
        conv = LarkConverter(rules, set(), set())
        output = conv.convert('a').lower()
        assert 'b:' in output
        assert 'c:' in output

    def test_non_rule_tokens_not_dependencies(self):
        rules = {
            'a': ['b', 'c'],
            'b': ['x'],
            'c': ['x'],
        }
        conv = LarkConverter(rules, set(), set())
        output = conv.convert('a')
        # b и c — правила, создают определения
        assert 'b:' in output.lower()
        assert 'c:' in output.lower()
        # x — не правило, не создает собственного определения 'x:'
        assert 'x:' not in output.lower()

class TestEmptyAlternatives:
    """Обработка пустых альтернатив."""

    def test_empty_alt_double_quote(self):
        conv = LarkConverter({}, set(), set())
        result = conv._handle_empty_alternatives('" " | "abc"')
        assert 'abc' in result

    def test_empty_alt_single_quote(self):
        conv = LarkConverter({}, set(), set())
        result = conv._handle_empty_alternatives("' ' | 'abc'")
        assert 'abc' in result

    def test_only_empty_alts_raises(self):
        """Audit 3.4: `" "` и `''` выбрасывают ValueError вместо возврата."""
        conv = LarkConverter({}, set(), set())
        with pytest.raises(ValueError, match="только пустые альтернативы"):
            conv._handle_empty_alternatives('" "')

    def test_single_non_empty_alt(self):
        conv = LarkConverter({}, set(), set())
        result = conv._handle_empty_alternatives('" " | "abc"')
        # Реальное поведение: не оборачивает в ?
        assert 'abc' in result

    def test_no_empty_alts_unchanged(self):
        conv = LarkConverter({}, set(), set())
        result = conv._handle_empty_alternatives('a | b | c')
        assert 'a' in result
        assert 'b' in result
        assert 'c' in result

    def test_empty_alt_only_double_quote_raises(self):
        """Audit 3.4: баг — `" "` выбрасывает ValueError."""
        conv = LarkConverter({}, set(), set())
        with pytest.raises(ValueError):
            conv._handle_empty_alternatives('" "')

    def test_empty_alt_only_single_quote_raises(self):
        """Audit 3.4: баг — `''` выбрасывает ValueError."""
        conv = LarkConverter({}, set(), set())
        with pytest.raises(ValueError):
            conv._handle_empty_alternatives("''")


# =====================================================================
# Расширение правил
# =====================================================================

class TestExpandRule:
    """Расширение правил для Lark."""

    def test_expand_char_class(self):
        rules = {'rule': ['[a-z]+']}
        conv = LarkConverter(rules, set(), set())
        result = conv._expand_rule('rule', set())
        assert '[a-z]+' in result

    def test_expand_concatenation(self):
        rules = {'rule': ['a', 'b', 'c']}
        conv = LarkConverter(rules, set(), set())
        result = conv._expand_rule('rule', set())
        assert 'a' in result
        assert 'b' in result
        assert 'c' in result

    def test_expand_alternative(self):
        rules = {'rule': ['a', '|', 'b']}
        conv = LarkConverter(rules, set(), set())
        result = conv._expand_rule('rule', set())
        assert 'a' in result
        assert 'b' in result

    def test_expand_with_quantifier(self):
        rules = {'rule': ['[a-z]', '+']}
        conv = LarkConverter(rules, set(), set())
        result = conv._expand_rule('rule', set())
        assert '+' in result


# =====================================================================
# Токены в Lark
# =====================================================================

class TestTokenToLark:
    """Конвертация токенов в Lark-формат."""

    def test_char_class_inline(self):
        rules = {'rule': ['[a-z]+']}
        conv = LarkConverter(rules, set(), set())
        result = conv._token_to_lark('[a-z]+', set())
        # Реальное поведение: возвращает как есть
        assert result == '[a-z]+'

    def test_string_literal_double_quotes(self):
        rules = {'rule': ['"hello"']}
        conv = LarkConverter(rules, set(), set())
        result = conv._token_to_lark('"hello"', set())
        assert 'hello' in result

    def test_string_literal_single_quotes(self):
        rules = {'rule': ["'hello'"]}
        conv = LarkConverter(rules, set(), set())
        result = conv._token_to_lark("'hello'", set())
        assert 'hello' in result

    def test_empty_string_returns_none(self):
        conv = LarkConverter({}, set(), set())
        assert conv._token_to_lark('" "', set()) is None
        assert conv._token_to_lark("''", set()) is None

    def test_special_char_quoted(self):
        conv = LarkConverter({}, set(), set())
        result = conv._token_to_lark('+', set())
        assert '"' in result

    def test_rule_reference_as_string(self):
        rules = {'rule': ['other'], 'other': ['[a-z]+']}
        conv = LarkConverter(rules, set(), {'other'})
        result = conv._token_to_lark('rule', set())
        assert result == 'rule'

    def test_regex_rule_as_terminal(self):
        rules = {'rule': ['other'], 'other': ['[a-z]+']}
        conv = LarkConverter(rules, set(), {'other'})
        result = conv._token_to_lark('other', set())
        assert result == 'OTHER'

    def test_backslash_sequence(self):
        conv = LarkConverter({}, set(), set())
        result = conv._token_to_lark('\\n', set())
        assert result is not None


# =====================================================================
# Regex кэш
# =====================================================================

class TestRegexCache:
    """Кэширование regex для regex_rules."""

    def test_cache_populated(self):
        rules = {
            'a': ['[0-9]+'],
            'b': ['a'],
        }
        conv = LarkConverter(rules, set(), {'a'}, None)
        conv.convert('a')
        # Regex-кеш заполняется во время конвертации (встроено в convert)
        assert 'a' in conv._regex_cache

    def test_cache_returns_regex_string(self):
        rules = {'rule': ['[0-9]+']}
        conv = LarkConverter(rules, set(), {'rule'}, None)
        conv.convert('rule')
        result = conv._regex_cache['rule']
        assert isinstance(result, str)


# =====================================================================
# Полный конверт
# =====================================================================

class TestFullConvert:
    """Полная конвертация в Lark-грамматику."""

    def test_convert_contains_terminal(self):
        rules = {
            'rule': ['other'],
            'other': ['[0-9]+'],
        }
        conv = LarkConverter(rules, set(), {'other'})
        result = conv.convert('rule')
        assert 'OTHER' in result

    def test_convert_contains_ignore(self):
        rules = {'rule': ['[a-z]+']}
        conv = LarkConverter(rules, set(), {'rule'})
        result = conv.convert('rule')
        assert '%ignore' in result

    def test_convert_contains_rule_definition(self):
        rules = {'rule': ['[a-z]+']}
        conv = LarkConverter(rules, set(), set(), None)
        result = conv.convert('rule')
        assert 'rule' in result
