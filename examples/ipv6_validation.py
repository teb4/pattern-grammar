#!/usr/bin/env python3
"""
Тестирование Pattern Grammar на IPv6
Сравнение оригинального regex и эквивалента на Pattern Grammar
(Версия с расширенной статистикой по образцу test_url_rfc3986.py)
"""
import re
from pattern_grammar import Pattern

# =============================================================================
# 1. ОРИГИНАЛЬНЫЙ REGEX (IPv6 - упрощённый для тестирования)
# =============================================================================
# Базовый паттерн IPv6 (без всех edge-cases, но покрывает основные форматы)
IPV6_REGEX = r'^(?:(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:)?(?:(?:25[0-5]|(?:2[0-4]|1[0-9])?[0-9])\.){3}(?:25[0-5]|(?:2[0-4]|1[0-9])?[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1[0-9])?[0-9])\.){3}(?:25[0-5]|(?:2[0-4]|1[0-9])?[0-9]))$'

# =============================================================================
# 2. ЭКВИВАЛЕНТ НА PATTERN GRAMMAR
# =============================================================================

IPV6_GRAMMAR = """
ipv6 ::= full
       | compressed
       | mixed
       | link_local

# Полная форма (8 групп)
full ::= hgroup (":" hgroup){7}

# Сжатая форма с "::"
compressed ::= (prefix "::" suffix)
             | "::" suffix
             | prefix "::"
             | "::"

# Префикс для сжатой формы (1-7 групп)
prefix ::= hgroup (":" hgroup){0,6}

# Суффикс для сжатой формы (1-7 групп)
suffix ::= hgroup (":" hgroup){0,6}

# Смешанная форма (IPv6 + IPv4)
mixed ::= full_prefix ":" ipv4
        | prefix "::" ipv4
        | "::" ipv4
        | "::" hgroup ":" ipv4

# Префикс для смешанной формы (1-6 групп)
full_prefix ::= hgroup (":" hgroup){0,5}

# Локальные адреса link-local
link_local ::= "fe80:" (":" hgroup){0,4} "%" zone_id
zone_id    ::= [a-zA-Z0-9]+

# IPv4 часть
ipv4 ::= octet "." octet "." octet "." octet
octet ::= "25"[0-5]
        | "2"[0-4][0-9]
        | "1"[0-9][0-9]
        | [1-9][0-9]
        | [0-9]

# Базовые компоненты
hgroup   ::= hexdigit{1,4}
hexdigit ::= [0-9a-fA-F]
digit    ::= [0-9]
"""

# =============================================================================
# 3. ТЕСТОВЫЕ ДАННЫЕ
# =============================================================================
TEST_CASES = [
    # Полные адреса
    ('2001:0db8:85a3:0000:0000:8a2e:0370:7334', True, 'Полный формат'),
    ('0000:0000:0000:0000:0000:0000:0000:0001', True, 'Все нули + 1'),
    # Сжатые адреса (::)
    ('2001:db8::8a2e:370:7334', True, 'Сжатие в середине'),
    ('::1', True, 'localhost IPv6'),
    ('::', True, 'Все нули сжатые'),
    ('fe80::', True, 'Link-local сжатый'),
    ('2001:db8::', True, 'Префикс + ::'),
    ('::2001:db8', True, ':: + суффикс'),
    # Mixed IPv4
    ('::ffff:192.0.2.1', True, 'IPv4-mapped'),
    ('::192.0.2.1', True, 'IPv4-совместимый'),
    ('2001:db8::192.0.2.1', True, 'Mixed с префиксом'),
    # Link-local с zone ID
    ('fe80::1%eth0', True, 'Link-local с интерфейсом'),
    ('fe80::1234:5678:9abc:def0%wlan0', True, 'Link-local полный с zone'),
    # Невалидные
    ('2001:db8:::8a2e', False, 'Тройное двоеточие'),
    ('1200::AB00:1234::2552:7777:1313', False, 'Два ::'),
    ('2001:db8:85a3:::8a2e:370:7334', False, 'Лишний :'),
    ('12345::1', False, 'Группа >4 hex'),
    ('2001:db8::8a2e:370g:7334', False, 'Не hex символ'),
    ('192.0.2.1', False, 'Только IPv4'),
    ('', False, 'Пустая строка'),
    (':::', False, 'Только двоеточия'),
]

# =============================================================================
# 4. ИНИЦИАЛИЗАЦИЯ
# =============================================================================
print("=" * 90)
print("ТЕСТИРОВАНИЕ IPv6")
print("=" * 90)
print()

# Компилируем regex
regex_compiled = re.compile(IPV6_REGEX)
print("✅ Regex скомпилирован")

# Создаём Pattern Grammar
try:
    pattern = Pattern(IPV6_GRAMMAR)
    print("✅ Pattern Grammar успешно загружена")
except Exception as e:
    print(f"❌ Ошибка загрузки грамматики: {e}")
    import sys
    sys.exit(1)

print("\n" + "=" * 90 + "\n")

# Счётчики
regex_matches = 0
grammar_matches = 0

# Счётчики сравнения (как в test_url_rfc3986.py)
grammar_vs_expected = 0
regex_vs_expected = 0
grammar_vs_regex = 0

# =============================================================================
# 5. ЗАПУСК ТЕСТОВ
# =============================================================================
results = []
for addr, expected, description in TEST_CASES:
    # Тестируем regex
    regex_result = bool(regex_compiled.match(addr))
    if regex_result:
        regex_matches += 1

    # Тестируем Pattern Grammar
    try:
        grammar_result = pattern.match('ipv6', addr)
        if grammar_result:
            grammar_matches += 1
    except Exception as e:
        grammar_result = f"ERROR: {e}"

    # Сравниваем (логика из test_url_rfc3986.py)
    g_vs_e = None
    r_vs_e = None
    g_vs_r = None

    if isinstance(grammar_result, bool):
        g_vs_e = (grammar_result == expected)
        if g_vs_e:
            grammar_vs_expected += 1

    r_vs_e = (regex_result == expected)
    if r_vs_e:
        regex_vs_expected += 1

    if isinstance(grammar_result, bool):
        g_vs_r = (grammar_result == regex_result)
        if g_vs_r:
            grammar_vs_regex += 1

    results.append({
        'addr': addr,
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
header = f"{'Адрес':<40} {'Ожид.':<6} {'Regex':<6} {'Grammar':<8} {'GvE':<5} {'RvE':<5} {'GvR':<5} {'Описание'}"
print(header)
print("-" * 120)
for r in results:
    # Формируем статусы
    g_vs_e_status = "✅" if r['g_vs_e'] else "❌" if r['g_vs_e'] is False else "?"
    r_vs_e_status = "✅" if r['r_vs_e'] else "❌" if r['r_vs_e'] is False else "?"
    g_vs_r_status = "✅" if r['g_vs_r'] else "❌" if r['g_vs_r'] is False else "?"

    regex_str = str(r['regex'])[:6]
    grammar_str = str(r['grammar'])[:6]
    addr_display = r['addr'][:38] + '..' if len(r['addr']) > 40 else r['addr']

    print(f"{addr_display:<40} {str(r['expected']):<6} {regex_str:<6} {grammar_str:<8} "
          f"{g_vs_e_status:<5} {r_vs_e_status:<5} {g_vs_r_status:<5} {r['description']}")
print("-" * 120)
print()

# =============================================================================
# 7. СТАТИСТИКА
# =============================================================================
print("СТАТИСТИКА:")
print("-" * 90)
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
print("-" * 90)
print()

# Детальный анализ расхождений
if grammar_errors > 0 or regex_errors > 0 or grammar_regex_diff > 0:
    print("⚠️  НАЙДЕНЫ РАСХОЖДЕНИЯ!")
    print("-" * 90)
    if grammar_errors > 0:
        print("\n📌 Grammar НЕ совпадает с ожиданием:")
        for r in results:
            if r['g_vs_e'] is False:
                print(f"  • {r['addr']}: grammar={r['grammar']}, ожидалось={r['expected']}")
                print(f"    → {r['description']}")
    if regex_errors > 0:
        print("\n📌 Regex НЕ совпадает с ожиданием:")
        for r in results:
            if r['r_vs_e'] is False:
                print(f"  • {r['addr']}: regex={r['regex']}, ожидалось={r['expected']}")
                print(f"    → {r['description']}")
    if grammar_regex_diff > 0:
        print("\n📌 Grammar и Regex НЕ совпадают между собой:")
        for r in results:
            if r['g_vs_r'] is False:
                print(f"  • {r['addr']}: grammar={r['grammar']}, regex={r['regex']}")
                print(f"    → {r['description']}")
else:
    print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Pattern Grammar полностью совместим с regex")
print()
print("=" * 90)

# =============================================================================
# 8. ИНФОРМАЦИЯ О ГРАММАТИКЕ
# =============================================================================
print()
print("ИНФОРМАЦИЯ О ГРАММАТИКЕ:")
print("-" * 90)
info = pattern.get_info()
print(f"Всего правил: {info.get('total_rules', 0)}")
print(f"Правила (regex):     {info.get('regex_rules', [])}")
print(f"Правила (parser):    {info.get('parser_rules', [])}")
print()

# =============================================================================
# 9. ПРИМЕР ДЕРЕВА РАЗБОРА
# =============================================================================
print("ПРИМЕР ДЕРЕВА РАЗБОРА (2001:db8::8a2e:370:7334):")
print("-" * 90)
try:
    tree = pattern.parse('ipv6', '2001:db8::8a2e:370:7334')
    if tree:
        print(tree.pretty())
    else:
        print("Дерево не получено")
except Exception as e:
    print(f"Ошибка: {e}")
print("=" * 90)
