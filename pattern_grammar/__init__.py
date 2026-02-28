"""
Pattern Grammar - Читаемые паттерны вместо регулярных выражений

Автоматически использует:
- Регулярные выражения для простых правил
- Lark парсер для рекурсивных правил
"""

from .parser import BNFParser
from .analyzer import RecursionAnalyzer
from .regex_converter import RegexConverter
from .lark_converter import LarkConverter
from lark import Lark, Tree, Token
import re
from typing import Dict, Set, Optional, List

__version__ = "0.1.0"


class PatternError(Exception):
    """Базовое исключение для ошибок Pattern Grammar"""
    pass


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

    def __init__(self, grammar_text: str):
        """
        Инициализирует паттерн из текста грамматики

        :param grammar_text: Текст грамматики в формате Pattern Grammar
        """
        self.grammar_text = grammar_text

        # Парсим грамматику
        self.parser = BNFParser()
        self.parser.parse(grammar_text)
        self.rules = self.parser.get_rules()

        # Анализируем рекурсию
        self.analyzer = RecursionAnalyzer(self.rules)
        self.recursive_rules = self.analyzer.find_recursive_rules()
        self.regex_rules = set(self.rules.keys()) - self.recursive_rules

        # Компилируем движки
        self.regex_engines: Dict[str, Dict[str, re.Pattern]] = {}
        self.parser_engines: Dict[str, Lark] = {}

        self._compile_all()

    def _compile_all(self):
        """Компилирует все правила"""
        # Компилируем нерекурсивные правила в regex
        regex_converter = RegexConverter(self.rules, self.regex_rules, self.parser)

        for rule_name in self.regex_rules:
            try:
                regex_str = regex_converter.convert(rule_name)
                #print(f"DEBUG: Компилирую {rule_name} -> {regex_str}")

                # Для match используем ^...$ (полное совпадение)
                # Для findall используем без якорей (поиск в тексте)
                self.regex_engines[rule_name] = {
                    'match': re.compile(f'^{regex_str}$'),
                    'findall': re.compile(regex_str)
                }
            except Exception as e:
                raise PatternError(f"Не удалось скомпилировать правило '{rule_name}' в regex: {e}")

        ## Компилируем рекурсивные правила через Lark
        #lark_converter = LarkConverter(self.rules)

        # Компилируем рекурсивные правила через Lark
        #lark_converter = LarkConverter(self.rules, self.recursive_rules)
        #lark_converter = LarkConverter(self.rules, self.recursive_rules, self.regex_rules)
        lark_converter = LarkConverter(self.rules, self.recursive_rules, self.regex_rules, self.parser)

        for rule_name in self.recursive_rules:
            try:
                lark_grammar = lark_converter.convert(rule_name)
                # Восстанавливаем оригинальные символы в Lark грамматике
                lark_grammar = self.parser.restore_special_chars(lark_grammar)

                #print(f"\n=== Lark грамматика для '{rule_name}' ===")
                #print(lark_grammar)

                #self.parser_engines[rule_name] = Lark(lark_grammar, start=rule_name)
                #self.parser_engines[rule_name] = Lark(lark_grammar, start=rule_name, parser='earley')
                #self.parser_engines[rule_name] = Lark(lark_grammar, start=rule_name, parser='earley', lexer='standard')
                #self.parser_engines[rule_name] = Lark(lark_grammar, start=rule_name, parser='earley', lexer='basic')
                #self.parser_engines[rule_name] = Lark(lark_grammar, start=rule_name, lexer='basic')
                #self.parser_engines[rule_name] = Lark(lark_grammar, start=rule_name, parser='earley', lexer='basic')
                #self.parser_engines[rule_name] = Lark(lark_grammar, start=rule_name, parser='earley')

                #print(f"\n=== Lark грамматика для '{rule_name}' ===")
                #print(lark_grammar)
                #print("=" * 40)

                self.parser_engines[rule_name] = Lark(lark_grammar, start=rule_name, parser='lalr')
            except Exception as e:
                raise PatternError(f"Не удалось скомпилировать правило '{rule_name}' через Lark: {e}")

    def match(self, rule_name: str, text: str) -> bool:
        """
        Проверяет, соответствует ли текст правилу

        :param rule_name: Имя правила
        :param text: Текст для проверки
        :return: True если соответствует, иначе False
        """
        if rule_name in self.regex_rules:
            engines = self.regex_engines.get(rule_name)
            if not engines:
                raise PatternError(f"Правило '{rule_name}' не скомпилировано")

            pattern = engines['match']
            return pattern.match(text) is not None

        elif rule_name in self.recursive_rules:
            parser = self.parser_engines.get(rule_name)
            if not parser:
                raise PatternError(f"Парсер для правила '{rule_name}' не создан")

            try:
                #print(f"\n=== Парсинг {rule_name} ===")
                #print(f"Текст: {repr(text)}")
                result = parser.parse(text)
                #print(f"Результат парсинга: {result}")
                #print("=== Парсинг успешен ===\n")
                return True
            except Exception as e:
                #print(f"!!! Ошибка парсинга: {e}")
                #import traceback
                #traceback.print_exc()
                #print("=== Парсинг失敗 ===\n")
                return False

        else:
            raise PatternError(f"Правило '{rule_name}' не найдено")

    def parse(self, rule_name: str, text: str) -> Optional[Tree]:
        """
        Парсит текст и возвращает дерево разбора (AST)

        :param rule_name: Имя правила
        :param text: Текст для парсинга
        :return: Дерево разбора или None
        """
        if rule_name in self.recursive_rules:
            parser = self.parser_engines.get(rule_name)
            if not parser:
                raise PatternError(f"Парсер для правила '{rule_name}' не создан")

            try:
                return parser.parse(text)
            except Exception as e:
                raise PatternError(f"Ошибка парсинга: {e}")

        elif rule_name in self.regex_rules:
            engines = self.regex_engines.get(rule_name)
            if not engines:
                raise PatternError(f"Правило '{rule_name}' не скомпилировано")

            pattern = engines['match']
            match = pattern.match(text)
            if match:
                # Для regex возвращаем дерево с одним узлом
                return Tree('match', [Token('VALUE', text)])
            return None

        else:
            raise PatternError(f"Правило '{rule_name}' не найдено")

    def findall(self, rule_name: str, text: str) -> List[str]:
        """
        Находит все совпадения правила в тексте

        :param rule_name: Имя правила
        :param text: Текст для поиска
        :return: Список совпадений
        """
        if rule_name not in self.regex_rules:
            raise PatternError(f"Метод findall доступен только для нерекурсивных правил")

        engines = self.regex_engines.get(rule_name)
        if not engines:
            raise PatternError(f"Правило '{rule_name}' не скомпилировано")

        pattern = engines['findall']
        # ОТЛАДКА
        #print(f"DEBUG findall: pattern={pattern.pattern}")
        #print(f"DEBUG findall: text={repr(text)}")
        result = pattern.findall(text)
        #print(f"DEBUG findall: result={result}")

        return result

    def get_info(self) -> dict:
        """
        Возвращает отладочную информацию о грамматике

        :return: Словарь с информацией
        """
        # Форматируем правила для вывода
        formatted_rules = {}
        for name, tokens in self.rules.items():
            formatted_rules[name] = ' '.join(tokens)

        return {
            'total_rules': len(self.rules),
            'regex_rules': sorted(list(self.regex_rules)),
            'parser_rules': sorted(list(self.recursive_rules)),
            'rules': formatted_rules
        }

    def __repr__(self):
        return f"<Pattern rules={len(self.rules)} regex={len(self.regex_rules)} parser={len(self.recursive_rules)}>"


# Удобные функции для быстрого использования
def match(grammar_text: str, rule_name: str, text: str) -> bool:
    """
    Быстрая проверка соответствия

    :param grammar_text: Текст грамматики
    :param rule_name: Имя правила
    :param text: Текст для проверки
    :return: True если соответствует, иначе False
    """
    pattern = Pattern(grammar_text)
    return pattern.match(rule_name, text)


def parse(grammar_text: str, rule_name: str, text: str) -> Optional[Tree]:
    """
    Быстрый парсинг

    :param grammar_text: Текст грамматики
    :param rule_name: Имя правила
    :param text: Текст для парсинга
    :return: Дерево разбора или None
    """
    pattern = Pattern(grammar_text)
    return pattern.parse(rule_name, text)
