"""
Контейер вспомогательных генераторов для GrammarGenerator.

Группирует три специализированных генератора, чтобы GrammarGenerator
не превышал лимит атрибутов (правило №5).
"""
from .generator_char_class import CharClassGenerator
from .generator_simple import SimpleGenerator
from .generator_unicode import UnicodeGenerator


class GeneratorHelpers:
    """Хранит генераторы UNICODE, символьных классов и простых токенов."""

    def __init__(self):
        self.unicode = UnicodeGenerator()
        self.char_class = CharClassGenerator(self.unicode)
        self.simple = SimpleGenerator()
