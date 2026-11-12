"""
Pydantic-интеграция для pattern-grammar.

Опциональный модуль — требует установки pydantic:
    pip install pattern-grammar[pydantic]

Пример использования:
    from pydantic import BaseModel
    from pattern_grammar import Pattern as PatternGrammar

    from pattern_grammar.integrations.pydantic import PatternType

    pattern = PatternGrammar('''
        email ::= [a-z]+ "@" [a-z]+ ".com"
    ''')

    class User(BaseModel):
        email: PatternType(pattern, 'email')
"""

from ..constants import PYDANTIC_PACKAGE
try:
    import importlib.util
    if importlib.util.find_spec(PYDANTIC_PACKAGE) is None:
        raise ImportError("pydantic не установлен")
    from pydantic import GetJsonSchemaHandler
    from pydantic.json_schema import JsonSchemaValue
    from pydantic_core import CoreSchema, core_schema
    from typing import Any
except ImportError:
    raise ImportError(
        "Pydantic-интеграция требует установки pydantic.\n"
        "Установите его командой: pip install pattern-grammar[pydantic]\n"
        "Или: pip install pydantic"
    )

from pattern_grammar import Pattern, PatternError


class PatternValidator:
    """
    Валидатор Pydantic на основе Pattern Grammar.

    Используется как обёртка вокруг Pattern.match().
    """

    def __init__(self, pattern: Pattern, rule: str):
        """
        :param pattern: Экземпляр Pattern Grammar
        :param rule: Имя правила в грамматике
        """
        self.pattern = pattern
        self.rule = rule

    def __get_pydantic_core_schema__(
        self,
        _source_type: Any,
        _handler: GetJsonSchemaHandler,
    ) -> CoreSchema:
        """Возвращает CoreSchema для Pydantic v2."""
        return core_schema.no_info_before_validator_function(
            self._validate,
            core_schema.str_schema(),
        )

    def __get_pydantic_json_schema__(
        self,
        _core_schema: CoreSchema,
        handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        """Возвращает JSON Schema для валидатора."""
        schema = self.pattern.to_json_schema(self.rule)
        return schema

    def _validate(self, value: Any) -> str:
        """Проверяет значение через pattern.match()."""
        if not isinstance(value, str):
            raise ValueError(
                f"Ожидалась строка, получено {type(value).__name__}"
            )
        try:
            is_match = self.pattern.match(self.rule, value)
        except PatternError as exc:
            raise ValueError(str(exc))
        if not is_match:
            fail_msg = self.pattern._fail_messages.get(self.rule)
            if fail_msg:
                raise ValueError(fail_msg)
            raise ValueError(
                f"Значение '{value}' не соответствует правилу '{self.rule}'"
            )
        return value


def PatternType(pattern: Pattern, rule: str) -> PatternValidator:
    """
    Функция-обёртка для создания PatternValidator.

    Используется в аннотациях Pydantic-моделей:

        class User(BaseModel):
            email: PatternType(email_pattern, 'email')
    """
    return PatternValidator(pattern, rule)
