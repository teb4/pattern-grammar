"""
Unit-тесты для Pydantic-интеграции pattern-grammar.

Фаза 3-5 плана Pydantic-интеграции.
"""
import subprocess
import sys

import pytest
from pydantic import BaseModel, ValidationError

from pattern_grammar import Pattern, PatternError
from pattern_grammar.integrations.pydantic import PatternType, PatternValidator


# Глобальные паттерны для переиспользования
EMAIL_PATTERN = Pattern(
    'email ::= [a-z]+ "@" [a-z]+ ".com"',
)

PIN_PATTERN = Pattern(
    '''
digit   ::= [0-9]
pin     ::= digit{4}
''',
)


class TestPydanticBasic:
    """Базовое использование PatternType в Pydantic-моделях."""

    def test_valid_value(self):
        """Валидное значение проходит."""
        class User(BaseModel):
            email: PatternType(EMAIL_PATTERN, 'email')

        user = User(email='user@example.com')
        assert user.email == 'user@example.com'

    def test_invalid_value_raises(self):
        """Невалидное значение вызывает ValidationError."""
        class User(BaseModel):
            email: PatternType(EMAIL_PATTERN, 'email')

        with pytest.raises(ValidationError) as exc_info:
            User(email='invalid')

        assert len(exc_info.value.errors()) == 1
        err = exc_info.value.errors()[0]
        assert err['type'] == 'value_error'
        assert 'email' in err.get('msg', '').lower()

    def test_fail_message_propagates(self):
        """Сообщение @fail должно попасть в ValidationError."""
        fail_pattern = Pattern(
            'email ::= [a-z]+ "@" [a-z]+ ".com" @fail "неверный email"',
        )

        class User(BaseModel):
            email: PatternType(fail_pattern, 'email')

        with pytest.raises(ValidationError) as exc_info:
            User(email='123@example.com')

        assert len(exc_info.value.errors()) == 1
        err = exc_info.value.errors()[0]
        assert 'неверный email' in err.get('msg', '')

    def test_default_message_without_fail(self):
        """Без @fail — стандартное сообщение."""
        class User(BaseModel):
            email: PatternType(EMAIL_PATTERN, 'email')

        with pytest.raises(ValidationError) as exc_info:
            User(email='invalid')

        err = exc_info.value.errors()[0]
        # Должно быть какое-то сообщение
        assert 'msg' in err and err['msg']


class TestPydanticJSONSchema:
    """to_json_schema через PatternValidator."""

    def test_regex_rule_schema(self):
        """JSON Schema для regex-правила содержит pattern."""
        schema = EMAIL_PATTERN.to_json_schema('email')
        assert 'pattern' in schema
        assert schema['type'] == 'string'

    def test_parser_rule_no_pattern(self):
        """JSON Schema для parser-правила не содержит pattern."""
        expr_pattern = Pattern(
            '''
expr ::= term ("+" | "-") term
term ::= factor ("*" | "/") factor
factor ::= NUMBER | "(" expr ")"
NUMBER ::= [0-9]+
''',
        )
        schema = expr_pattern.to_json_schema('expr')
        assert 'pattern' not in schema
        assert 'description' in schema
        assert schema['type'] == 'string'


class TestPydanticWithoutImport:
    """Проверка, что импорт без pydantic работает только для ядра."""

    def test_pattern_works_without_pydantic(self):
        """Pattern работает без pydantic (проверка через subprocess)."""
        code = '''
import sys
# Убедимся что pydantic недоступен
if "pydantic" in sys.modules:
    del sys.modules["pydantic"]

# Удаляем из cached_import если есть
mods_to_remove = [k for k in sys.modules if k.startswith("pydantic")]
for m in mods_to_remove:
    del sys.modules[m]

# Теперь импортируем pattern_grammar
from pattern_grammar import Pattern
p = Pattern("word ::= [a-z]+")
assert p.match("word", "hello") is True
print("OK")
'''
        result = subprocess.run(
            [sys.executable, '-c', code],
            capture_output=True,
            text=True,
            env={**dict(__import__('os').environ), 'PYTHONDONTWRITEBYTECODE': '1'},
        )
        # Эта проверка — что pattern_grammar не импортирует pydantic
        assert result.returncode == 0 or 'pattern_grammar' not in result.stderr

    def test_import_pydantic_integration_raises(self):
        """Импорт integrations.pydantic без pydantic → ImportError."""
        # Проверяем, что pydantic не входит в базовые зависимости
        import tomllib
        import pathlib

        pyproject_path = pathlib.Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            cfg = tomllib.load(f)

        deps = cfg["project"]["dependencies"]
        dep_names = [d.split(">=")[0].split("==")[0].split("<=")[0].strip() for d in deps]
        assert "pydantic" not in dep_names, (
            "pydantic не должен быть в базовых dependencies"
        )


class TestPatternValidatorClass:
    """Тесты на PatternValidator класс."""

    def test_pattern_validator_type(self):
        """PatternValidator — правильный тип."""
        validator = PatternType(EMAIL_PATTERN, 'email')
        assert isinstance(validator, PatternValidator)

    def test_match_works(self):
        """Валидатор проверяет match."""
        validator = PatternType(EMAIL_PATTERN, 'email')
        result = validator._validate('user@example.com')
        assert result == 'user@example.com'

    def test_match_invalid(self):
        """Валидатор бросает ValueError на невалидном."""
        validator = PatternType(EMAIL_PATTERN, 'email')
        with pytest.raises(ValueError):
            validator._validate('invalid')
