"""
Unit-тесты для покрытия непокрытых веток RecursionAnalyzer.

Цель — достичь 100% покрытия analyzer.py.
Непокрытые строки: 29, 43
"""
from pattern_grammar.analyzer import RecursionAnalyzer


# =====================================================================
# find_recursive_rules: косвенная рекурсия с has_non_terminal=False (строка 29)
# =====================================================================

class TestIndirectRecursionNonTerminal:
    """Покрытие ветки строка 29 — _has_non_terminal возвращает False."""

    def test_no_indirect_recursion_when_no_non_terminal(self):
        """Правило без non-terminal не добавляется в indirect_recursive."""
        rules = {
            'a': ['b'],
            'b': ['[0-9]+'],
        }
        analyzer = RecursionAnalyzer(rules)
        recursive = analyzer.find_recursive_rules()
        # 'a' зависит от 'b', но 'b' не рекурсивное → 'a' не добавляется
        assert 'a' not in recursive
        assert 'b' not in recursive

    def test_indirect_with_non_terminal_true(self):
        """Правило с non-terminal, зависящее от рекурсивного."""
        rules = {
            'list': ['item', '|', 'list', ',', 'item'],
            'item': ['[a-z]+'],
            'expr': ['list'],
        }
        analyzer = RecursionAnalyzer(rules)
        recursive = analyzer.find_recursive_rules()
        assert 'expr' in recursive


# =====================================================================
# _has_recursion: глубина > MAX_RECURSION_DEPTH (строка 43)
# =====================================================================

class TestMaxRecursionDepth:
    """Покрытие ветки ограничения глубины (строка 43)."""

    def test_deep_chain_exceeds_max_depth(self):
        """Цепочка глубже MAX_RECURSION_DEPTH → возвращает False.

        MAX_RECURSION_DEPTH = 100, условие depth > 100.
        Нужно 102 правила, чтобы глубина достигла 101.
        """
        rules = {
            f'rule{i}': [f'rule{i+1}']
            for i in range(102)
        }
        rules['rule101'] = ['[a-z]+']
        analyzer = RecursionAnalyzer(rules)
        result = analyzer._has_recursion('rule0', [], 0)
        assert result is False

    def test_deep_chain_no_cycle_within_depth(self):
        """Цепочка без цикла, но длинная → False."""
        rules = {
            f'rule{i}': [f'rule{i+1}']
            for i in range(50)
        }
        rules['rule49'] = ['[a-z]+']
        analyzer = RecursionAnalyzer(rules)
        result = analyzer._has_recursion('rule0', [], 0)
        assert result is False

    def test_deep_chain_with_cycle_at_end(self):
        """Цикл в конце длинной цепочки → True (до достижения MAX_DEPTH)."""
        rules = {
            f'rule{i}': [f'rule{i+1}']
            for i in range(10)
        }
        rules['rule9'] = ['rule0']
        analyzer = RecursionAnalyzer(rules)
        result = analyzer._has_recursion('rule0', [], 0)
        assert result is True
