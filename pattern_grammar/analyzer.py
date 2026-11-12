"""
Анализатор рекурсии в грамматике
"""

from typing import Dict, List, Set

from .constants import MAX_RECURSION_DEPTH


class RecursionAnalyzer:
    """Анализатор рекурсии в грамматике"""

    def __init__(self, rules: Dict[str, List[str]]):
        self.rules = rules

    def find_recursive_rules(self) -> Set[str]:
        """Находит все рекурсивные правила"""
        recursive: Set[str] = set()

        for rule in self.rules:
            has_recursion = (self._has_non_terminal(rule) and self._has_recursion(rule, [], 0))
            if has_recursion:
                recursive.add(rule)

        indirect_recursive: Set[str] = set()
        for rule in self.rules:
            if rule in recursive:
                continue
            depends_on_recursive = (self._has_non_terminal(rule) and self._depends_on_recursive(rule, recursive, set()))
            if depends_on_recursive:
                indirect_recursive.add(rule)

        return recursive | indirect_recursive

    def _has_non_terminal(self, rule: str) -> bool:
        """Проверяет, есть ли в правиле ссылки на другие правила"""
        for token in self.rules.get(rule, []):
            if token in self.rules:
                return True
        return False

    def _has_recursion(self, rule: str, path: List[str], depth: int) -> bool:
        """Проверяет рекурсию с ограничением глубины"""
        if depth > MAX_RECURSION_DEPTH:
            return False

        if rule in path:
            return True

        new_path = path + [rule]

        for token in self.rules.get(rule, []):
            if token in self.rules:
                if self._has_recursion(token, new_path, depth + 1):
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
