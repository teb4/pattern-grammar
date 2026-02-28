#!/usr/bin/env python3
"""
Тестирование Pattern Grammar на URL (OWASP)
Сравнение оригинального regex и эквивалента на Pattern Grammar
"""
import re
from pattern_grammar import Pattern
# =============================================================================
# 1. ОРИГИНАЛЬНЫЙ REGEX (URL OWASP)
# =============================================================================
URL_REGEX = r'^(https?|ftp):\/\/(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+(?:[a-zA-Z]{2,})|localhost|\d{1,3}(?:\.\d{1,3}){3})(?::\d{2,5})?(?:\/[^\s?]*)?(?:\?[^\s#]*)?(?:#[^\s]*)?$'
# =============================================================================
# 2. ЭКВИВАЛЕНТ НА PATTERN GRAMMAR
# =============================================================================
URL_GRAMMAR = """
url ::= scheme "://" host port? path? query? fragment?
scheme ::= "http" | "https" | "ftp"
host ::= domain | "localhost" | ipv4
# 🔧 ИСПРАВЛЕНО: точка внутри повторяемого элемента
domain ::= label_with_dot+ tld
label_with_dot ::= label "."
label ::= alnum (alnum_or_dash* alnum)?
tld ::= alpha{2,}
ipv4 ::= octet "." octet "." octet "." octet
octet ::= digit{1,3}
port ::= ":" digit{2,5}
path ::= "/" path_segment*
path_segment ::= [^\\s?]+
query ::= "?" [^\\s#]*
fragment ::= "#" [^\\s]*
alnum ::= [a-zA-Z0-9]
alpha ::= [a-zA-Z]
digit ::= [0-9]
alnum_or_dash ::= [a-zA-Z0-9-]
"""

URL_GRAMMAR = """
# URL грамматика (http, https, ftp)
url ::= scheme "://" authority path? query? fragment?

# Поддерживаемые схемы
scheme ::= "http" | "https" | "ftp"

# Authority (хост + опциональный порт)
authority ::= host port?

# Хост может быть доменом, localhost или IPv4
host ::= domain
       | "localhost"
       | ipv4

# Доменное имя
domain ::= label ("." label)* "." tld
label ::= alnum (alnum_or_dash* alnum)?
tld ::= alpha{2,}

# IPv4 адрес
ipv4 ::= octet "." octet "." octet "." octet
octet ::= "25"[0-5]
        | "2"[0-4][0-9]
        | "1"[0-9][0-9]
        | [1-9][0-9]
        | [0-9]

# Опциональный порт
port ::= ":" digit{2,5}

# Путь (исправлено для длинных путей)
path ::= "/" path_segments
path_segments ::= path_segment ("/" path_segment)*
path_segment ::= [^\\s?/#]+

# Query параметры
query ::= "?" [^\\s#]*

# Fragment
fragment ::= "#" [^\\s]*

# Базовые компоненты
alnum ::= [a-zA-Z0-9]
alpha ::= [a-zA-Z]
digit ::= [0-9]
alnum_or_dash ::= [a-zA-Z0-9-]
"""

# =============================================================================
# 3. ТЕСТОВЫЕ ДАННЫЕ
# =============================================================================
TEST_CASES = [
# (URL, должно_совпасть, описание)
('http://example.com', True, 'Базовый HTTP'),
('https://example.com', True, 'Базовый HTTPS'),
('ftp://files.example.com', True, 'FTP'),
('http://localhost', True, 'localhost'),
('http://localhost:8080', True, 'localhost с портом'),
('http://example.com:80', True, 'С портом'),
('http://example.com/path', True, 'С путём'),
('http://example.com/path/to/resource', True, 'С длинным путём'),
('http://example.com?query=value', True, 'С query'),
('http://example.com#fragment', True, 'С фрагментом'),
('http://example.com/path?query=1#frag', True, 'Полный URL'),
('https://sub.domain.example.co.uk', True, 'Поддомены'),
('http://192.168.1.1', True, 'IPv4'),
('http://192.168.1.1:8080/path', True, 'IPv4 с портом и путём'),
('http://a.b.c.d.e.f.g.com', True, 'Много поддоменов'),
('example.com', False, 'Нет схемы'),
('http://', False, 'Только схема'),
('http://.', False, 'Невалидный домен'),
('http://example', False, 'Нет TLD'),
('http://example.c', False, 'TLD слишком короткий'),
('http://example.com:', False, 'Пустой порт'),
('http://example.com:808080', False, 'Порт слишком длинный'),
('mailto:test@example.com', False, 'Неподдерживаемая схема'),
('http://256.256.256.256', False, 'Невалидный IPv4 (но regex пропустит)'),
]
# =============================================================================
# 4. ИНИЦИАЛИЗАЦИЯ
# =============================================================================
print("=" * 80)
print("ТЕСТИРОВАНИЕ URL (OWASP)")
print("=" * 80)
print()
# Компилируем regex
regex_compiled = re.compile(URL_REGEX)
# Создаём Pattern Grammar
pattern = Pattern(URL_GRAMMAR)
# Счётчики
regex_matches = 0
grammar_matches = 0
discrepancies = 0

# 🔧 НОВЫЕ СЧЁТЧИКИ (как в test_url_rfc3986.py)
grammar_vs_expected = 0
regex_vs_expected = 0
grammar_vs_regex = 0

# =============================================================================
# 5. ЗАПУСК ТЕСТОВ
# =============================================================================
results = []
for url, expected, description in TEST_CASES:
    # Тестируем regex
    regex_result = bool(regex_compiled.match(url))

    # Тестируем Pattern Grammar
    try:
        grammar_result = pattern.match('url', url)
    except Exception as e:
        grammar_result = f"ERROR: {e}"

    # Сравниваем regex и grammar между собой
    match_each_other = (regex_result == grammar_result) if isinstance(grammar_result, bool) else False

    # 🔧 НОВЫЕ СРАВНЕНИЯ (как в test_url_rfc3986.py)
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

    if regex_result is not None and isinstance(grammar_result, bool):
        g_vs_r = (grammar_result == regex_result)
        if g_vs_r:
            grammar_vs_regex += 1

    results.append({
        'url': url,
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
    if regex_result:
        regex_matches += 1
    if isinstance(grammar_result, bool) and grammar_result:
        grammar_matches += 1
    if not match_each_other:
        discrepancies += 1

# =============================================================================
# 6. ВЫВОД РЕЗУЛЬТАТОВ
# =============================================================================
print("РЕЗУЛЬТАТЫ ПО ТЕСТАМ:")
print("-" * 120)
header = f"{'URL':<40} {'Ожид.':<6} {'Regex':<8} {'Grammar':<8} {'GvE':<5} {'RvE':<5} {'GvR':<5} {'Описание'}"
print(header)
print("-" * 120)
for r in results:
    # Формируем статусы
    g_vs_e_status = "✅" if r['g_vs_e'] else "❌" if r['g_vs_e'] is False else "?"
    r_vs_e_status = "✅" if r['r_vs_e'] else "❌" if r['r_vs_e'] is False else "?"
    g_vs_r_status = "✅" if r['g_vs_r'] else "❌" if r['g_vs_r'] is False else "?"

    regex_str = str(r['regex'])[:8]
    grammar_str = str(r['grammar'])[:8]
    url_display = r['url'][:37] + '...' if len(r['url']) > 40 else r['url']

    print(f"{url_display:<40} {str(r['expected']):<6} {regex_str:<8} {grammar_str:<8} "
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

# Детальный анализ расхождений
if grammar_errors > 0 or regex_errors > 0 or grammar_regex_diff > 0:
    print("⚠️  НАЙДЕНЫ РАСХОЖДЕНИЯ!")
    print("-" * 80)
    if grammar_errors > 0:
        print("\n📌 Grammar НЕ совпадает с ожиданием:")
        for r in results:
            if r['g_vs_e'] is False:
                print(f"  • {r['url']}: grammar={r['grammar']}, ожидалось={r['expected']}")
                print(f"    → {r['description']}")
    if regex_errors > 0:
        print("\n📌 Regex НЕ совпадает с ожиданием:")
        for r in results:
            if r['r_vs_e'] is False:
                print(f"  • {r['url']}: regex={r['regex']}, ожидалось={r['expected']}")
                print(f"    → {r['description']}")
    if grammar_regex_diff > 0:
        print("\n📌 Grammar и Regex НЕ совпадают между собой:")
        for r in results:
            if r['g_vs_r'] is False:
                print(f"  • {r['url']}: grammar={r['grammar']}, regex={r['regex']}")
                print(f"    → {r['description']}")
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
print("ПРИМЕР ДЕРЕВА РАЗБОРА (https://example.com/path?query=1#frag):")
print("-" * 80)
try:
    tree = pattern.parse('url', 'https://example.com/path?query=1#frag')
    if tree:
        print(tree.pretty())
    else:
        print("Дерево не получено")
except Exception as e:
    print(f"Ошибка: {e}")
print("=" * 80)
