"""
Обработка @fail сообщений для Pattern.

FailChecker отвечает за генерацию PatternError с сообщениями @fail,
включая вложенные @fail во внутренних правилах.
"""
import re
from typing import Dict, List, Optional

from .constants import BUILTIN_CLASSES
from .errors import PatternError
from .regex_converter import RegexConverter


class FailChecker:
    """Проверяет @fail сообщения и формирует ошибки."""

    def __init__(
        self,
        rules: Dict[str, List[str]],
        regex_rules: set,
        fail_messages: Dict[str, Optional[str]],
        fail_group_map: Dict[str, Dict[str, str]],
        parser,
        match_engine,
    ):
        self.rules = rules
        self.regex_rules = regex_rules
        self._fail_messages = fail_messages
        self._fail_group_map = fail_group_map
        self.parser = parser
        self._match_engine = match_engine

    def raise_if_fail(
        self, rule_name: str, text: str, compiled=None
    ) -> None:
        """
        Бросает PatternError с @fail сообщением, если оно есть.

        Если rule_name — правило с именованными группами для вложенных @fail,
        пытается определить, какое именно под-правило не совпало, и
        проверяет его по соответствующей части строки.
        """
        group_map = self._fail_group_map.get(rule_name, {})

        has_match = (group_map and text and compiled is not None)
        if has_match:
            inner_fails = self.find_inner_fail_rules_ordered(rule_name)

            if inner_fails:
                span_map = self.extract_spans_by_tokens(rule_name, text)

                for inner_rule, _inner_fail in inner_fails:
                    span = span_map.get(inner_rule)
                    if span is None:
                        try:
                            self.raise_if_fail_recursive(inner_rule, text)
                        except PatternError:
                            raise
                        raise self._make_error(inner_rule)

                    if self._match_engine._do_match(inner_rule, span):
                        continue
                    else:
                        raise self._make_error(inner_rule)

        message = self._fail_messages.get(rule_name)
        if message:
            raise self._make_error(rule_name, message)

    def _make_error(self, rule_name: str, message: Optional[str] = None) -> PatternError:
        """Встроенный метод: создает PatternError для правила."""
        text = message if message is not None else self._fail_messages.get(rule_name, '')
        return PatternError(text)

    def token_to_regex(self, token: str) -> str:
        """Преобразует токен в regex-строку (встроенный метод)."""
        is_char_class = (token.startswith('[') and token.endswith(']'))
        if is_char_class:
            return self.parser.restore_special_chars(token) if self.parser else token
        return token

    def raise_if_fail_recursive(
        self, rule_name: str, text: str
    ) -> None:
        """
        Рекурсивная версия raise_if_fail, не требующая compiled.

        Используется для поиска глубокой ошибки @fail.
        """
        inner_fails = self.find_inner_fail_rules_ordered(rule_name)

        if inner_fails:
            span_map = self.extract_spans_by_tokens(rule_name, text)

            for inner_rule, inner_msg in inner_fails:
                span = span_map.get(inner_rule)
                if span is None:
                    try:
                        self.raise_if_fail_recursive(inner_rule, text)
                    except PatternError:
                        raise
                    raise self._make_error(inner_rule, inner_msg)

                if self._match_engine._do_match(inner_rule, span):
                    continue
                else:
                    raise self._make_error(inner_rule, inner_msg)

        message = self._fail_messages.get(rule_name)
        if message:
            raise self._make_error(rule_name, message)

    def extract_spans_by_tokens(
        self, rule_name: str, text: str
    ) -> Dict[str, str]:
        """
        Извлекает span для каждого под-правила с @fail.

        Возвращает словарь {rule_name: matched_span}.
        Если какой-то токен не совпал — возвращает частичный словарь.
        """
        converter = RegexConverter(
            self.rules, self.regex_rules, self.parser, self._fail_messages
        )
        tokens = self.rules.get(rule_name, [])
        span_map: dict = {}
        pos = 0

        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token in ('|', '(', ')'):
                i += 1
                continue

            if token.startswith(('"', "'")):
                literal = token[1:-1]
                if text[pos:pos + len(literal)] == literal:
                    pos += len(literal)
                else:
                    return span_map
                i += 1
                continue

            is_char_class = (token.startswith('[') and token.endswith(']'))
            if is_char_class:
                next_token = tokens[i + 1] if i + 1 < len(tokens) else None
                is_quantifier = next_token in ('*', '+', '?')
                is_braced = (
                    next_token
                    and next_token.startswith('{')
                    and next_token.endswith('}')
                )

                is_quant_or_braced = is_quantifier or is_braced
                if is_quant_or_braced:
                    base_regex = self.token_to_regex(token)
                    assert next_token is not None
                    full_regex = base_regex + next_token
                    m = re.match(full_regex, text[pos:])
                    if m:
                        pos += len(m.group())
                        i += 2
                    else:
                        return span_map
                    continue
                else:
                    base_regex = self.token_to_regex(token)
                    m = re.match(base_regex, text[pos:])
                    if m:
                        pos += len(m.group())
                        i += 1
                    else:
                        return span_map
                    continue

            is_braced_token = (token.startswith('{') and token.endswith('}'))
            if is_braced_token:
                i += 1
                continue

            is_regex_rule_ref = (token in self.rules and token in self.regex_rules)
            if is_regex_rule_ref:
                regex_str = converter.convert(token)
                m = re.match(regex_str, text[pos:])
                if m:
                    pos += len(m.group())
                    span_map[token] = m.group()
                    i += 1
                else:
                    return span_map
                continue

            if token.startswith('\\'):
                if text[pos:pos + len(token)] == token:
                    pos += len(token)
                else:
                    return span_map
                i += 1
                continue

            i += 1

        return span_map

    def find_inner_fail_rules_ordered(
        self, rule_name: str
    ) -> List[tuple]:
        """
        Возвращает список (inner_rule, inner_fail) для вложенных правил
        с @fail в порядке их появления в токенах.
        """
        results: list = []
        seen: set = set()

        for token in self.rules.get(rule_name, []):
            is_delimiter = (token in ('|', '(', ')') or token.startswith(
                ('"', "'", '{', '\\')
            ))
            if is_delimiter:
                continue
            is_char_class = (token.startswith('[') and token.endswith(']'))
            if is_char_class:
                continue
            if token.lower() in BUILTIN_CLASSES:
                continue

            is_inner_fail_rule = (token in self.regex_rules
                and token in self._fail_messages
                and self._fail_messages[token]
                and token not in seen)
            if is_inner_fail_rule:
                seen.add(token)
                results.append((token, self._fail_messages[token]))

        return results
