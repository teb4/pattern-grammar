#!/usr/bin/env python3
"""
Тестирование Pattern Grammar на URL (RFC 3986/3987 - ПОЛНЫЙ РЕГЕКС)
Выяснилось при тестировании,  что регекс - неправильный
Сравнение монструозного regex и эквивалента на Pattern Grammar
"""

import sys
import re

# Попробуем импортировать regex-модуль с поддержкой PCRE
try:
    import regex as re
    HAS_REGEX = True
except ImportError:
    HAS_REGEX = False
    print("⚠️ Модуль 'regex' не установлен. Установите: pip install regex")
    print("Без него монструозный regex не скомпилируется.\n")

from pattern_grammar import Pattern

# =============================================================================
# 1. МОНСТРУОЗНЫЙ REGEX (RFC 3986/3987 - ИСПРАВЛЕННАЯ ВЕРСИЯ)
# =============================================================================

URL_MONSTER = re.compile(
    r'^(?:[a-zA-Z][a-zA-Z0-9+\-.]*:)?'  # scheme
    r'(?://'  # authority
        r'(?:[a-zA-Z0-9\-._~!$&\'()*+,;=]+@)?'  # userinfo
        r'(?:'  # host
            # IPv4
            r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
            r'|'
            # IPv6
            r'\[(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}'
            r'|(?:[0-9a-fA-F]{1,4}:){1,7}:'
            r'|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}'
            r'|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}'
            r'|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}'
            r'|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}'
            r'|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}'
            r'|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})'
            r'|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)'
            r'|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]+'
            r'|::(?:ffff(?::0{1,4})?:)?(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
            r'|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
            r'\]'
            r'|'
            # domain name
            r'(?:[a-zA-Z0-9\-._~!$&\'()*+,;=]|%[0-9a-fA-F]{2})+(?:\.(?:[a-zA-Z0-9\-._~!$&\'()*+,;=]|%[0-9a-fA-F]{2})+)*'
        r')'
        r'(?::[0-9]*)?'  # port
    r')?'  # end authority
    r'(?:/(?:[a-zA-Z0-9\-._~!$&\'()*+,;=:@]|%[0-9a-fA-F]{2})*)*'  # path
    r'(?:\?(?:[a-zA-Z0-9\-._~!$&\'()*+,;=:@/?]|%[0-9a-fA-F]{2})*)?'  # query
    r'(?:#(?:[a-zA-Z0-9\-._~!$&\'()*+,;=:@/?]|%[0-9a-fA-F]{2})*)?$'  # fragment
)

# =============================================================================
# 2. ЭКВИВАЛЕНТ НА PATTERN GRAMMAR (ИСПРАВЛЕННАЯ ВЕРСИЯ)
# =============================================================================

URL_GRAMMAR = r"""
url      ::= scheme "://" authority path? query? fragment?

scheme   ::= "http" | "https" | "ftp"  | "file" | "ssh"
           | "git"  | "svn"  | "mailto"| "news" | "irc"
           | "rtsp" | "webcal"

authority ::= userinfo? host port?
userinfo  ::= [^@]+ "@"
host      ::= ipv4 | ipv6 | domain
port      ::= ":" [0-9]{2,5}

domain   ::= label ("." label)*
alnum    ::= [a-zA-Z0-9]
alnumhyp ::= [a-zA-Z0-9-]
label    ::= alnum (alnumhyp* alnum)?

ipv4      ::= dec-octet "." dec-octet "." dec-octet "." dec-octet
dec-octet ::= "25"[0-5]
            | "2"[0-4][0-9]
            | "1"[0-9][0-9]
            | [1-9][0-9]
            | [0-9]

ipv6            ::= "[" ( ipv6_full | ipv6_compressed | ipv6_v4mapped | ipv6_linklocal ) "]"
ipv6_full       ::= hex4 ":" hex4 ":" hex4 ":" hex4 ":"
                    hex4 ":" hex4 ":" hex4 ":" hex4
hex4            ::= [0-9a-fA-F]{1,4}
ipv6_compressed ::= ipv6_start | ipv6_middle | ipv6_end
ipv6_start      ::= "::" (hex4? (":" hex4)*)
ipv6_middle     ::= hex4 "::" hex4? (":" hex4)*
ipv6_end        ::= hex4 (":" hex4)+ "::" hex4?
                  | hex4 (":" hex4)+ "::"
ipv6_v4mapped   ::= "::ffff:" ipv4
ipv6_linklocal  ::= "fe80:" (":" hex4)* "%" [a-zA-Z0-9]+

path_char    ::= [a-zA-Z0-9\-._~!$&'()*+,;=:@%]
path_segment ::= path_char+
path         ::= "/" (path_segment "/")* path_segment?

query_char ::= [a-zA-Z0-9\-._~!$&'()*+,;=:@%?]
query      ::= "?" query_char*

fragment_char ::= [a-zA-Z0-9\-._~!$&'()*+,;=:@%?#]
fragment      ::= "#" fragment_char*
"""

# =============================================================================
# 2. ЭКВИВАЛЕНТ НА PATTERN GRAMMAR (РЕФАКТОРИНГ ПО RFC 3986)
# =============================================================================
URL_GRAMMAR = r"""
# =============================================================================
# БАЗОВЫЕ КЛАССЫ СИМВОЛОВ (RFC 3986, Section 2.2-2.4)
# Определяются ОДИН РАЗ и переиспользуются во всех правилах
# =============================================================================

# unreserved — всегда безопасные символы, не требуют процент-кодирования
unreserved  ::= [a-zA-Z0-9\-._~]

# gen-delims — общие разделители, имеют специальное значение в URL
gen-delims  ::= [:/?#[]@]

# sub-delims — подмножество reserved для данных пользователя
sub-delims  ::= [!$&'()*+,;=]

# reserved — объединённое множество (gen-delims + sub-delims)
reserved    ::= gen-delims | sub-delims

# pct-encoded — процент-кодирование (%XX где XX — шестнадцатеричные цифры)
pct-encoded ::= "%" [0-9a-fA-F]{2}

# =============================================================================
# КОМПОЗИЦИЯ: сборка классов для конкретных частей URL
# Используем альтернативы (|) вместо дублирования символьных классов
# =============================================================================

# pchar — основной строительный блок для path, query, fragment (RFC 3986, Section 3.3)
pchar       ::= unreserved | pct-encoded | sub-delims | ":" | "@"

# query-char — расширяем pchar для query-строки (добавляем / и ?)
query-char  ::= pchar | "/" | "?"

# fragment-char — расширяем pchar для фрагмента (добавляем / ? #)
fragment-char ::= pchar | "/" | "?" | "#"

# userinfo-char — для логина/пароля (исключаем @, так как он разделитель)
userinfo-char ::= unreserved | pct-encoded | sub-delims | ":"

# reg-name — для доменных имён в authority (RFC 3986, Section 3.2)
reg-name    ::= ( unreserved | pct-encoded | sub-delims )+

# =============================================================================
# ГЛАВНОЕ ПРАВИЛО URL
# =============================================================================

url         ::= scheme "://" authority path? query? fragment?

# =============================================================================
# SCHEME (ПРОТОКОЛ)
# =============================================================================

scheme      ::= "http" | "https" | "ftp"  | "file" | "ssh"
              | "git"  | "svn"  | "mailto"| "news" | "irc"
              | "rtsp" | "webcal"

# =============================================================================
# AUTHORITY (ХОСТ + ОПЦИОНАЛЬНО USERINFO И ПОРТ)
# =============================================================================

authority   ::= userinfo? host port?
userinfo    ::= userinfo-char+ "@"
host        ::= ipv4 | ipv6 | domain
port        ::= ":" [0-9]{1,5}

# =============================================================================
# DOMAIN NAMES (ДОМЕННЫЕ ИМЕНА)
# =============================================================================

domain      ::= label ("." label)*
alnum       ::= [a-zA-Z0-9]
alnumhyp    ::= [a-zA-Z0-9-]
label       ::= alnum (alnumhyp* alnum)?

# =============================================================================
# IPV4 ADDRESSES
# =============================================================================

ipv4        ::= dec-octet "." dec-octet "." dec-octet "." dec-octet
dec-octet   ::= "25"[0-5]
              | "2"[0-4][0-9]
              | "1"[0-9][0-9]
              | [1-9][0-9]
              | [0-9]

# =============================================================================
# IPV6 ADDRESSES (ВСЕ ФОРМЫ)
# =============================================================================

ipv6            ::= "[" ( ipv6_full | ipv6_compressed | ipv6_v4mapped | ipv6_linklocal ) "]"
hex4            ::= [0-9a-fA-F]{1,4}

# Полная форма (8 групп по 4 шестнадцатеричных цифры)
ipv6_full       ::= hex4 ":" hex4 ":" hex4 ":" hex4 ":"
                    hex4 ":" hex4 ":" hex4 ":" hex4

# Сжатая форма с :: (все варианты расположения)
ipv6_compressed ::= ipv6_start | ipv6_middle | ipv6_end
ipv6_start      ::= "::" (hex4? (":" hex4)*)
ipv6_middle     ::= hex4 "::" hex4? (":" hex4)*
ipv6_end        ::= hex4 (":" hex4)+ "::" hex4?
                  | hex4 (":" hex4)+ "::"

# Специальные формы IPv6
ipv6_v4mapped   ::= "::ffff:" ipv4
ipv6_linklocal  ::= "fe80:" (":" hex4)* "%" [a-zA-Z0-9]+

# =============================================================================
# PATH (ПУТЬ)
# Используем композицию pchar вместо монолитного [a-zA-Z0-9\-._~!$&'()*+,;=:@%]
# =============================================================================

path-segment  ::= pchar+
path          ::= "/" (path-segment "/")* path-segment?

# =============================================================================
# QUERY PARAMETERS (СТРОКА ЗАПРОСА)
# Используем композицию query-char
# =============================================================================

query         ::= "?" query-char*

# =============================================================================
# FRAGMENT (ФРАГМЕНТ)
# Используем композицию fragment-char
# =============================================================================

fragment      ::= "#" fragment-char*
"""

# =============================================================================
# 3. ТЕСТОВЫЕ ДАННЫЕ
# =============================================================================
TEST_CASES = [
    # Базовые URL
    ('https://google.com', True, 'Простой HTTPS'),
    ('http://example.org', True, 'Простой HTTP'),
    ('ftp://files.example.com', True, 'FTP протокол'),
    ('https://sub.domain.co.uk', True, 'С поддоменами'),

    # IPv4 адреса
    ('http://192.168.1.1', True, 'IPv4 адрес'),
    ('http://192.168.1.1:8080', True, 'IPv4 с портом'),
    ('http://256.256.256.256', False, 'Невалидный IPv4 (числа >255)'),
    #('http://256.256.256.256', True, 'Валидный hostname (выглядит как IPv4, но это домен)'),

    # IPv6 адреса
    ('http://[2001:0db8:85a3:0000:0000:8a2e:0370:7334]', True, 'IPv6 полная форма'),
    ('http://[2001:db8::1]', True, 'IPv6 с сокращением ::'),
    ('http://[::1]', True, 'IPv6 localhost'),
    ('http://[::ffff:192.0.2.1]', True, 'IPv6 IPv4-mapped'),
    ('http://[fe80::1%eth0]', True, 'IPv6 link-local с зоной'),
    ('http://[2001:db8:1]', False, 'Невалидный IPv6 (не хватает групп)'),

    # Интернациональные домены
    ('https://xn--d1acpjx3f.xn--p1ai', True, 'Punycode (пример.рф)'),

    # URL с путями и параметрами
    ('https://example.com/path/to/page', True, 'С путём'),
    ('https://example.com/path?query=1&test=2', True, 'С query параметрами'),
    ('https://example.com/path?query=1#fragment', True, 'С фрагментом'),
    ('https://example.com/path#fragment?with=query', True, 'Фрагмент со спецсимволами'),

    # Сложные случаи
    ('https://user:pass@example.com', True, 'С userinfo (логин/пароль)'),
    ('https://example.com:8080', True, 'С портом'),
    ('https://example.com/path?query#fragment', True, 'Полный URL со всем'),

    # Невалидные
    ('not a url', False, 'Просто текст'),
    ('http://', False, 'Пустой хост'),
    ('http://.com', False, 'Точка в начале домена'),
    ('http://example..com', False, 'Две точки в домене'),
    ('http://-example.com', False, 'Дефис в начале'),
    ('http://example-.com', False, 'Дефис в конце'),
]

# =============================================================================
# 4. ИНИЦИАЛИЗАЦИЯ
# =============================================================================
print("=" * 80)
print("ТЕСТИРОВАНИЕ URL (RFC 3986/3987 - ПОЛНЫЙ РЕГЕКС)")
print("=" * 80)
print()

# Компилируем монструозный regex
regex_compiled = None
if HAS_REGEX:
    try:
        regex_compiled = URL_MONSTER
        print("✅ Монструозный regex скомпилирован (модуль regex)")
    except Exception as e:
        print(f"❌ Ошибка компиляции regex: {e}")
        regex_compiled = None
else:
    print("❌ Модуль regex не доступен - сравнение с монстром невозможно")

# Создаём Pattern Grammar
try:
    pattern = Pattern(URL_GRAMMAR)
    print("✅ Pattern Grammar успешно загружена")
except Exception as e:
    print(f"❌ Ошибка загрузки грамматики: {e}")
    sys.exit(1)

print("\n" + "=" * 80 + "\n")

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
for url, expected, description in TEST_CASES:
    # Тестируем regex
    regex_result = None
    if regex_compiled:
        regex_result = bool(regex_compiled.match(url))
        if regex_result:
            regex_matches += 1

    # Тестируем Pattern Grammar
    try:
        grammar_result = pattern.match('url', url)
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
        'url': url,
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
header = f"{'URL':<40} {'Ожид.':<6} {'Regex':<8} {'Grammar':<8} {'GvE':<5} {'RvE':<5} {'GvR':<5} {'Описание'}"
print(header)
print("-" * 120)

for r in results:
    # Формируем статусы
    g_vs_e_status = "✅" if r['g_vs_e'] else "❌" if r['g_vs_e'] is False else "?"
    r_vs_e_status = "✅" if r['r_vs_e'] else "❌" if r['r_vs_e'] is False else "?"
    g_vs_r_status = "✅" if r['g_vs_r'] else "❌" if r['g_vs_r'] is False else "?"

    regex_str = str(r['regex'])[:8] if r['regex'] is not None else "N/A"
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
if regex_compiled:
    print(f"  Regex с ожиданием:              {regex_vs_expected}/{len(TEST_CASES)} ({regex_vs_expected/len(TEST_CASES)*100:.1f}%)")
    print(f"  Grammar с Regex:                {grammar_vs_regex}/{len(TEST_CASES)} ({grammar_vs_regex/len(TEST_CASES)*100:.1f}%)")
print()

print("РАСХОЖДЕНИЯ:")
grammar_errors = len(TEST_CASES) - grammar_vs_expected
print(f"  Grammar с ожиданием:            {grammar_errors}")

if regex_compiled:
    regex_errors = len(TEST_CASES) - regex_vs_expected
    grammar_regex_diff = len(TEST_CASES) - grammar_vs_regex
    print(f"  Regex с ожиданием:              {regex_errors}")
    print(f"  Grammar с Regex:                {grammar_regex_diff}")

print("-" * 80)
print()

if regex_compiled:
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
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Pattern Grammar полностью совместим с монструозным regex")
else:
    print("ℹ️  Тестирование только Pattern Grammar")
    print(f"   Pattern Grammar правильно распознал {grammar_vs_expected}/{len(TEST_CASES)} URL ({grammar_vs_expected/len(TEST_CASES)*100:.1f}%)")

    if grammar_errors > 0:
        print("\n📌 Ошибки Pattern Grammar:")
        for r in results:
            if r['g_vs_e'] is False:
                print(f"  • {r['url']}: получено={r['grammar']}, ожидалось={r['expected']}")
                print(f"    → {r['description']}")

print()
print("=" * 80)

# =============================================================================
# 8. ИНФОРМАЦИЯ О ГРАММАТИКЕ
# =============================================================================
print("\nИНФОРМАЦИЯ О ГРАММАТИКЕ:")
print("-" * 80)
info = pattern.get_info()
print(f"Всего правил: {info.get('total_rules', 0)}")
print(f"Правила (regex): {info.get('regex_rules', [])}")
print(f"Правила (parser): {info.get('parser_rules', [])}")
print()

# =============================================================================
# 9. ПРИМЕР ДЕРЕВА РАЗБОРА
# =============================================================================
print("ПРИМЕР ДЕРЕВА РАЗБОРА (сложный URL):")
print("-" * 80)
try:
    tree = pattern.parse('url', 'https://user:pass@[2001:db8::1]:8080/path?query=1#fragment')
    if tree:
        print(tree.pretty())
    else:
        print("Дерево не получено")
except Exception as e:
    print(f"Ошибка: {e}")
print("=" * 80)

# =============================================================================
# 10. ИНСТРУКЦИЯ
# =============================================================================
if not HAS_REGEX:
    print("\n📦 Для полного теста с монструозным regex установите модуль 'regex':")
    print("    pip install regex")
    print("    Затем запустите тест снова")
