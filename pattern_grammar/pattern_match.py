"""
Проверка соответствия тексту (match/findall) для Pattern.

MatchEngine проверяет текст через regex- или Lark-движки и бросает
@fail ошибки через FailChecker.
"""
import re
from typing import Dict

from .errors import PatternError
from .unicode import _require_regex
from .constants import METHOD_MATCH, METHOD_FINDALL, REGEX_UNICODE_OPEN, REGEX_PATTERN_ATTR, RULE_NAME_TYPE_ERROR, TEXT_TYPE_ERROR, RULE_PREFIX, RULE_NOT_FOUND, RULE_NOT_COMPILED, PARSER_PREFIX, RULE_NOT_CREATED


class MatchEngine:
    """Движок проверки соответствия тексту."""

    def __init__(
        self,
        regex_engines: Dict[str, Dict[str, object]],
        parser_engines: Dict[str, object],
        regex_rules: set,
        recursive_rules: set,
        fail_checker,
    ):
        self.regex_engines = regex_engines
        self.parser_engines = parser_engines
        self.regex_rules = regex_rules
        self.recursive_rules = recursive_rules
        self._fail_checker = fail_checker

    def match(self, rule_name: str, text: str, *, ignore_case: bool = False) -> bool:
        """Проверяет, соответствует ли текст правилу."""
        if not isinstance(rule_name, str):
            raise TypeError(RULE_NAME_TYPE_ERROR)
        if not isinstance(text, str):
            raise TypeError(TEXT_TYPE_ERROR)
        return self._do_match(rule_name, text, ignore_case=ignore_case)

    def findall(self, rule_name: str, text: str, *, ignore_case: bool = False) -> list:
        """Находит все совпадения правила в тексте (только regex-правила)."""
        if not isinstance(rule_name, str):
            raise TypeError(RULE_NAME_TYPE_ERROR)
        if not isinstance(text, str):
            raise TypeError(TEXT_TYPE_ERROR)

        is_regex_rule = rule_name in self.regex_rules
        if not is_regex_rule:
            raise PatternError("Метод findall доступен только для нерекурсивных правил")

        engines = self.regex_engines.get(rule_name)
        if not engines:
            raise PatternError(f"{RULE_PREFIX}'{rule_name}'{RULE_NOT_COMPILED}")

        compiled = engines[METHOD_FINDALL]
        flags = re.IGNORECASE if ignore_case else 0
        uses_unicode_class = (hasattr(compiled, REGEX_PATTERN_ATTR) and REGEX_UNICODE_OPEN in compiled.pattern)
        if uses_unicode_class:
            regex_mod = _require_regex()
            return regex_mod.findall(compiled.pattern, text, flags)
        return re.findall(compiled.pattern, text, flags)

    def _do_match(self, rule_name: str, text: str, ignore_case: bool = False) -> bool:
        """Распределяет проверку между regex- и Lark-движками."""
        if rule_name in self.regex_rules:
            return self._match_regex(rule_name, text, ignore_case=ignore_case)

        if rule_name in self.recursive_rules:
            return self._match_lark(rule_name, text, ignore_case=ignore_case)

        raise PatternError(f"{RULE_PREFIX}'{rule_name}'{RULE_NOT_FOUND}")

    def _match_regex(self, rule_name: str, text: str, ignore_case: bool = False) -> bool:
        """Проверяет через regex движок."""
        engines = self.regex_engines.get(rule_name)
        if not engines:
            raise PatternError(f"{RULE_PREFIX}'{rule_name}'{RULE_NOT_COMPILED}")

        compiled = engines[METHOD_MATCH]
        flags = re.IGNORECASE if ignore_case else 0
        uses_unicode_class = (hasattr(compiled, REGEX_PATTERN_ATTR) and REGEX_UNICODE_OPEN in compiled.pattern)
        if uses_unicode_class:
            regex_mod = _require_regex()
            matched = regex_mod.match(compiled.pattern, text, flags) is not None
        else:
            matched = re.match(compiled.pattern, text, flags) is not None
        if not matched:
            self._fail_checker.raise_if_fail(rule_name, text, compiled)
        return matched

    def _match_lark(self, rule_name: str, text: str, ignore_case: bool = False) -> bool:
        """Проверяет через Lark парсер."""
        parser = self.parser_engines.get(rule_name)
        if not parser:
            raise PatternError(f"{PARSER_PREFIX}'{rule_name}'{RULE_NOT_CREATED}")

        try:
            if ignore_case:
                parser.parse(text.lower())
            else:
                parser.parse(text)
            return True
        except Exception:
            self._fail_checker.raise_if_fail(rule_name, text, None)
            return False
