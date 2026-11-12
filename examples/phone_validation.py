#!/usr/bin/env python3
"""
Тестирование Pattern Grammar на номерах телефонов (E.164)
Сравнение оригинального regex и эквивалента на Pattern Grammar

E.164: +<country code><subscriber number>
Например: +12025551234 (США), +442071838762 (Великобритания), +74955555555 (Россия)

Также тестируем расширенные форматы с разделителями:
- С пробелами: +1 202 555 1234
- С дефисами: +7 495 555-55-55
- Со скобками: +1 (202) 555-1234
"""
import re
from pattern_grammar import Pattern

# =============================================================================
# 1. ОРИГИНАЛЬНЫЙ REGEX (E.164 — только цифры после +)
# =============================================================================
PHONE_E164_REGEX = r'^\+[1-9]\d{0,14}$'

# =============================================================================
# 2. ЭКВИВАЛЕНТ НА PATTERN GRAMMAR
# =============================================================================

PHONE_GRAMMAR = r"""
# E.164: +<first_digit><0-14 more digits>, всего 1-15 цифр
phone ::= e164
e164 ::= "+" first_digit rest_14
first_digit ::= [1-9]
rest_14 ::= digit {0,14}
digit ::= [0-9]
"""

# =============================================================================
# 3. РАСШИРЕННАЯ ГРАММАТИКА (с разделителями)
# =============================================================================
PHONE_GRAMMAR_EXTENDED = '''
# Главная точка входа
phone ::= e164_plain
        | e164_formatted

digit ::= [0-9]

# =============================================================================
# E.164 plain: +<1-9><digit>{0,14}, всего 1-15 цифр
# =============================================================================
e164_plain ::= "+" first_digit rest_14
first_digit ::= [1-9]
rest_14 ::= digit {0,14}

# =============================================================================
# Форматированный: +1 202 555 1234  /  +7 (495) 555-55-55
# country_code — 1-3 цифры (коды стран E.164: 1-3 цифры)
# area_code в скобках опционален
# Группы цифр разделены разделителями (пробел/дефис)
# =============================================================================
e164_formatted ::= "+" country_code parens_area? fmt_groups

country_code ::= digit {1,3}

parens_area ::= sep? "(" area_code ")"
area_code ::= digit {2,4}

# Группы цифр: разделитель опционален (для plain-формата без разделителей)
fmt_group ::= sep? group
sep ::= " " | "-"
fmt_groups ::= fmt_group+
group ::= digit {1,4}
'''

# =============================================================================
# 4. ТЕСТОВЫЕ ДАННЫЕ (E.164 plain)
# =============================================================================
PLAIN_TEST_CASES = [
    # ========== ВАЛИДНЫЕ E.164 ==========
    ('+12025551234', True, 'США (Washington DC)'),
    ('+442071838762', True, 'Великобритания (Лондон)'),
    ('+74955555555', True, 'Россия (Москва)'),
    ('+8613800138000', True, 'Китай'),
    ('+919876543210', True, 'Индия'),
    ('+4930123456789', True, 'Германия (Берлин)'),
    ('+33142123456', True, 'Франция (Париж)'),
    ('+81312345678', True, 'Япония (Токио)'),
    ('+5511987654321', True, 'Бразилия'),
    ('+61212345678', True, 'Австралия'),
    ('+12125551234', True, 'США (Нью-Йорк)'),
    ('+447911123456', True, 'Великобритания мобильный'),
    ('+79161234567', True, 'Россия мобильный'),

    # ========== КРАЕВЫЕ СЛУЧАИ ==========
    ('+12', True, 'Минимальная (2 цифры)'),
    ('+123', True, '3 цифры'),
    ('+' + '9' * 15, True, 'Максимум (15 цифр)'),
    ('+' + '9' * 14, True, '14 цифр'),
    ('+' + '9' * 16, False, 'Слишком длинный (16 цифр)'),

    # ========== НЕВАЛИДНЫЕ ==========
    ('12025551234', False, 'Без +'),
    ('+0', False, 'Код страны 0'),
    ('+00', False, 'Код страны 00'),
    ('+000', False, 'Код страны 000'),
    ('+012025551234', False, 'Начинается с 0'),
    ('', False, 'Пустая строка'),
    ('+', False, 'Только +'),
]

# =============================================================================
# 5. ТЕСТОВЫЕ ДАННЫЕ (расширенные форматы)
# =============================================================================
EXTENDED_TEST_CASES = [
    # ========== ВАЛИДНЫЕ ==========
    ('+1 202 555 1234', True, 'США с пробелами'),
    ('+44 20 7183 8762', True, 'Великобритания с пробелами'),
    ('+7 495 555-55-55', True, 'Россия с дефисами (смешанные)'),
    ('+1 (202) 555-1234', True, 'США со скобками и дефисами'),
    ('+44 (20) 7183 8762', True, 'Великобритания со скобками'),
    ('+7 (495) 555-55-55', True, 'Россия со скобками и дефисами'),
    ('+1-202-555-1234', True, 'США с дефисами'),

    # ========== НЕВАЛИДНЫЕ ==========
    ('+1.202.555.1234', False, 'Точки как разделители'),
    ('+1 (202) 555.1234', False, 'Точка внутри'),
    ('(202) 555-1234', False, 'Без + и кода страны'),
    ('1-202-555-1234', False, 'Дефис без +'),
]

# =============================================================================
# 6. ИНИЦИАЛИЗАЦИЯ
# =============================================================================
print("=" * 100)
print("ТЕСТИРОВАНИЕ ТЕЛЕФОННЫХ НОМЕРОВ (E.164)")
print("=" * 100)
print()

regex_compiled = re.compile(PHONE_E164_REGEX)
print("✅ Regex E.164 скомпилирован")

try:
    pattern = Pattern(PHONE_GRAMMAR)
    print("✅ Pattern Grammar (plain) успешно загружена")
except Exception as e:
    print(f"❌ Ошибка загрузки plain грамматики: {e}")
    import sys
    sys.exit(1)

try:
    pattern_ext = Pattern(PHONE_GRAMMAR_EXTENDED)
    print("✅ Pattern Grammar (extended) успешно загружена")
except Exception as e:
    print(f"❌ Ошибка загрузки extended грамматики: {e}")
    import sys
    sys.exit(1)

print()

# =============================================================================
# 7. ТЕСТЫ: E.164 PLAIN
# =============================================================================
print("ЧАСТЬ 1: E.164 PLAIN (только цифры после +)")
print("-" * 100)

total_plain = len(PLAIN_TEST_CASES)
grammar_plain_vs_expected = 0
regex_plain_vs_expected = 0
grammar_plain_vs_regex = 0

plain_results = []
for phone, expected, description in PLAIN_TEST_CASES:
    regex_result = bool(regex_compiled.match(phone))

    try:
        grammar_result = pattern.match('phone', phone)
    except Exception as e:
        grammar_result = f"ERROR: {e}"

    g_vs_e = None
    r_vs_e = None
    g_vs_r = None

    if isinstance(grammar_result, bool):
        g_vs_e = (grammar_result == expected)
        if g_vs_e:
            grammar_plain_vs_expected += 1

    r_vs_e = (regex_result == expected)
    if r_vs_e:
        regex_plain_vs_expected += 1

    if isinstance(grammar_result, bool):
        g_vs_r = (grammar_result == regex_result)
        if g_vs_r:
            grammar_plain_vs_regex += 1

    plain_results.append({
        'phone': phone,
        'expected': expected,
        'regex': regex_result,
        'grammar': grammar_result,
        'description': description,
        'g_vs_e': g_vs_e,
        'r_vs_e': r_vs_e,
        'g_vs_r': g_vs_r
    })

header = f"{'Номер':<25} {'Ожид.':<6} {'Regex':<8} {'Grammar':<8} {'GvE':<5} {'RvE':<5} {'GvR':<5} {'Описание'}"
print(header)
print("-" * 100)
for r in plain_results:
    g_vs_e_status = "✅" if r['g_vs_e'] else "❌" if r['g_vs_e'] is False else "?"
    r_vs_e_status = "✅" if r['r_vs_e'] else "❌" if r['r_vs_e'] is False else "?"
    g_vs_r_status = "✅" if r['g_vs_r'] else "❌" if r['g_vs_r'] is False else "?"

    regex_str = str(r['regex'])[:8]
    grammar_str = str(r['grammar'])[:8]
    phone_display = r['phone'][:24] + '..' if len(r['phone']) > 25 else r['phone']

    print(f"{phone_display:<25} {str(r['expected']):<6} {regex_str:<8} {grammar_str:<8} "
          f"{g_vs_e_status:<5} {r_vs_e_status:<5} {g_vs_r_status:<5} {r['description']}")
print("-" * 100)
print()

print("СТАТИСТИКА E.164 PLAIN:")
print("-" * 80)
grammar_plain_errors = total_plain - grammar_plain_vs_expected
regex_plain_errors = total_plain - regex_plain_vs_expected
grammar_plain_regex_diff = total_plain - grammar_plain_vs_regex
print(f"  Grammar с ожиданием:           {grammar_plain_vs_expected}/{total_plain} ({grammar_plain_vs_expected/total_plain*100:.1f}%)")
print(f"  Regex с ожиданием:             {regex_plain_vs_expected}/{total_plain} ({regex_plain_vs_expected/total_plain*100:.1f}%)")
print(f"  Grammar с Regex:               {grammar_plain_vs_regex}/{total_plain} ({grammar_plain_vs_regex/total_plain*100:.1f}%)")
print(f"  Ошибки Grammar:                {grammar_plain_errors}")
print(f"  Ошибки Regex:                  {regex_plain_errors}")
print(f"  Расхождения Grammar/Regex:     {grammar_plain_regex_diff}")
print("-" * 80)
print()

# =============================================================================
# 8. ТЕСТЫ: EXTENDED FORMATS
# =============================================================================
print("ЧАСТЬ 2: РАСШИРЕННЫЕ ФОРМАТЫ (с разделителями)")
print("-" * 100)

total_ext = len(EXTENDED_TEST_CASES)
grammar_ext_vs_expected = 0
ext_results = []

for phone, expected, description in EXTENDED_TEST_CASES:
    try:
        grammar_result = pattern_ext.match('phone', phone)
    except Exception as e:
        grammar_result = f"ERROR: {e}"

    g_vs_e = (grammar_result == expected) if isinstance(grammar_result, bool) else None
    if g_vs_e:
        grammar_ext_vs_expected += 1

    ext_results.append({
        'phone': phone,
        'expected': expected,
        'grammar': grammar_result,
        'description': description,
        'g_vs_e': g_vs_e
    })

header = f"{'Номер':<25} {'Ожид.':<6} {'Grammar':<8} {'GvE':<5} {'Описание'}"
print(header)
print("-" * 100)
for r in ext_results:
    g_vs_e_status = "✅" if r['g_vs_e'] else "❌" if r['g_vs_e'] is False else "?"
    grammar_str = str(r['grammar'])[:8]
    phone_display = r['phone'][:24] + '..' if len(r['phone']) > 25 else r['phone']

    print(f"{phone_display:<25} {str(r['expected']):<6} {grammar_str:<8} "
          f"{g_vs_e_status:<5} {r['description']}")
print("-" * 100)
print()

print("СТАТИСТИКА EXTENDED:")
print("-" * 80)
grammar_ext_errors = total_ext - grammar_ext_vs_expected
print(f"  Grammar с ожиданием:           {grammar_ext_vs_expected}/{total_ext} ({grammar_ext_vs_expected/total_ext*100:.1f}%)")
print(f"  Ошибки Grammar:                {grammar_ext_errors}")
print("-" * 80)
print()

# =============================================================================
# 9. ОБЩАЯ СТАТИСТИКА
# =============================================================================
total_all = total_plain + total_ext
all_pass = grammar_plain_vs_expected + grammar_ext_vs_expected
print("ОБЩАЯ СТАТИСТИКА:")
print("-" * 80)
print(f"  Всего тестов:                {total_all}")
print(f"  Passed (Grammar):            {all_pass}/{total_all} ({all_pass/total_all*100:.1f}%)")
print(f"  Passed (Regex):              {regex_plain_vs_expected}/{total_plain} (только plain)")
print("-" * 80)
print()

# =============================================================================
# 10. ДЕТАЛЬНЫЙ АНАЛИЗ
# =============================================================================
if grammar_plain_errors > 0 or regex_plain_errors > 0 or grammar_plain_regex_diff > 0:
    print("⚠️  НАЙДЕНЫ РАСХОЖДЕНИЯ (plain):")
    print("-" * 80)
    if grammar_plain_errors > 0:
        print("\n📌 Grammar НЕ совпадает с ожиданием:")
        for r in plain_results:
            if r['g_vs_e'] is False:
                print(f"  • {r['phone']}: grammar={r['grammar']}, ожидалось={r['expected']}")
                print(f"    → {r['description']}")
    if regex_plain_errors > 0:
        print("\n📌 Regex НЕ совпадает с ожиданием:")
        for r in plain_results:
            if r['r_vs_e'] is False:
                print(f"  • {r['phone']}: regex={r['regex']}, ожидалось={r['expected']}")
                print(f"    → {r['description']}")
    if grammar_plain_regex_diff > 0:
        print("\n📌 Grammar и Regex НЕ совпадают:")
        for r in plain_results:
            if r['g_vs_r'] is False:
                print(f"  • {r['phone']}: grammar={r['grammar']}, regex={r['regex']}")
                print(f"    → {r['description']}")
else:
    print("✅ ВСЕ ТЕСТИ PLAIN ПРОЙДЕНЫ! Pattern Grammar полностью совместим с regex")
print()

if grammar_ext_errors > 0:
    print("⚠️  ОШИБКИ (extended):")
    print("-" * 80)
    for r in ext_results:
        if r['g_vs_e'] is False:
            print(f"  • {r['phone']}: grammar={r['grammar']}, ожидалось={r['expected']}")
            print(f"    → {r['description']}")
else:
    print("✅ ВСЕ ТЕСТИ EXTENDED ПРОЙДЕНЫ!")
print()

# =============================================================================
# 11. ИНФОРМАЦИЯ О ГРАММАТИКЕ
# =============================================================================
print("=" * 100)
print()
print("ИНФОРМАЦИЯ О ГРАММАТИКЕ (plain):")
print("-" * 80)
info = pattern.get_info()
print(f"Всего правил: {info.get('total_rules', 0)}")
print(f"Правила (regex):     {info.get('regex_rules', [])}")
print(f"Правила (parser):    {info.get('parser_rules', [])}")
print()

print("ИНФОРМАЦИЯ О ГРАММАТИКЕ (extended):")
print("-" * 80)
info_ext = pattern_ext.get_info()
print(f"Всего правил: {info_ext.get('total_rules', 0)}")
print(f"Правила (regex):     {info_ext.get('regex_rules', [])}")
print(f"Правила (parser):    {info_ext.get('parser_rules', [])}")
print()

# =============================================================================
# 12. ПРИМЕР ДЕРЕВА РАЗБОРА
# =============================================================================
print("ПРИМЕР ДЕРЕВА РАЗБОРА (+1 202 555 1234):")
print("-" * 80)
try:
    tree = pattern_ext.parse('phone', '+1 202 555 1234')
    if tree:
        print(tree.pretty())
    else:
        print("Дерево не получено")
except Exception as e:
    print(f"Ошибка при парсинге: {e}")

print()
print("ПРИМЕР ДЕРЕВА РАЗБОРА (+7 (495) 555-55-55):")
print("-" * 80)
try:
    tree = pattern_ext.parse('phone', '+7 (495) 555-55-55')
    if tree:
        print(tree.pretty())
    else:
        print("Дерево не получено")
except Exception as e:
    print(f"Ошибка при парсинге: {e}")

print("=" * 100)
