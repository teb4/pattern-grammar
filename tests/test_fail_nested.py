"""
Unit-тесты для поведения @fail при вложенных правилах.

Критично для Pydantic-интеграции: если пользователь декомпозирует грамматику
на под-правила, каждое со своим @fail, то при ошибке в под-правиле сообщение
должно относиться именно к этому под-правилю, а не "проглатываться" внешним
@fail правила-родителя.
"""
import pytest
from pattern_grammar import Pattern, PatternError


class TestFailNestedRules:
    """Проверка поведения @fail при вложенных правилах."""

    def test_nested_regex_fail_inner_message(self):
        """
        Оба правила — regex (нерекурсивные).
        username ссылается на [a-z]+, domain — на [a-z]+.
        email ::= username "@" domain.
        Если username не совпадает, должно всплыть сообщение из username.
        """
        grammar = '''
username ::= [a-z]+ @fail "ошибка username"
domain   ::= [a-z]+   @fail "ошибка domain"
email    ::= username "@" domain
'''
        p = Pattern(grammar)
        # username = "123" не совпадает с [a-z]+
        with pytest.raises(PatternError, match="ошибка username"):
            p.match('email', '123@example.com')

    def test_nested_regex_fail_outer_message(self):
        """
        Если совпадает username, но не domain — должно быть сообщение domain.
        """
        grammar = '''
username ::= [a-z]+ @fail "ошибка username"
domain   ::= [a-z]+   @fail "ошибка domain"
email    ::= username "@" domain
'''
        p = Pattern(grammar)
        # username совпадает, domain — "123" не совпадает с [a-z]+
        with pytest.raises(PatternError, match="ошибка domain"):
            p.match('email', 'user@123')

    def test_nested_regex_both_with_fail(self):
        """
        Если оба под-правила имеют @fail, ошибка должна быть от
        именно того правила, которое не совпало.
        """
        grammar = '''
a ::= [a-z]+ @fail "ошибка a"
b ::= [a-z]+ @fail "ошибка b"
ab  ::= a "-" b
'''
        p = Pattern(grammar)
        # Первое — не буквы
        with pytest.raises(PatternError, match="ошибка a"):
            p.match('ab', '123-abc')
        # Второе — не буквы
        with pytest.raises(PatternError, match="ошибка b"):
            p.match('ab', 'abc-123')

    def test_nested_mixed_regex_parser_fail(self):
        """
        Рекурсивное правило (через Lark) ссыается на regex-подправило.
        Если regex-подправило не совпало, его @fail должен всплыть.
        """
        grammar = '''
username ::= [a-z]+ @fail "ошибка username"
email    ::= username "@" [a-z]+ ".com"
'''
        p = Pattern(grammar)
        # username не совпадает
        with pytest.raises(PatternError, match="ошибка username"):
            p.match('email', '123@example.com')

    def test_fail_with_no_inner_fail_uses_outer(self):
        """
        Если под-правило НЕ имеет @fail, а внешнее — имеет,
        то при ошибке под-правила всплывает внешнее сообщение.
        """
        grammar = '''
username ::= [a-z]+
email    ::= username "@" [a-z]+ ".com" @fail "неверный email"
'''
        p = Pattern(grammar)
        # username не совпадает, у него нет @fail, всплывает outer
        with pytest.raises(PatternError, match="неверный email"):
            p.match('email', '123@example.com')

    def test_deeply_nested_fail_message(self):
        """
        Три уровня вложенности: level3 -> level2 -> level1 -> root.
        При ошибке на level3 должно быть сообщение level3.
        """
        grammar = '''
l3 ::= [a-z]+ @fail "ошибка l3"
l2 ::= l3 "-" [0-9]+ @fail "ошибка l2"
l1 ::= l2 "+" [a-z]+ @fail "ошибка l1"
root ::= l1
'''
        p = Pattern(grammar)
        # l3 не совпадает
        with pytest.raises(PatternError, match="ошибка l3"):
            p.match('root', '123-1+abc')
        # l2 ([0-9]+ не совпадает, вместо цифры буква)
        with pytest.raises(PatternError, match="ошибка l2"):
            p.match('root', 'abc-a+xyz')
        # Успешный match: l3=abc, -, 1, +, xyz
        assert p.match('root', 'abc-1+xyz') is True


class TestFailDecompositionPattern:
    """
    Проверка, что паттерн декомпозиции грамматики работает.
    Это основной use-case для Pydantic-интеграции.
    """

    def test_email_decomposition(self):
        """
        Email разбит на под-правила, каждое со своим @fail.
        При ошибке в домене — сообщение про домен.
        """
        grammar = '''
username ::= [a-z]+ @fail "некорректное имя пользователя"
domain   ::= [a-z]+   @fail "некорректный домен"
tld      ::= [a-z]{2,} @fail "некорректная зона"
email    ::= username "@" domain "." tld
'''
        p = Pattern(grammar)
        # Ошибка в username
        with pytest.raises(PatternError, match="некорректное имя пользователя"):
            p.match('email', '123@user.com')
        # Ошибка в домене
        with pytest.raises(PatternError, match="некорректный домен"):
            p.match('email', 'user@123.com')
        # Ошибка в tld
        with pytest.raises(PatternError, match="некорректная зона"):
            p.match('email', 'user@domain.c')

    def test_no_outer_fail_doesnt_gobble_inner(self):
        """
        Внешнее правило БЕЗ @fail не должно "проглатывать"
        ошибки внутренних правил с @fail.
        """
        grammar = '''
a ::= [a-z]+ @fail "ошибка a"
b ::= [a-z]+ @fail "ошибка b"
parent ::= a "-" b
'''
        p = Pattern(grammar)
        # parent не имеет @fail, но a — имеет.
        # Ошибка a должна всплыть наружу.
        with pytest.raises(PatternError, match="ошибка a"):
            p.match('parent', '123-abc')
