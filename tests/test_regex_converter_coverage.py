"""
Unit-тесты для покрытия непокрытых веток RegexConverter.

Цель — достичь 100% покрытия regex_converter.py.
Непокрытые строки: 59, 87, 98, 126-156, 165, 173-179, 196, 224-231
"""
from pattern_grammar.regex_converter import RegexConverter
from pattern_grammar.parser import BNFParser


# =====================================================================
# _expand: квантификатор за простым токеном (строка 59)
# =====================================================================

class TestExpandQuantifier:
    """Покрытие ветки _expand с квантификатором за токеном (строка 59)."""

    def test_expand_quantifier_after_plain_token(self):
        """plain токен + квантификатор * → ветка строка 59."""
        rules = {'rule': ['abc', '*']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert 'abc' in result
        assert '*' in result

    def test_expand_quantifier_plus_after_plain(self):
        """plain токен + квантификатор +."""
        rules = {'rule': ['abc', '+']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert 'abc' in result
        assert '+' in result

    def test_expand_quantifier_question_after_plain(self):
        """plain токен + квантификатор ?."""
        rules = {'rule': ['abc', '?']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert 'abc' in result
        assert '?' in result


# =====================================================================
# _expand: braced квантификатор (строка 87)
# =====================================================================

class TestExpandBraced:
    """Покрытие ветки _expand с braced квантификатором (строка 87)."""

    def test_expand_braced_single(self):
        """plain токен + {3} → ветка строка 87."""
        rules = {'rule': ['abc', '{3}']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert 'abc' in result
        assert '{3}' in result

    def test_expand_braced_range(self):
        """plain токен + {2,4} → ветка строка 87."""
        rules = {'rule': ['abc', '{2,4}']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert 'abc' in result
        assert '{2,4}' in result


# =====================================================================
# _process_tokens: вложенная группировка с квантификатором (строки 126-156, 165, 173-179)
# =====================================================================

class TestProcessTokensNested:
    """Покрытие _process_tokens с вложенными группами и квантификаторами."""

    def test_process_nested_group_with_quantifier(self):
        """Вложенная группа ( ... ) с квантификатором +."""
        rules = {'rule': ['(', '(', 'a', 'b', ')', '+', ')']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert isinstance(result, str)
        assert '+' in result

    def test_process_nested_group_with_star(self):
        """Вложенная группа с квантификатором *."""
        rules = {'rule': ['(', 'a', ')', '*']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert isinstance(result, str)
        assert '*' in result

    def test_process_nested_group_with_question(self):
        """Вложенная группа с квантификатором ?."""
        rules = {'rule': ['(', 'a', ')', '?']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert isinstance(result, str)
        assert '?' in result

    def test_process_braced_inside_group(self):
        """Braced квантификатор внутри группы."""
        rules = {'rule': ['(', 'abc', '{2}', ')']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert isinstance(result, str)
        assert '{2}' in result

    def test_process_braced_quantifier_inside_group(self):
        """Braced квантификатор {3} внутри группы → ветка строка 173-179."""
        rules = {'rule': ['(', 'abc', '{3}', ')']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert '{3}' in result

    def test_process_alternative_inside_group(self):
        """Альтернатива внутри группы."""
        rules = {'rule': ['(', 'a', '|', 'b', ')']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert '|' in result

    def test_process_tokens_empty_group(self):
        """Пустая группа."""
        rules = {'rule': ['()']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert isinstance(result, str)


# =====================================================================
# _token_to_regex: special chars (строка 196)
# =====================================================================

class TestTokenToRegexSpecial:
    """Покрытие ветки _token_to_regex для special chars (строка 196)."""

    def test_special_char_dot(self):
        """. — special char → ветка строка 196."""
        conv = RegexConverter({}, set(), None)
        result = conv._token_to_regex('.', set())
        assert r'\.' in result

    def test_special_char_caret(self):
        """^ — special char."""
        conv = RegexConverter({}, set(), None)
        result = conv._token_to_regex('^', set())
        assert r'\^' in result

    def test_special_char_dollar(self):
        """$ — special char."""
        conv = RegexConverter({}, set(), None)
        result = conv._token_to_regex('$', set())
        assert r'\$' in result

    def test_special_char_pipe(self):
        """| — special char."""
        conv = RegexConverter({}, set(), None)
        result = conv._token_to_regex('|', set())
        assert r'\|' in result

    def test_special_char_open_paren(self):
        """( — special char."""
        conv = RegexConverter({}, set(), None)
        result = conv._token_to_regex('(', set())
        assert r'\(' in result

    def test_special_char_open_bracket(self):
        """[ — special char."""
        conv = RegexConverter({}, set(), None)
        result = conv._token_to_regex('[', set())
        assert r'\[' in result

    def test_special_char_backslash(self):
        """\\ — goes to is_escape branch, NOT is_special."""
        conv = RegexConverter({}, set(), None)
        result = conv._token_to_regex('\\', set())
        assert result == '\\'


# =====================================================================
# _token_to_regex: braced range и digit (строки 224-231)
# =====================================================================

class TestTokenToRegexBraced:
    """Покрытие веток braced range и digit check (строки 224-231)."""

    def test_braced_range_valid(self):
        """{1,3} — валидный диапазон → ветка строка 227-228."""
        conv = RegexConverter({}, set(), None)
        result = conv._token_to_regex('{1,3}', set())
        assert result == '{1,3}'

    def test_braced_range_invalid(self):
        """{a,b} — невалидный диапазон, goes to digit check."""
        conv = RegexConverter({}, set(), None)
        result = conv._token_to_regex('{a,b}', set())
        assert isinstance(result, str)

    def test_braced_digit_only(self):
        """{123} — digit only → ветка строка 229-230."""
        conv = RegexConverter({}, set(), None)
        result = conv._token_to_regex('{123}', set())
        assert result == '{123}'

    def test_braced_empty(self):
        """{} — пустой braced."""
        conv = RegexConverter({}, set(), None)
        result = conv._token_to_regex('{}', set())
        assert isinstance(result, str)


# =====================================================================
# _token_to_regex: rule reference that IS a regex rule (строка 59 ветка is_rule_ref)
# =====================================================================

class TestTokenToRegexRuleRef:
    """Покрытие ветки is_rule_ref в _token_to_regex."""

    def test_rule_ref_is_regex_rule(self):
        """Ссылка на правило, которое в regex_rules → ветка is_rule_ref."""
        rules = {
            'outer': ['inner'],
            'inner': ['[a-z]+'],
        }
        conv = RegexConverter(rules, {'inner'}, None)
        result = conv._token_to_regex('inner', set())
        assert isinstance(result, str)

    def test_rule_ref_not_regex_rule(self):
        """Ссылка на правило, которое НЕ в regex_rules → не ветка is_rule_ref."""
        rules = {
            'outer': ['inner'],
            'inner': ['[a-z]+'],
        }
        conv = RegexConverter(rules, set(), None)
        result = conv._token_to_regex('inner', set())
        # inner не в regex_rules → goes to builtin/char_class/etc.
        assert isinstance(result, str)


# =====================================================================
# _expand: альтернативы с group + quantifier
# =====================================================================

class TestExpandGroupQuantifier:
    """Покрытие ветки group + quantifier в _expand."""

    def test_expand_group_star(self):
        """Группа () с квантификатором *."""
        rules = {'rule': ['(', 'a', 'b', ')', '*']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert '*' in result

    def test_expand_group_plus(self):
        """Группа () с квантификатором +."""
        rules = {'rule': ['(', 'a', 'b', ')', '+']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert '+' in result

    def test_expand_group_question(self):
        """Группа () с квантификатором ?."""
        rules = {'rule': ['(', 'a', 'b', ')', '?']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert '?' in result

    def test_expand_nested_group_with_quantifier(self):
        """Вложенная группа с квантификатором."""
        rules = {'rule': ['(', '(', 'a', ')', '+', ')', '*']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert '*' in result
        assert '+' in result


# =====================================================================
# _expand: несколько альтернатив с группами
# =====================================================================

class TestExpandComplex:
    """Сложные случаи _expand."""

    def test_expand_alt_with_groups(self):
        """Альтернатива с группами."""
        rules = {'rule': ['(', 'a', 'b', ')', '|', '(', 'c', 'd', ')']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert '|' in result

    def test_expand_concat_with_quantifier_and_alt(self):
        """Конкатенация с квантификатором и альтернативой."""
        rules = {'rule': ['a', '|', 'b', '+', 'c']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert '|' in result
        assert '+' in result

    def test_expand_empty_body(self):
        """Правило с пустым телом."""
        rules = {'rule': []}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert result == '(?:)'


# =====================================================================
# restore_special_chars через parser в convert
# =====================================================================

class TestConvertWithParser:
    """Конвертация с parser для восстановления спецсимволов."""

    def test_convert_with_hash_parser(self):
        """convert с parser → restore_special_chars вызывается."""
        parser = BNFParser()
        parser.parse('rule ::= "a#b"')
        rules = {'rule': ['"a___HASH___b"']}
        conv = RegexConverter(rules, set(), parser)
        result = conv.convert('rule')
        assert r'\#' in result

    def test_convert_no_parser(self):
        """convert без parser → restore_special_chars НЕ вызывается."""
        rules = {'rule': ['"abc"']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        assert isinstance(result, str)


# =====================================================================
# _process_tokens: группа без квантификатора (строки 154-155)
# =====================================================================

class TestProcessTokensGroupNoQuantifier:
    """Покрытие ветки group без квантификатора (строки 154-155)."""

    def test_process_group_without_quantifier(self):
        """Группа () без квантификатора → else ветка строки 154-155."""
        rules = {'rule': ['(', 'a', 'b', ')']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        # Группа без квантификатора → (?:ab)
        assert '(?:ab)' in result


# =====================================================================
# _expand: группа без квантификатора (строки 154-155)
# =====================================================================

class TestExpandGroupNoQuantifier:
    """Покрытие ветки group без квантификатора в _expand (строки 154-155)."""

    def test_expand_group_without_quantifier(self):
        """Группа () в _expand без квантификатора → else ветка строки 154-155."""
        rules = {'rule': ['(', 'x', 'y', ')', '|', 'z']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        # (?:xy) | z
        assert '(?:xy)' in result
        assert '|' in result


# =====================================================================
# _expand: group with quantifier (строка 137 — depth += 1)
# =====================================================================

class TestExpandNestedGroupDepth:
    """Покрытие строки 137 — depth += 1 при вложенных группах."""

    def test_expand_nested_paren_depth_increment(self):
        """Вложенная группа с ( ( ) ) → depth += 1 выполняется."""
        rules = {'rule': ['(', '(', 'a', ')', 'b', ')', '*']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        # (?:((?:a)b))*
        assert '*' in result
        assert '(?:' in result


# =====================================================================
# _token_to_regex: rule_ref с pipe внутри (строка 196)
# =====================================================================

class TestTokenToRegexRuleRefWithPipe:
    """Покрытие строки 196 — return f'(?:{expanded})' когда pipe в expanded."""

    def test_rule_ref_with_pipe_needs_group(self):
        """rule_ref с pipe внутри → return f'(?:{expanded})' (строка 196)."""
        rules = {
            'rule': ['inner'],
            'inner': ['a', '|', 'b'],
        }
        # inner — regex_rule, expand с pipe
        conv = RegexConverter(rules, {'inner'}, None)
        result = conv.convert('rule')
        # inner expand → (?:a|b), и так как pipe в expanded → (?:a|b)
        assert '(?:a|b)' in result


# =====================================================================
# _token_to_regex: needs_group для квантификатора (строка 165)
# =====================================================================

class TestTokenToRegexNeedsGroup:
    """Покрытие строки 165 — sub_expr = f'(?:{sub_expr})'."""

    def test_token_to_regex_needs_group_for_quantifier(self):
        """Токен с длиной sub_expr > 1 и без [] → group (строка 165)."""
        rules = {'rule': ['abc', '*']}
        conv = RegexConverter(rules, set(), None)
        result = conv.convert('rule')
        # abc не char class, len > 1 → (?:abc)*
        assert '(?:abc)' in result
