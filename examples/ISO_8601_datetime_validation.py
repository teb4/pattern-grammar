#!/usr/bin/env python3
"""
Тестирование Pattern Grammar на ISO 8601 датах
Сравнение оригинального regex и эквивалента на Pattern Grammar
"""
import re
from pattern_grammar import Pattern

# =============================================================================
# 1. ОРИГИНАЛЬНЫЙ REGEX (ISO 8601)
# =============================================================================
ISO8601_REGEX = r'^(?:[\+-]?\d{4}(?!\d{2}\b))(?:(-?)(?:(?:0[1-9]|1[0-2])(?:\1(?:[12]\d|0[1-9]|3[01]))?|W(?:[0-4]\d|5[0-2])(?:-?[1-7])?|(?:00[1-9]|0[1-9]\d|[12]\d{2}|3(?:[0-5]\d|6[1-6])))(?:[T\s](?:(?:(?:[01]\d|2[0-3])(?:(:?)[0-5]\d)?|24\:?00)(?:[\.,]\d+(?!:))?)?(?:\2[0-5]\d(?:[\.,]\d+)?)?(?:[zZ]|(?:[\+-])(?:[01]\d|2[0-3]):?(?:[0-5]\d)?)?)?)?$'

# =============================================================================
# 2. ЭКВИВАЛЕНТ НА PATTERN GRAMMAR
# =============================================================================

ISO8601_GRAMMAR = """
datetime     ::= (date (time_sep time)?) | week_date | ordinal_date
date         ::= year sep? month31 sep? day31
               | year sep? month30 sep? day30
               | year sep? month_feb sep? day_feb
year         ::= sign [0-9]+ | [0-9]{4}
sign         ::= [+-]
month31      ::= '01' | '03' | '05' | '07' | '08' | '10' | '12'
month30      ::= '04' | '06' | '09' | '11'
month_feb    ::= '02'
day31        ::= '0'[1-9] | [12][0-9] | '30' | '31'
day30        ::= '0'[1-9] | [12][0-9] | '30'
day_feb      ::= '0'[1-9] | [12][0-9]
sep          ::= '-'
week_date    ::= year sep? 'W' week (sep? week_day)?
week         ::= [0-4][0-9] | '5'[0-3]
week_day     ::= [1-7]
ordinal_date ::= year sep? day_of_year
day_of_year  ::= '00'[1-9] | '0'[1-9][0-9] | [12][0-9][0-9] | '3'[0-5][0-9] | '36'[0-6]
time         ::= midnight | hours (':' minutes (':' seconds)?)? fractional? timezone?
midnight     ::= '24' ':' '00' (':' '00')? fractional? timezone?
hours        ::= [0-1][0-9] | '2'[0-3]
minutes      ::= [0-5][0-9]
seconds      ::= [0-5][0-9]
fractional   ::= [.,] [0-9]+
time_sep     ::= 'T' | ' '
timezone     ::= 'Z' | 'z' | offset
offset       ::= ('+' | '-') offset_hours (':'? offset_minutes)?
offset_hours ::= [0-1][0-9] | '2'[0-3]
offset_minutes ::= [0-5][0-9]
"""

# =============================================================================
# 3. ТЕСТОВЫЕ ДАННЫЕ
# =============================================================================
TEST_CASES = [
    # ========== ОСНОВНЫЕ ФОРМАТЫ ДАТ ==========
    ('2024-03-15', True, 'Базовая дата (YYYY-MM-DD)'),
    ('2024-12-31', True, 'Последний день года'),
    ('2024-02-29', True, 'Високосный год'),
    ('2024-13-01', False, 'Невалидный месяц 13'),
    ('2024-04-31', False, 'Невалидный день (апрель имеет 30 дней)'),

    # ========== ГОДЫ СО ЗНАКОМ ==========
    ('+002024-03-15', True, 'Год со знаком +'),
    ('-000123-03-15', True, 'Год со знаком -'),
    ('2024-03-15', True, 'Год без знака'),

    # ========== НЕДЕЛЬНЫЙ ФОРМАТ ==========
    ('2024-W12', True, 'Неделя без дня'),
    ('2024-W12-5', True, 'Неделя с днём'),
    ('2024-W53', True, '53-я неделя (макс)'),
    ('2024-W54', False, 'Невалидная неделя 54'),
    ('2024-W12-8', False, 'Невалидный день недели 8'),
    ('2024-W12-0', False, 'Невалидный день недели 0'),

    # ========== ПОРЯДКОВЫЙ ФОРМАТ (ДЕНЬ В ГОДУ) ==========
    ('2024-001', True, 'Первый день года'),
    ('2024-091', True, '91-й день (апрель)'),
    ('2024-365', True, '365-й день (обычный год)'),
    ('2024-366', True, '366-й день (високосный)'),
    ('2024-367', False, '367-й день (невалидный)'),
    ('2024-000', False, '000 день (невалидный)'),

    # ========== БЕЗ РАЗДЕЛИТЕЛЯ ==========
    ('20240315', True, 'Без разделителей (YYYYMMDD)'),
    ('2024W12', True, 'Без разделителей (YYYYWww)'),
    ('2024091', True, 'Без разделителей (YYYYDDD)'),

    # ========== С ВРЕМЕНЕМ ==========
    ('2024-03-15T14:30:00', True, 'С временем (T разделитель)'),
    ('2024-03-15 14:30:00', True, 'С временем (пробел разделитель)'),
    ('2024-03-15T14:30', True, 'Без секунд'),
    ('2024-03-15T14', True, 'Только часы'),

    # ========== С ДРОБЯМИ ==========
    ('2024-03-15T14:30:15.123', True, 'С дробными секундами (точка)'),
    ('2024-03-15T14:30:15,456', True, 'С дробными секундами (запятая)'),
    ('2024-03-15T14:30,5', True, 'Дробные минуты'),
    ('2024-03-15T14,25', True, 'Дробные часы'),

    # ========== ЧАСОВЫЕ ПОЯСА ==========
    ('2024-03-15T14:30:00Z', True, 'UTC (Z)'),
    ('2024-03-15T14:30:00z', True, 'UTC (z)'),
    ('2024-03-15T14:30:00+03:00', True, 'Смещение +03:00'),
    ('2024-03-15T14:30:00-05:00', True, 'Смещение -05:00'),
    ('2024-03-15T14:30:00+0300', True, 'Смещение без :'),
    ('2024-03-15T14:30:00+03', True, 'Только часы в смещении'),
    ('2024-03-15T14:30:00+24:00', False, 'Невалидное смещение >23'),
    ('2024-03-15T14:30:00+03:60', False, 'Невалидные минуты 60'),

    # ========== ПОЛНОЧЬ ==========
    ('2024-03-15T24:00', True, 'Полночь (24:00)'),
    ('2024-03-15T24:00:00', True, 'Полночь с секундами'),
    ('2024-03-15T24:00:00Z', True, 'Полночь UTC'),
    ('2024-03-15T24:01', False, '24:01 невалидно'),
    ('2024-03-15T24:00:01', False, '24:00:01 невалидно'),

    # ========== КРАЕВЫЕ СЛУЧАИ ==========
    ('2024-03-15T14:30:00.123Z', True, 'Дробные секунды с UTC'),
    ('2024-03-15T14:30:00,123+03:00', True, 'Дробные секунды со смещением'),
    ('2024-03-15T14:30:00.123+03:00', True, 'Полный формат'),

    # ========== НЕВАЛИДНЫЕ ФОРМАТЫ ==========
    ('2024-03', False, 'Неполная дата (только год-месяц)'),
    ('2024', False, 'Только год'),
    ('2024-03-15T', False, 'Только T без времени'),
    ('2024-03-15T14:30:60', False, 'Секунды 60'),
    ('2024-03-15T14:60', False, 'Минуты 60'),
    ('2024-03-15T25:00', False, 'Часы 25'),
    ('invalid-date', False, 'Полностью невалидная строка'),

    # ========== ШЕСТИЗНАЧНЫЕ ЧИСЛА ==========
    ('20241234', False, '6 цифр подряд должны быть невалидны'),
    ('2024-123456', False, 'Год с 6 цифрами после дефиса'),
]

# =============================================================================
# 4. ИНИЦИАЛИЗАЦИЯ
# =============================================================================
print("=" * 80)
print("ТЕСТИРОВАНИЕ ISO 8601 DATETIME")
print("=" * 80)
print()

# Компилируем regex
regex_compiled = re.compile(ISO8601_REGEX)

# Создаём Pattern Grammar
pattern = Pattern(ISO8601_GRAMMAR)

# Счётчики
regex_matches = 0
grammar_matches = 0
discrepancies = 0

# Счётчики совпадений с ожиданием
grammar_vs_expected = 0
regex_vs_expected = 0
grammar_vs_regex = 0

# =============================================================================
# 5. ЗАПУСК ТЕСТОВ
# =============================================================================
results = []
for date_str, expected, description in TEST_CASES:
    # Тестируем regex
    try:
        regex_result = bool(regex_compiled.match(date_str))
    except Exception as e:
        regex_result = f"ERROR: {e}"

    # Тестируем Pattern Grammar
    try:
        grammar_result = pattern.match('datetime', date_str)
    except Exception as e:
        grammar_result = f"ERROR: {e}"

    # Сравниваем результаты
    match_each_other = (regex_result == grammar_result) if isinstance(grammar_result, bool) else False

    # Сравнения с ожиданием
    g_vs_e = None
    r_vs_e = None
    g_vs_r = None

    if isinstance(grammar_result, bool):
        g_vs_e = (grammar_result == expected)
        if g_vs_e:
            grammar_vs_expected += 1

    if isinstance(regex_result, bool):
        r_vs_e = (regex_result == expected)
        if r_vs_e:
            regex_vs_expected += 1

    if isinstance(regex_result, bool) and isinstance(grammar_result, bool):
        g_vs_r = (grammar_result == regex_result)
        if g_vs_r:
            grammar_vs_regex += 1

    results.append({
        'date': date_str,
        'expected': expected,
        'regex': regex_result,
        'grammar': grammar_result,
        'description': description,
        'match_each_other': match_each_other,
        'g_vs_e': g_vs_e,
        'r_vs_e': r_vs_e,
        'g_vs_r': g_vs_r
    })

    # Обновляем старые счётчики
    if isinstance(regex_result, bool) and regex_result:
        regex_matches += 1
    if isinstance(grammar_result, bool) and grammar_result:
        grammar_matches += 1
    if not match_each_other and isinstance(grammar_result, bool) and isinstance(regex_result, bool):
        discrepancies += 1

# =============================================================================
# 6. ВЫВОД РЕЗУЛЬТАТОВ
# =============================================================================
print("РЕЗУЛЬТАТЫ ПО ТЕСТАМ:")
print("-" * 120)
header = f"{'Дата/время':<40} {'Ожид.':<6} {'Regex':<8} {'Grammar':<8} {'GvE':<5} {'RvE':<5} {'GvR':<5} {'Описание'}"
print(header)
print("-" * 120)

for r in results:
    # Формируем статусы
    g_vs_e_status = "✅" if r['g_vs_e'] else "❌" if r['g_vs_e'] is False else "?"
    r_vs_e_status = "✅" if r['r_vs_e'] else "❌" if r['r_vs_e'] is False else "?"
    g_vs_r_status = "✅" if r['g_vs_r'] else "❌" if r['g_vs_r'] is False else "?"

    regex_str = str(r['regex'])[:8]
    grammar_str = str(r['grammar'])[:8]
    date_display = r['date'][:37] + '...' if len(r['date']) > 40 else r['date']

    print(f"{date_display:<40} {str(r['expected']):<6} {regex_str:<8} {grammar_str:<8} "
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
print(f"  Grammar с Regex:                {grammar_vs_regex}/{len(TEST_CASES)} ({grammar_vs_regex/len(TEST_CASES)*100:.1f}%)")
print()
print("РАСХОЖДЕНИЯ:")
grammar_errors = len(TEST_CASES) - grammar_vs_expected
regex_errors = len(TEST_CASES) - regex_vs_expected
grammar_regex_diff = len(TEST_CASES) - grammar_vs_regex
print(f"  Grammar с ожиданием:           {grammar_errors}")
print(f"  Regex с ожиданием:             {regex_errors}")
print(f"  Grammar с Regex:                {grammar_regex_diff}")
print("-" * 80)
print()

# Детальный анализ расхождений
if grammar_errors > 0 or regex_errors > 0 or grammar_regex_diff > 0:
    print("⚠️  НАЙДЕНЫ РАСХОЖДЕНИЯ!")
    print("-" * 80)

    if grammar_errors > 0:
        print("\n📌 Grammar НЕ совпадает с ожиданием:")
        grammar_fails = [r for r in results if r['g_vs_e'] is False]
        for r in grammar_fails[:10]:  # Показываем первые 10
            print(f"  • {r['date']}: grammar={r['grammar']}, ожидалось={r['expected']}")
            print(f"    → {r['description']}")
        if len(grammar_fails) > 10:
            print(f"    ... и ещё {len(grammar_fails) - 10}")

    if regex_errors > 0:
        print("\n📌 Regex НЕ совпадает с ожиданием:")
        regex_fails = [r for r in results if r['r_vs_e'] is False]
        for r in regex_fails[:10]:  # Показываем первые 10
            print(f"  • {r['date']}: regex={r['regex']}, ожидалось={r['expected']}")
            print(f"    → {r['description']}")
        if len(regex_fails) > 10:
            print(f"    ... и ещё {len(regex_fails) - 10}")

    if grammar_regex_diff > 0:
        print("\n📌 Grammar и Regex НЕ совпадают между собой:")
        diff_fails = [r for r in results if r['g_vs_r'] is False]
        for r in diff_fails[:10]:  # Показываем первые 10
            print(f"  • {r['date']}: grammar={r['grammar']}, regex={r['regex']}")
            print(f"    → {r['description']}")
        if len(diff_fails) > 10:
            print(f"    ... и ещё {len(diff_fails) - 10}")
else:
    print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Pattern Grammar полностью совместим с regex")

print()
print("=" * 80)

# =============================================================================
# 8. ИНФОРМАЦИЯ О ГРАММАТИКЕ
# =============================================================================
print()
print("ИНФОРМАЦИЯ О ГРАММАТИКЕ:")
print("-" * 80)
info = pattern.get_info()
print(f"Всего правил: {info.get('total_rules', 0)}")
print(f"Правила (regex):     {info.get('regex_rules', [])}")
print(f"Правила (parser):    {info.get('parser_rules', [])}")
print()

# =============================================================================
# 9. ПРИМЕР ДЕРЕВА РАЗБОРА
# =============================================================================
print("ПРИМЕР ДЕРЕВА РАЗБОРА (2024-03-15T14:30:00+03:00):")
print("-" * 80)
try:
    tree = pattern.parse('datetime', '2024-03-15T14:30:00+03:00')
    if tree:
        print(tree.pretty())
    else:
        print("Дерево не получено (возможно, правило не поддерживает парсинг)")
except Exception as e:
    print(f"Ошибка при парсинге: {e}")

print("=" * 80)
