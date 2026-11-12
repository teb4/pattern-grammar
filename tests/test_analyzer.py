"""
Unit-тесты для RecursionAnalyzer.
"""
import pytest
from pattern_grammar.analyzer import RecursionAnalyzer


# =====================================================================
# Простые правила без рекурсии
# =====================================================================

class TestNonRecursive:
    """Анализатор не находит рекурсии в простых правилах."""

    def test_no_recursion_simple(self, simple_rules):
        analyzer = RecursionAnalyzer(simple_rules)
        recursive = analyzer.find_recursive_rules()
        assert recursive == set()

    def test_no_recursion_single_rule(self):
        rules = {
            'rule': ['[a-z]+'],
        }
        analyzer = RecursionAnalyzer(rules)
        assert analyzer.find_recursive_rules() == set()

    def test_no_recursion_chained(self):
        rules = {
            'a': ['b'],
            'b': ['[0-9]+'],
        }
        analyzer = RecursionAnalyzer(rules)
        assert analyzer.find_recursive_rules() == set()


# =====================================================================
# Прямая рекурсия
# =====================================================================

class TestDirectRecursion:
    """Обнаружение прямой рекурсии."""

    def test_direct_recursion_list(self, recursive_rules):
        analyzer = RecursionAnalyzer(recursive_rules)
        recursive = analyzer.find_recursive_rules()
        assert 'list' in recursive


# =====================================================================
# Косвенная рекурсия
# =====================================================================

class TestIndirectRecursion:
    """Обнаружение косвенной рекурсии (A → B → A)."""

    def test_indirect_recursion_a_b(self):
        rules = {
            'a': ['b'],
            'b': ['a'],
        }
        analyzer = RecursionAnalyzer(rules)
        recursive = analyzer.find_recursive_rules()
        assert 'a' in recursive
        assert 'b' in recursive

    def test_indirect_recursion_chain(self):
        rules = {
            'a': ['b'],
            'b': ['c'],
            'c': ['a'],
        }
        analyzer = RecursionAnalyzer(rules)
        recursive = analyzer.find_recursive_rules()
        assert 'a' in recursive
        assert 'b' in recursive
        assert 'c' in recursive

    def test_indirect_depends_on_recursive(self):
        """Правило, зависящее от рекурсивного, тоже считается рекурсивным."""
        rules = {
            'list': ['item', '|', 'list', ',', 'item'],
            'item': ['[a-z]+'],
            'expr': ['list'],
        }
        analyzer = RecursionAnalyzer(rules)
        recursive = analyzer.find_recursive_rules()
        assert 'list' in recursive
        assert 'expr' in recursive


# =====================================================================
# Глубокие цепочки
# =====================================================================

class TestDeepChains:
    """Глубокие цепочки зависимостей."""

    def test_deep_chain_no_recursion(self):
        rules = {
            f'rule{i}': [f'rule{i+1}']
            for i in range(10)
        }
        rules['rule9'] = ['[a-z]+']
        analyzer = RecursionAnalyzer(rules)
        assert analyzer.find_recursive_rules() == set()

    def test_deep_chain_with_cycle(self):
        rules = {
            f'rule{i}': [f'rule{i+1}']
            for i in range(5)
        }
        rules['rule4'] = ['rule0']
        analyzer = RecursionAnalyzer(rules)
        recursive = analyzer.find_recursive_rules()
        assert len(recursive) == 5


# =====================================================================
# Методы класса
# =====================================================================

class TestHelperMethods:
    """Вспомогательные методы RecursionAnalyzer."""

    def test_has_non_terminal_true(self, simple_rules):
        rules = {
            'a': ['b'],
            'b': ['[0-9]+'],
        }
        analyzer = RecursionAnalyzer(rules)
        assert analyzer._has_non_terminal('a') is True

    def test_has_non_terminal_false(self, simple_rules):
        analyzer = RecursionAnalyzer(simple_rules)
        assert analyzer._has_non_terminal('tld') is False

    def test_has_non_terminal_empty(self):
        analyzer = RecursionAnalyzer({})
        assert analyzer._has_non_terminal('missing') is False

    def test_has_recursion_simple(self):
        rules = {
            'list': ['item', '|', 'list', ',', 'item'],
            'item': ['[a-z]+'],
        }
        analyzer = RecursionAnalyzer(rules)
        assert analyzer._has_recursion('list', [], 0) is True

    def test_has_recursion_no_cycle(self):
        rules = {
            'a': ['b'],
            'b': ['[0-9]+'],
        }
        analyzer = RecursionAnalyzer(rules)
        assert analyzer._has_recursion('a', [], 0) is False

    def test_depends_on_recursive_true(self):
        rules = {
            'list': ['item', '|', 'list', ',', 'item'],
            'item': ['[a-z]+'],
            'expr': ['list'],
        }
        analyzer = RecursionAnalyzer(rules)
        recursive_set = {'list'}
        assert analyzer._depends_on_recursive('expr', recursive_set, set()) is True

    def test_depends_on_recursive_false(self):
        rules = {
            'a': ['b'],
            'b': ['[0-9]+'],
        }
        analyzer = RecursionAnalyzer(rules)
        recursive_set = set()
        assert analyzer._depends_on_recursive('a', recursive_set, set()) is False
