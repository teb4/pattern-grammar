"""
Анализатор рекурсии в грамматике
"""

from typing import Dict, List, Set


class RecursionAnalyzer:
    """Анализатор рекурсии в грамматике"""

    def __init__(self, rules: Dict[str, List[str]]):
        self.rules = rules

    def find_recursive_rules(self) -> Set[str]:
        """Находит все рекурсивные правила"""
        recursive = set()

        for rule in self.rules:
            # Проверяем только правила, которые ссылаются на другие правила
            if self._has_non_terminal(rule) and self._has_recursion(rule, []):
                recursive.add(rule)

        # Также находим правила, которые зависят от рекурсивных
        indirect_recursive = set()
        for rule in self.rules:
            if rule in recursive:
                continue
            # Правило должно ссылаться на другие правила, чтобы быть кандидатом
            if self._has_non_terminal(rule) and self._depends_on_recursive(rule, recursive, set()):
                indirect_recursive.add(rule)

        return recursive | indirect_recursive

    def _has_non_terminal(self, rule: str) -> bool:
        """Проверяет, есть ли в правиле ссылки на другие правила"""
        for token in self.rules.get(rule, []):
            if token in self.rules:
                return True
        return False

    def _has_recursion(self, rule: str, path: List[str]) -> bool:
        if rule in path:
            return True

        new_path = path + [rule]  # копия, не мутируем оригинал

        for token in self.rules.get(rule, []):
            if token in self.rules:
                if self._has_recursion(token, new_path):
                    return True

        return False

    def _depends_on_recursive(self, rule: str, recursive_set: Set[str], visited: Set[str]) -> bool:
        """Проверяет, зависит ли правило от рекурсивного"""
        if rule in visited:
            return False
        visited.add(rule)

        if rule in recursive_set:
            return True

        for token in self.rules.get(rule, []):
            if token in self.rules:
                if self._depends_on_recursive(token, recursive_set, visited):
                    return True

        return False
