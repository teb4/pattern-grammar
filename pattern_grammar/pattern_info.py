"""
Отладочная информация и JSON Schema для Pattern.

PatternInfo формирует get_info() (отладочные данные) и
to_json_schema() (JSON Schema для правила).
"""
from typing import Dict

from .errors import PatternError
from .constants import METHOD_MATCH, JSON_KEY_TYPE, JSON_KEY_STRING, KEY_PATTERN, RULE_PREFIX, RULE_NOT_FOUND, RULE_NOT_COMPILED


class PatternInfo:
    """Формирует отладочную информацию и JSON Schema."""

    def __init__(
        self,
        rules: Dict[str, list],
        regex_rules: set,
        recursive_rules: set,
        regex_engines: Dict[str, Dict[str, object]],
    ):
        self.rules = rules
        self.regex_rules = regex_rules
        self.recursive_rules = recursive_rules
        self.regex_engines = regex_engines

    def to_json_schema(self, rule: str) -> dict:
        """
        Возвращает JSON Schema для указанного правила.

        Для нерекурсивных правил: {"type": "string", "pattern": "<regex>"}
        Для рекурсивных правил: {"type": "string", "description": "<BNF>"}
        """
        if not isinstance(rule, str):
            raise TypeError("rule должен быть строкой")

        if rule not in self.rules:
            raise PatternError(f"{RULE_PREFIX}'{rule}'{RULE_NOT_FOUND}")

        if rule in self.regex_rules:
            engines = self.regex_engines.get(rule)
            if not engines:
                raise PatternError(f"{RULE_PREFIX}'{rule}'{RULE_NOT_COMPILED}")

            compiled = engines[METHOD_MATCH]
            pattern_str = compiled.pattern
            if pattern_str.startswith('^'):
                pattern_str = pattern_str[1:]
            if pattern_str.endswith('$'):
                pattern_str = pattern_str[:-1]

            return {JSON_KEY_TYPE: JSON_KEY_STRING, KEY_PATTERN: pattern_str}

        tokens = self.rules[rule]
        bnf_text = ' '.join(tokens)
        return {
            JSON_KEY_TYPE: JSON_KEY_STRING,
            "description": bnf_text,
        }

    def get_info(self) -> dict:
        """Возвращает отладочную информацию о грамматике."""
        formatted_rules = {}
        for name, tokens in self.rules.items():
            formatted_rules[name] = ' '.join(tokens)

        return {
            'total_rules': len(self.rules),
            'regex_rules': sorted(list(self.regex_rules)),
            'parser_rules': sorted(list(self.recursive_rules)),
            'rules': formatted_rules
        }
