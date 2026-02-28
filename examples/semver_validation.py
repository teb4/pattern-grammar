#!/usr/bin/env python3
"""
Тестирование Pattern Grammar на SemVer 2.0.0
Сравнение оригинального regex и эквивалента на Pattern Grammar
"""
import re
from pattern_grammar import Pattern
# =============================================================================
# 1. ОРИГИНАЛЬНЫЙ REGEX (SemVer 2.0.0)
# =============================================================================
SEMVER_REGEX = r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
# =============================================================================
# 2. ЭКВИВАЛЕНТ НА PATTERN GRAMMAR
# =============================================================================

SEMVER_GRAMMAR = """
# SemVer (Semantic Versioning) грамматика
# https://semver.org/spec/v2.0.0.html

semver ::= major "." minor "." patch pre_release? build_metadata?

# Основные компоненты версии
major ::= zero | non_zero_digit digits*
minor ::= zero | non_zero_digit digits*
patch ::= zero | non_zero_digit digits*

# Pre-release версия
pre_release ::= "-" pre_release_version

pre_release_version ::= pre_release_identifier ("." pre_release_identifier)*

pre_release_identifier ::= numeric_identifier
                         | alphanumeric_identifier

# Числовые идентификаторы (без ведущих нулей)
numeric_identifier ::= zero
                     | non_zero_digit digits*

# Буквенно-цифровые идентификаторы (могут содержать дефисы)
alphanumeric_identifier ::= digit* letter_or_dash alnum_or_dash*

# Build metadata
build_metadata ::= "+" build_identifier

build_identifier ::= build_segment ("." build_segment)*

build_segment ::= alnum_or_dash+

# Базовые компоненты
zero             ::= "0"
non_zero_digit   ::= [1-9]
digit            ::= [0-9]
digits           ::= [0-9]+
letter_or_dash   ::= [a-zA-Z-]
alnum_or_dash    ::= [a-zA-Z0-9-]
"""

# Рекурсивная версия

SEMVER_GRAMMAR = """
# SemVer (Semantic Versioning) грамматика
# https://semver.org/spec/v2.0.0.html

semver ::= core ("-" pre_release)? ("+" build)?

core ::= number "." number "." number

number ::= "0" | [1-9][0-9]*

# Рекурсивные списки
pre_release ::= identifier ("." pre_release)?
identifier ::= numeric | alphanumeric

numeric ::= "0" | [1-9][0-9]*
alphanumeric ::= [0-9]* [a-zA-Z-] [a-zA-Z0-9-]*

# Build metadata (тоже рекурсивно)
build ::= segment ("." build)?
segment ::= [a-zA-Z0-9-]+
"""

# =============================================================================
# 3. ТЕСТОВЫЕ ДАННЫЕ
# =============================================================================
TEST_CASES = [
# (версия, должно_совпасть, описание)
('1.0.0', True, 'Базовая версия'),
('0.0.0', True, 'Нулевая версия'),
('10.20.30', True, 'Многозначные числа'),
('1.0.0-alpha', True, 'Pre-release'),
('1.0.0-alpha.1', True, 'Pre-release с цифрой'),
('1.0.0-0.3.7', True, 'Numeric pre-release'),
('1.0.0-x.7.z.92', True, 'Alphanumeric pre-release'),
('1.0.0-alpha+001', True, 'Pre-release + build'),
('1.0.0+20130313144700', True, 'Build metadata'),
('1.0.0-beta+exp.sha.5114f85', True, 'Full version'),
('1.0.0-rc.1+build.123', True, 'Release candidate'),
('01.0.0', False, 'Ведущий ноль в major'),
('1.01.0', False, 'Ведущий ноль в minor'),
('1.0.01', False, 'Ведущий ноль в patch'),
('1.0', False, 'Нет patch'),
('1', False, 'Только major'),
('1.0.0-', False, 'Пустой pre-release'),
('1.0.0+', False, 'Пустой build'),
('v1.0.0', False, 'Префикс v'),
('1.0.0.0', False, 'Лишняя часть'),
('1.0.0-alpha..1', False, 'Две точки в pre-release'),
('1.0.0-01', False, 'Ведущий ноль в numeric identifier'),
('1.0.0-ä', False, 'Не ASCII символ'),
]
# =============================================================================
# 4. ИНИЦИАЛИЗАЦИЯ
# =============================================================================
print("=" * 80)
print("ТЕСТИРОВАНИЕ SemVer 2.0.0")
print("=" * 80)
print()
# Компилируем regex
regex_compiled = re.compile(SEMVER_REGEX)
print("✅ Original regex скомпилирован")
# Создаём Pattern Grammar
try:
    pattern = Pattern(SEMVER_GRAMMAR)
    print("✅ Pattern Grammar успешно загружена")
except Exception as e:
    print(f"❌ Ошибка загрузки грамматики: {e}")
    import sys
    sys.exit(1)
print()
print("=" * 80)
# Счётчики
regex_matches = 0
grammar_matches = 0
grammar_vs_expected = 0
regex_vs_expected = 0
grammar_vs_regex = 0
# =============================================================================
# 5. ЗАПУСК ТЕСТОВ
# =============================================================================
results = []
for version, expected, description in TEST_CASES:
    # Тестируем regex
    regex_result = bool(regex_compiled.match(version))
    if regex_result:
        regex_matches += 1
    # Тестируем Pattern Grammar
    try:
        grammar_result = pattern.match('semver', version)
        if grammar_result:
            grammar_matches += 1
    except Exception as e:
        grammar_result = f"ERROR: {e}"
    # Сравниваем
    g_vs_e = None
    r_vs_e = None
    g_vs_r = None
    if isinstance(grammar_result, bool):
        g_vs_e = (grammar_result == expected)
        if g_vs_e:
            grammar_vs_expected += 1
    if regex_result is not None:
        r_vs_e = (regex_result == expected)
        if r_vs_e:
            regex_vs_expected += 1
    if regex_result is not None and isinstance(grammar_result, bool):
        g_vs_r = (grammar_result == regex_result)
        if g_vs_r:
            grammar_vs_regex += 1
    results.append({
        'version': version,
        'expected': expected,
        'regex': regex_result,
        'grammar': grammar_result,
        'description': description,
        'g_vs_e': g_vs_e,
        'r_vs_e': r_vs_e,
        'g_vs_r': g_vs_r
    })
# =============================================================================
# 6. ВЫВОД РЕЗУЛЬТАТОВ
# =============================================================================
print("РЕЗУЛЬТАТЫ ПО ТЕСТАМ:")
print("-" * 120)
header = f"{'Версия':<25} {'Ожид.':<6} {'Regex':<8} {'Grammar':<8} {'GvE':<5} {'RvE':<5} {'GvR':<5} {'Описание'}"
print(header)
print("-" * 120)
for r in results:
    # Формируем статусы
    g_vs_e_status = "✅" if r['g_vs_e'] else "❌" if r['g_vs_e'] is False else "?"
    r_vs_e_status = "✅" if r['r_vs_e'] else "❌" if r['r_vs_e'] is False else "?"
    g_vs_r_status = "✅" if r['g_vs_r'] else "❌" if r['g_vs_r'] is False else "?"
    regex_str = str(r['regex'])[:8] if r['regex'] is not None else "N/A"
    grammar_str = str(r['grammar'])[:8]
    version_display = r['version'][:23] + '..' if len(r['version']) > 25 else r['version']
    print(f"{version_display:<25} {str(r['expected']):<6} {regex_str:<8} {grammar_str:<8} "
          f"{g_vs_e_status:<5} {r_vs_e_status:<5} {g_vs_r_status:<5} {r['description']}")
print("-" * 120)
print()
# =============================================================================
# 7. СТАТИСТИКА
# =============================================================================
print("СТАТИСТИКА:")
print("-" * 80)
print(f"Всего тестов:                    {len(TEST_CASES)}")
print()
print("СОВПАДЕНИЯ:")
print(f"  Grammar с ожиданием:           {grammar_vs_expected}/{len(TEST_CASES)} ({grammar_vs_expected/len(TEST_CASES)*100:.1f}%)")
print(f"  Regex с ожиданием:             {regex_vs_expected}/{len(TEST_CASES)} ({regex_vs_expected/len(TEST_CASES)*100:.1f}%)")
print(f"  Grammar с Regex:               {grammar_vs_regex}/{len(TEST_CASES)} ({grammar_vs_regex/len(TEST_CASES)*100:.1f}%)")
print()
print("РАСХОЖДЕНИЯ:")
grammar_errors = len(TEST_CASES) - grammar_vs_expected
regex_errors = len(TEST_CASES) - regex_vs_expected
grammar_regex_diff = len(TEST_CASES) - grammar_vs_regex
print(f"  Grammar с ожиданием:           {grammar_errors}")
print(f"  Regex с ожиданием:             {regex_errors}")
print(f"  Grammar с Regex:               {grammar_regex_diff}")
print("-" * 80)
print()
# =============================================================================
# 8. ДЕТАЛЬНЫЙ АНАЛИЗ РАСХОЖДЕНИЙ
# =============================================================================
if grammar_errors > 0 or regex_errors > 0 or grammar_regex_diff > 0:
    print("⚠️  НАЙДЕНЫ РАСХОЖДЕНИЯ!")
    print("-" * 80)
    if grammar_errors > 0:
        print("📌 Grammar НЕ совпадает с ожиданием:")
        for r in results:
            if r['g_vs_e'] is False:
                print(f"  • {r['version']}: grammar={r['grammar']}, ожидалось={r['expected']}")
                print(f"    → {r['description']}")
    if regex_errors > 0:
        print("📌 Regex НЕ совпадает с ожиданием:")
        for r in results:
            if r['r_vs_e'] is False:
                print(f"  • {r['version']}: regex={r['regex']}, ожидалось={r['expected']}")
                print(f"    → {r['description']}")
    if grammar_regex_diff > 0:
        print("📌 Grammar и Regex НЕ совпадают между собой:")
        for r in results:
            if r['g_vs_r'] is False:
                print(f"  • {r['version']}: grammar={r['grammar']}, regex={r['regex']}")
                print(f"    → {r['description']}")
else:
    print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Pattern Grammar полностью совместим с regex")
print()
print("=" * 80)
# =============================================================================
# 9. ИНФОРМАЦИЯ О ГРАММАТИКЕ
# =============================================================================
print()
print("ИНФОРМАЦИЯ О ГРАММАТИКЕ:")
print("-" * 80)
info = pattern.get_info()
print(f"Всего правил:        {info.get('total_rules', 0)}")
print(f"Правила (regex):     {info.get('regex_rules', [])}")
print(f"Правила (parser):    {info.get('parser_rules', [])}")
print()
# Проверка: используем ли Lark?
if info.get('parser_rules'):
    print("✅ Рекурсивные правила обнаружены → будет использоваться Lark parser")
else:
    print("⚠️  Рекурсивные правила НЕ обнаружены → что-то не так!")
print()
# =============================================================================
# 10. ПРИМЕР ДЕРЕВА РАЗБОРА
# =============================================================================
print("ПРИМЕР ДЕРЕВА РАЗБОРА (1.0.0-alpha+001):")
print("-" * 80)
try:
    tree = pattern.parse('semver', '1.0.0-alpha+001')
    if tree:
        print(tree.pretty())
    else:
        print("Дерево не получено")
except Exception as e:
    print(f"Ошибка: {e}")
print()
print("ПРИМЕР ДЕРЕВА РАЗБОРА (1.0.0-beta+exp.sha.5114f85):")
print("-" * 80)
try:
    tree = pattern.parse('semver', '1.0.0-beta+exp.sha.5114f85')
    if tree:
        print(tree.pretty())
    else:
        print("Дерево не получено")
except Exception as e:
    print(f"Ошибка: {e}")
print("=" * 80)
