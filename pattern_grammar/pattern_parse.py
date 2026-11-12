"""
Парсинг текста в AST (parse) для Pattern.

ParseEngine парсит текст через Lark (рекурсивные правила) или regex
(нерекурсивные правила) и возвращает дерево разбора.
"""
from typing import Dict, Optional

import re
from lark import Tree, Token

from .unicode import _require_regex

from .errors import PatternError
from .constants import METHOD_MATCH, REGEX_UNICODE_OPEN, REGEX_PATTERN_ATTR, RULE_NAME_TYPE_ERROR, TEXT_TYPE_ERROR, RULE_PREFIX, RULE_NOT_FOUND, RULE_NOT_COMPILED, PARSER_PREFIX, RULE_NOT_CREATED


class ParseEngine:
    """Движок парсинга текста в дерево."""

    def __init__(
        self,
        regex_engines: Dict[str, Dict[str, object]],
        parser_engines: Dict[str, object],
        regex_rules: set,
        recursive_rules: set,
    ):
        self.regex_engines = regex_engines
        self.parser_engines = parser_engines
        self.regex_rules = regex_rules
        self.recursive_rules = recursive_rules

    def parse(
        self, rule_name: str, text: str, *, ignore_case: bool = False
    ) -> Optional[object]:
        """Парсит текст и возвращает дерево разбора (AST)."""
        if not isinstance(rule_name, str):
            raise TypeError(RULE_NAME_TYPE_ERROR)
        if not isinstance(text, str):
            raise TypeError(TEXT_TYPE_ERROR)
        return self._do_parse(rule_name, text, ignore_case=ignore_case)

    def _do_parse(
        self, rule_name: str, text: str, ignore_case: bool = False
    ) -> Optional[object]:
        """Распределяет парсинг между Lark- и regex-движками."""
        if rule_name in self.recursive_rules:
            return self._parse_recursive(rule_name, text, ignore_case=ignore_case)

        if rule_name in self.regex_rules:
            return self._parse_regex(rule_name, text, ignore_case=ignore_case)

        raise PatternError(f"{RULE_PREFIX}'{rule_name}'{RULE_NOT_FOUND}")

    def _parse_recursive(
        self, rule_name: str, text: str, ignore_case: bool = False
    ) -> Optional[object]:
        """Парсит рекурсивное правило через Lark."""
        parser = self.parser_engines.get(rule_name)
        if not parser:
            raise PatternError(f"{PARSER_PREFIX}'{rule_name}'{RULE_NOT_CREATED}")

        try:
            if ignore_case:
                return parser.parse(text.lower())
            return parser.parse(text)
        except Exception as e:
            raise PatternError(f"Ошибка парсинга: {e}")

    def _parse_regex(
        self, rule_name: str, text: str, ignore_case: bool = False
    ) -> Optional[object]:
        """Парсит regex-правило через regex движок."""
        engines = self.regex_engines.get(rule_name)
        if not engines:
            raise PatternError(f"{RULE_PREFIX}'{rule_name}'{RULE_NOT_COMPILED}")

        compiled = engines[METHOD_MATCH]
        flags = re.IGNORECASE if ignore_case else 0
        uses_unicode_class = (hasattr(compiled, REGEX_PATTERN_ATTR) and REGEX_UNICODE_OPEN in compiled.pattern)
        if uses_unicode_class:
            regex_mod = _require_regex()
            match_result = regex_mod.match(compiled.pattern, text, flags)
        else:
            match_result = re.match(compiled.pattern, text, flags)
        if match_result:
            return Tree('match', [Token('VALUE', text)])
        return None
