"""
Компиляция грамматики в движки (regex + Lark) для Pattern.

CompileEngine выполняет роль _compile/_compile_regex/_compile_lark:
распарсивает грамматику, определяет рекурсивные/regex-правила и
компилирует их в соответствующие движки. Результат записывается
в атрибуты переданного Pattern.
"""
import re
from typing import Dict
from .constants import METHOD_MATCH, METHOD_FINDALL

from lark import Lark

from .analyzer import RecursionAnalyzer
from .lark_converter import LarkConverter
from .parser import BNFParser
from .regex_converter import RegexConverter
from .unicode import has_unicode_classes, _require_regex


class CompileEngine:
    """Компилирует грамматику в regex- и Lark-движки."""

    def __init__(self, grammar_text: str, base_path=None):
        self.grammar_text = grammar_text
        self.base_path = base_path

    def compile(self, pattern) -> None:
        """
        Компилирует грамматику и записывает результат в атрибуты Pattern.

        :param pattern: Экземпляр Pattern (заполняется атрибутами)
        """
        parser = BNFParser()
        parser.parse(self.grammar_text, base_path=self.base_path)
        pattern.parser = parser
        pattern.rules = parser.get_rules()
        pattern._fail_messages = parser.get_fail_messages()

        analyzer = RecursionAnalyzer(pattern.rules)
        pattern.analyzer = analyzer
        pattern.recursive_rules = analyzer.find_recursive_rules()
        pattern.regex_rules = set(pattern.rules.keys()) - pattern.recursive_rules

        pattern.regex_engines: Dict[str, Dict[str, re.Pattern]] = {}
        pattern.parser_engines: Dict[str, object] = {}

        self._compile_regex(pattern)
        self._compile_lark(pattern)

    def _compile_regex(self, pattern) -> None:
        """Компилирует нерекурсивные правила в regex (встроенный метод)."""
        regex_converter = RegexConverter(
            pattern.rules, pattern.regex_rules, pattern.parser, pattern._fail_messages
        )

        has_unicode = False
        for rule_name in pattern.regex_rules:
            if has_unicode_classes(pattern.rules[rule_name]):
                has_unicode = True
                break

        pattern._fail_group_map: Dict[str, Dict[str, str]] = {}

        if has_unicode:
            regex_mod = _require_regex()
            for rule_name in pattern.regex_rules:
                regex_str, group_map = regex_converter.convert_with_named_groups(rule_name)
                pattern._fail_group_map[rule_name] = group_map
                pattern.regex_engines[rule_name] = {
                    METHOD_MATCH: regex_mod.compile(f'^{regex_str}$'),
                    METHOD_FINDALL: regex_mod.compile(regex_str)
                }
        else:
            for rule_name in pattern.regex_rules:
                regex_str, group_map = regex_converter.convert_with_named_groups(rule_name)
                pattern._fail_group_map[rule_name] = group_map
                pattern.regex_engines[rule_name] = {
                    METHOD_MATCH: re.compile(f'^{regex_str}$'),
                    METHOD_FINDALL: re.compile(regex_str)
                }

    def _compile_lark(self, pattern) -> None:
        """Компилирует рекурсивные правила через Lark (встроенный метод)."""
        lark_converter = LarkConverter(
            pattern.rules, pattern.recursive_rules, pattern.regex_rules, pattern.parser
        )

        for rule_name in pattern.recursive_rules:
            lark_grammar = lark_converter.convert(rule_name)
            lark_grammar = pattern.parser.restore_special_chars(lark_grammar)
            pattern.parser_engines[rule_name] = Lark(
                lark_grammar, start=rule_name, parser='lalr'
            )
