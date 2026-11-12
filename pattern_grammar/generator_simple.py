r"""
Генерация для встроенных классов и escape-последовательностей.

Встроенные классы ([digit], [alpha] и т.д.) и escape (\d, \w и т.д.).
"""
import functools
import random
import string
from typing import Any, Callable, Dict



class SimpleGenerator:
    """Генератор для встроенных классов и escape-последовательностей."""

    def generate_builtin(self, name: str) -> str:
        """Генерирует символ для встроенного класса."""
        generators: Dict[str, Callable[[], str]] = {
            'digit': self._generate_builtin_digit,
            'digits': self._generate_builtin_digits,
            'alpha': functools.partial(random.choice, string.ascii_letters),
            'alnum': functools.partial(random.choice, string.ascii_letters + string.digits),
            'word': functools.partial(random.choice, string.ascii_letters + string.digits + '_'),
            'whitespace': functools.partial(random.choice, ' \t\n'),
            'space': functools.partial(random.choice, ' '),
            'tab': functools.partial(random.choice, '\t'),
            'newline': functools.partial(random.choice, '\n'),
        }
        generator = generators.get(name)
        is_generator = generator is not None
        result = generator() if is_generator else ''
        return result

    def _generate_builtin_digit(self) -> str:
        """Генерирует одну цифру."""
        return str(random.randint(0, 9))

    def _generate_builtin_digits(self) -> str:
        """Генерирует три цифры подряд."""
        return ''.join(str(random.randint(0, 9)) for _ in range(3))

    def generate_escape(self, escape: str) -> str:
        """Генерирует символ для escape-последовательности."""
        escape_map: Dict[str, Any] = {
            '\\d': self._generate_escape_d,
            '\\D': functools.partial(random.choice, string.ascii_letters),
            '\\s': functools.partial(random.choice, ' \t\n\r'),
            '\\S': functools.partial(random.choice, string.ascii_letters + string.digits),
            '\\w': functools.partial(random.choice, string.ascii_letters + string.digits + '_'),
            '\\W': functools.partial(random.choice, string.punctuation),
        }
        gen = escape_map.get(escape)
        is_gen = gen is not None
        result = gen() if is_gen else escape[1:]
        return result

    def _generate_escape_d(self) -> str:
        """Генерирует одну цифру для \\d."""
        return str(random.randint(0, 9))
