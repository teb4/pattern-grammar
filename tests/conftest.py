"""
Фикстуры для тестов pattern-grammar.
"""
import pytest
from pattern_grammar.parser import BNFParser
from pattern_grammar.analyzer import RecursionAnalyzer
from pattern_grammar.regex_converter import RegexConverter
from pattern_grammar.lark_converter import LarkConverter
from pattern_grammar import Pattern, PatternError


# =====================================================================
# Фикстуры для BNFParser
# =====================================================================

SIMPLE_GRAMMAR = """
email ::= username "@" domain "." tld
username ::= [a-zA-Z0-9._%+-]+
domain ::= [a-zA-Z0-9.-]+
tld ::= [a-zA-Z]{2,}
"""

EMAIL_RULES = {
    'email': ['username', '@', 'domain', '.', 'tld'],
    'username': ['[a-zA-Z0-9._%+-]+'],
    'domain': ['[a-zA-Z0-9.-]+'],
    'tld': ['[a-zA-Z]{2,}'],
}

# =====================================================================
# Фикстуры для Pattern
# =====================================================================

@pytest.fixture
def simple_pattern():
    """Базовый паттерн с email-грамматикой."""
    return Pattern(SIMPLE_GRAMMAR)


@pytest.fixture
def arithmetic_grammar():
    """Грамматика для арифметических выражений (с рекурсией)."""
    return """
expr ::= term (("+" | "-") term)*
term ::= factor (("*" | "/") factor)*
factor ::= [0-9]+ | "(" expr ")"
"""


@pytest.fixture
def arithmetic_pattern(arithmetic_grammar):
    """Паттерн с арифметическими выражениями."""
    return Pattern(arithmetic_grammar)


@pytest.fixture
def empty_alternative_grammar():
    """Паттерн с пустыми альтернативами."""
    from pattern_grammar import Pattern
    grammar = """
option ::= word (" " word)* | ""
word ::= [a-z]+
"""
    return Pattern(grammar)


@pytest.fixture
def hash_grammar():
    """Паттерн с хеш-символом (#)."""
    from pattern_grammar import Pattern
    grammar = """
commented ::= word "#" [a-z]+
word ::= [a-z]+
"""
    return Pattern(grammar)


@pytest.fixture
def quoted_grammar():
    """Паттерн с кавычными литералами."""
    from pattern_grammar import Pattern
    grammar = """
greeting ::= "hello" " " name
name ::= [a-z]+
"""
    return Pattern(grammar)


@pytest.fixture
def multi_line_grammar():
    """Паттерн с многострочными правилами."""
    from pattern_grammar import Pattern
    grammar = """
rule1 ::= [a-z]+ "." [0-9]+
  ("." [a-z]+)*
rule2 ::= "test"
"""
    return Pattern(grammar)


@pytest.fixture
def recursive_grammar():
    """Паттерн с явной рекурсией."""
    from pattern_grammar import Pattern
    grammar = """
list ::= item ("," item)*
item ::= [a-z]+
"""
    return Pattern(grammar)


# =====================================================================
# Фикстуры для BNFParser
# =====================================================================

@pytest.fixture
def parser():
    """Новый экземпляр BNFParser."""
    return BNFParser()


@pytest.fixture
def parsed_simple(parser):
    """BNFParser, уже распарсивший SIMPLE_GRAMMAR."""
    parser.parse(SIMPLE_GRAMMAR)
    return parser


# =====================================================================
# Фикстуры для анализатора рекурсии
# =====================================================================

@pytest.fixture
def simple_rules():
    """Простые правила без рекурсии."""
    return dict(EMAIL_RULES)


@pytest.fixture
def recursive_rules():
    """Правила с рекурсией."""
    return {
        'list': ['item', '|', 'list', ',', 'item'],
        'item': ['[a-z]+'],
    }


# =====================================================================
# Фикстуры для конвертеров
# =====================================================================

@pytest.fixture
def regex_converter(simple_rules):
    """RegexConverter для простых правил."""
    return RegexConverter(simple_rules, set(simple_rules.keys()), None)


@pytest.fixture
def lark_converter(simple_rules):
    """LarkConverter для простых правил."""
    return LarkConverter(simple_rules, set(), set(simple_rules.keys()), None)
