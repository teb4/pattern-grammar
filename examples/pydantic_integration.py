"""
Пример интеграции pattern-grammar с Pydantic.

Требует опциональной зависимости:
    pip install pattern-grammar[pydantic]

Базовый функционал Pattern работает без Pydantic:
    pip install pattern-grammar
"""
from __future__ import annotations

from pydantic import BaseModel, ValidationError

from pattern_grammar import Pattern
from pattern_grammar.integrations.pydantic import PatternType

# ---------------------------------------------------------------------------
# Простая грамматика для email
# ---------------------------------------------------------------------------
email_pattern = Pattern(
    'email ::= [a-z]+ "@" [a-z]+ ".com"',
)


# ---------------------------------------------------------------------------
# Пример 1: Базовое использование
# ---------------------------------------------------------------------------
class User(BaseModel):
    """Модель пользователя с валидацией email через pattern-grammar."""

    name: str
    email: PatternType(email_pattern, 'email')


def example_basic() -> None:
    """Базовая валидация."""
    user = User(name='ivan', email='ivan@example.com')
    print(f'OK: {user.name} <{user.email}>')

    try:
        User(name='ivan', email='invalid')
    except ValidationError as exc:
        print(f'Validation error: {exc.errors()[0]["msg"]}')


# ---------------------------------------------------------------------------
# Пример 2: @fail — кастомные сообщения об ошибках
# ---------------------------------------------------------------------------
fail_pattern = Pattern(
    'email ::= [a-z]+ "@" [a-z]+ ".com" @fail "неверный email"',
)


class UserWithFail(BaseModel):
    email: PatternType(fail_pattern, 'email')


def example_fail_message() -> None:
    """Сообщение @fail попадает в ValidationError."""
    try:
        UserWithFail(email='123@example.com')
    except ValidationError as exc:
        err = exc.errors()[0]
        print(f'@fail message: {err["msg"]}')


# ---------------------------------------------------------------------------
# Пример 3: Вложенные правила с @fail
# ---------------------------------------------------------------------------
nested_pattern = Pattern(
    '''
username ::= [a-z]+ @fail "неверное имя пользователя"
domain   ::= [a-z]+ @fail "неверный домен"
email    ::= username "@" domain ".com"
''',
)


class NestedUser(BaseModel):
    email: PatternType(nested_pattern, 'email')


def example_nested_fail() -> None:
    """Вложенные @fail — сообщение от самого под-правила."""
    try:
        NestedUser(email='123@example.com')
    except ValidationError as exc:
        print(f'Nested @fail: {exc.errors()[0]["msg"]}')

    try:
        NestedUser(email='user@123.com')
    except ValidationError as exc:
        print(f'Nested @fail: {exc.errors()[0]["msg"]}')


# ---------------------------------------------------------------------------
# Пример 4: JSON Schema через to_json_schema
# ---------------------------------------------------------------------------
def example_json_schema() -> None:
    """to_json_schema для regex и parser правил."""
    schema = email_pattern.to_json_schema('email')
    print(f'Regex schema: {schema}')

    expr_pattern = Pattern(
        '''
expr ::= term ("+" | "-") term
term ::= factor ("*" | "/") factor
factor ::= NUMBER | "(" expr ")"
NUMBER ::= [0-9]+
''',
    )
    schema = expr_pattern.to_json_schema('expr')
    print(f'Parser schema: {schema}')


# ---------------------------------------------------------------------------
# Точка входа
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    print('=== Пример 1: Базовое использование ===')
    example_basic()

    print('\n=== Пример 2: @fail сообщение ===')
    example_fail_message()

    print('\n=== Пример 3: Вложенные @fail ===')
    example_nested_fail()

    print('\n=== Пример 4: JSON Schema ===')
    example_json_schema()
