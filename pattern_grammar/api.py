"""
Публичное API Pattern Grammar

Удобные функции для быстрого использования грамматики без создания Pattern.
Вынесены в отдельный модуль, чтобы не нарушать правило №3 (макс. 7 функций в файле).
"""
from typing import Optional


def match(
    grammar_text: str,
    rule_name: str,
    text: str,
    base_path: Optional[str] = None,
    *,
    ignore_case: bool = False,
) -> bool:
    """
    Быстрая проверка соответствия

    :param grammar_text: Текст грамматики
    :param rule_name: Имя правила
    :param text: Текст для проверки
    :param base_path: Базовый путь для разрешения относительных импортов
    :param ignore_case: Игнорировать регистр символов (по умолчанию False)
    :return: True если соответствует, иначе False
    """
    from pattern_grammar import Pattern
    pattern = Pattern(grammar_text, base_path=base_path)
    return pattern.match(rule_name, text, ignore_case=ignore_case)


def parse(
    grammar_text: str,
    rule_name: str,
    text: str,
    base_path: Optional[str] = None,
    *,
    ignore_case: bool = False,
) -> Optional[object]:
    """
    Быстрый парсинг

    :param grammar_text: Текст грамматики
    :param rule_name: Имя правила
    :param text: Текст для парсинга
    :param base_path: Базовый путь для разрешения относительных импортов
    :param ignore_case: Игнорировать регистр символов (по умолчанию False)
    :return: Дерево разбора или None
    """
    from pattern_grammar import Pattern
    pattern = Pattern(grammar_text, base_path=base_path)
    return pattern.parse(rule_name, text, ignore_case=ignore_case)
