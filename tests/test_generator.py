"""
Unit-тесты для GrammarGenerator.

Реальное поведение генератора:
- generate(rule_name, count=1) возвращает список сгенерированных строк
- Для regex-правил генерирует строки по токенам
- Для recursive-правил ограничивает глубину рекурсии
- Поддерживает квантификаторы *, +, ?, {n}, {n,m}
- Поддерживает группировку (...)
- Строковые литералы копируются как есть
- Символьные классы [abc] генерируют случайные символы из класса
"""
import pytest
from pattern_grammar import Pattern


# =====================================================================
# Базовая генерация
# =====================================================================

class TestGenerateBasic:
    """Базовая генерация строк."""

    def test_generate_single(self):
        grammar = 'rule ::= [a-z]+'
        p = Pattern(grammar)
        result = p.generate('rule')
        assert isinstance(result, list)
        assert len(result) == 1
        assert len(result[0]) > 0

    def test_generate_multiple(self):
        grammar = 'rule ::= [a-z]+'
        p = Pattern(grammar)
        result = p.generate('rule', count=5)
        assert len(result) == 5
        for s in result:
            assert len(s) > 0

    def test_generate_returns_strings(self):
        grammar = 'rule ::= [a-z]+'
        p = Pattern(grammar)
        result = p.generate('rule')
        assert isinstance(result[0], str)

    def test_generate_unknown_rule(self):
        grammar = 'rule ::= [a-z]+'
        p = Pattern(grammar)
        result = p.generate('nonexistent')
        assert result == ['']


# =====================================================================
# Генерация символьных классов
# =====================================================================

class TestGenerateCharClass:
    """Генерация символьных классов."""

    def test_generate_range(self):
        grammar = 'rule ::= [0-9]'
        p = Pattern(grammar)
        result = p.generate('rule')
        assert result[0].isdigit()

    def test_generate_set(self):
        grammar = 'rule ::= [abc]'
        p = Pattern(grammar)
        result = p.generate('rule')
        assert result[0] in ('a', 'b', 'c')

    def test_generate_alphanumeric(self):
        grammar = 'rule ::= [a-zA-Z0-9]'
        p = Pattern(grammar)
        result = p.generate('rule')
        assert result[0].isalnum()


# =====================================================================
# Генерация строковых литералов
# =====================================================================

class TestGenerateLiterals:
    """Генерация строковых литералов."""

    def test_generate_double_quote(self):
        grammar = 'rule ::= "hello"'
        p = Pattern(grammar)
        result = p.generate('rule')
        assert result[0] == 'hello'

    def test_generate_single_quote(self):
        grammar = "rule ::= 'world'"
        p = Pattern(grammar)
        result = p.generate('rule')
        assert result[0] == 'world'

    def test_generate_literal_with_spaces(self):
        grammar = 'rule ::= "hello world"'
        p = Pattern(grammar)
        result = p.generate('rule')
        assert result[0] == 'hello world'


# =====================================================================
# Генерация квантификаторов
# =====================================================================

class TestGenerateQuantifiers:
    """Генерация квантификаторов."""

    def test_generate_plus(self):
        grammar = 'rule ::= [0-9]+'
        p = Pattern(grammar)
        result = p.generate('rule')
        assert len(result[0]) > 0
        assert result[0].isdigit()

    def test_generate_star(self):
        grammar = 'rule ::= [0-9]*'
        p = Pattern(grammar)
        result = p.generate('rule', count=10)
        # * может дать пустую строку или строку из цифр
        for s in result:
            assert s == '' or all(c.isdigit() for c in s)

    def test_generate_question(self):
        grammar = 'rule ::= [0-9]?'
        p = Pattern(grammar)
        result = p.generate('rule', count=10)
        # ? может дать пустую строку или одну цифру
        for s in result:
            assert s == '' or (len(s) == 1 and s.isdigit())

    def test_generate_braced_single(self):
        grammar = 'rule ::= [0-9]{3}'
        p = Pattern(grammar)
        result = p.generate('rule')
        assert len(result[0]) == 3
        assert result[0].isdigit()

    def test_generate_braced_range(self):
        grammar = 'rule ::= [a-z]{2,4}'
        p = Pattern(grammar)
        result = p.generate('rule')
        assert 2 <= len(result[0]) <= 4
        assert result[0].isalpha()


# =====================================================================
# Генерация составных правил
# =====================================================================

class TestGenerateCompound:
    """Генерация составных правил."""

    def test_generate_sequence(self):
        grammar = 'rule ::= [a-z] [0-9]'
        p = Pattern(grammar)
        result = p.generate('rule')
        assert len(result[0]) == 2
        assert result[0][0].isalpha()
        assert result[0][1].isdigit()

    def test_generate_with_literal(self):
        grammar = 'rule ::= [a-z] "x" [0-9]'
        p = Pattern(grammar)
        result = p.generate('rule')
        assert result[0][1:] == 'x' or 'x' in result[0]

    def test_generate_multiple_rules(self):
        grammar = '''
rule1 ::= [a-z]+
rule2 ::= [0-9]+
'''
        p = Pattern(grammar)
        r1 = p.generate('rule1')
        r2 = p.generate('rule2')
        assert r1[0].isalpha()
        assert r2[0].isdigit()


# =====================================================================
# Генерация рекурсивных правил
# =====================================================================

class TestGenerateRecursive:
    """Генерация рекурсивных правил."""

    def test_generate_recursive_list(self):
        grammar = '''
list ::= item ("," item)*
item ::= [a-z]+
'''
        p = Pattern(grammar)
        result = p.generate('list')
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_generate_recursive_with_limit(self):
        grammar = '''
list ::= item ("," item)*
item ::= [a-z]+
'''
        p = Pattern(grammar)
        result = p.generate('list', max_depth=5)
        assert isinstance(result, list)


# =====================================================================
# Валидация входных данных
# =====================================================================

class TestGenerateValidation:
    """Валидация входных данных генератора."""

    def test_generate_non_string_rule(self):
        grammar = 'rule ::= [a-z]+'
        p = Pattern(grammar)
        with pytest.raises(TypeError, match="rule_name должен быть строкой"):
            p.generate(123)

    def test_generate_invalid_count(self):
        grammar = 'rule ::= [a-z]+'
        p = Pattern(grammar)
        with pytest.raises(ValueError, match="count должен быть положительным"):
            p.generate('rule', count=0)

    def test_generate_negative_count(self):
        grammar = 'rule ::= [a-z]+'
        p = Pattern(grammar)
        with pytest.raises(ValueError, match="count должен быть положительным"):
            p.generate('rule', count=-1)
