"""
Pattern Grammar - Читаемые паттерны вместо регулярных выражений

Автоматически использует:
- Регулярные выражения для простых правил
- Lark парсер для рекурсивных правил
- Модуль regex (с поддержкой Unicode) при наличии UNICODE-классов
"""

from .analyzer import RecursionAnalyzer
from .api import match, parse
from .errors import PatternError
from .generator import GrammarGenerator
from .lark_converter import LarkConverter
from .parser import BNFParser
from .pattern_compile import CompileEngine
from .pattern_fail import FailChecker
from .pattern_info import PatternInfo
from .pattern_match import MatchEngine
from .pattern_parse import ParseEngine
from .regex_converter import RegexConverter
from .constants import RULE_NAME_TYPE_ERROR

from typing import List, Optional


__version__ = "0.1.0"

__all__ = [
    'Pattern',
    'PatternError',
    'BNFParser',
    'RecursionAnalyzer',
    'RegexConverter',
    'LarkConverter',
    'GrammarGenerator',
    'match',
    'parse',
    '__version__',
]


class Pattern:
    """
    Основной класс для работы с паттернами

    Пример использования:
    >>> pattern = Pattern('''
    ...     email ::= username "@" domain "." tld
    ...     username ::= [a-zA-Z0-9._%+-]+
    ...     domain ::= [a-zA-Z0-9.-]+
    ...     tld ::= [a-zA-Z]{2,}
    ... ''')
    >>> pattern.match('email', 'test@example.com')
    True
    """

    def __init__(
        self,
        grammar_text: str,
        base_path: Optional[str] = None,
    ):
        """
        Инициализирует паттерн из текста грамматики.

        :param grammar_text: Текст грамматики в формате Pattern Grammar
        :param base_path: Базовый путь для разрешения относительных импортов.
                          Если передан путь к файлу, импорты разрешаются
                          относительно его директории.
        """
        if not isinstance(grammar_text, str):
            raise TypeError("grammar_text должен быть строкой")

        self.grammar_text = grammar_text
        self._base_path = base_path
        # Компилируем грамматику в движки (заполняем self.rules, regex_engines и т.д.)
        CompileEngine(self.grammar_text, self._base_path).compile(self)
        # Связываем хелперы со скомпилированным состоянием
        match_engine = MatchEngine(
            self.regex_engines, self.parser_engines,
            self.regex_rules, self.recursive_rules, None,
        )
        fail_checker = FailChecker(
            self.rules, self.regex_rules,
            self._fail_messages, self._fail_group_map, self.parser, match_engine,
        )
        match_engine._fail_checker = fail_checker
        self._match = match_engine
        self._fail = fail_checker
        self._parse = ParseEngine(
            self.regex_engines, self.parser_engines,
            self.regex_rules, self.recursive_rules,
        )
        self._info = PatternInfo(
            self.rules, self.regex_rules, self.recursive_rules, self.regex_engines,
        )

    def match(self, rule_name: str, text: str, *, ignore_case: bool = False) -> bool:
        """
        Проверяет, соответствует ли текст правилу

        :param rule_name: Имя правила
        :param text: Текст для проверки
        :param ignore_case: Игнорировать регистр символов (по умолчанию False)
        :return: True если соответствует, иначе False
        """
        return self._match.match(rule_name, text, ignore_case=ignore_case)

    def parse(
        self, rule_name: str, text: str, *, ignore_case: bool = False
    ) -> Optional[object]:
        """
        Парсит текст и возвращает дерево разбора (AST)

        :param rule_name: Имя правила
        :param text: Текст для парсинга
        :param ignore_case: Игнорировать регистр символов (по умолчанию False)
        :return: Дерево разбора или None
        :note:
            Для рекурсивных правил ignore_case реализован через text.lower()
            перед парсингом. Грамматика при этом должна содержать только
            символы в нижнем регистре.
        """
        return self._parse.parse(rule_name, text, ignore_case=ignore_case)

    def findall(
        self, rule_name: str, text: str, *, ignore_case: bool = False
    ) -> list:
        """
        Находит все совпадения правила в тексте

        :param rule_name: Имя правила
        :param text: Текст для поиска
        :param ignore_case: Игнорировать регистр символов (по умолчанию False)
        :return: Список совпадений
        """
        return self._match.findall(rule_name, text, ignore_case=ignore_case)

    def generate(
        self,
        rule_name: str,
        count: int = 1,
        max_depth: Optional[int] = None,
    ) -> List[str]:
        """
        Генерирует случайные строки, соответствующие правилу.

        :param rule_name: Имя правила
        :param count: Количество строк для генерации (по умолчанию 1)
        :param max_depth: Максимальная глубина рекурсии (по умолчанию 20)
        :return: Список сгенерированных строк (одна строка, если count=1)
        """
        if not isinstance(rule_name, str):
            raise TypeError(RULE_NAME_TYPE_ERROR)
        invalid_count = (not isinstance(count, int) or count < 1)
        if invalid_count:
            raise ValueError("count должен быть положительным целым числом")

        generator = GrammarGenerator(
            self.rules,
            self.regex_rules,
            self.recursive_rules,
            self.parser,
        )
        results = generator.generate(rule_name, count, max_depth)
        return results

    def to_json_schema(self, rule: str) -> dict:
        """
        Возвращает JSON Schema для указанного правила.

        Для нерекурсивных правил:
            {"type": "string", "pattern": "<regex>"}

        Для рекурсивных правил:
            {"type": "string", "description": "<BNF-описание>"}

        :param rule: Имя правила
        :return: Словарь JSON Schema
        :raises PatternError: Если правило не найдено
        :raises TypeError: Если rule не строка
        """
        return self._info.to_json_schema(rule)

    def get_info(self) -> dict:
        """
        Возвращает отладочную информацию о грамматике
        """
        return self._info.get_info()
