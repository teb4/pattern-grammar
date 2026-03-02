#!/usr/bin/env python3
"""
Проверка примеров из README.ru.md
Запускает код примеров и сверяет вывод с ожидаемым.
"""
import sys
from pattern_grammar import Pattern, match, parse


def check_example_1():
    """Пример 1: Простая валидация email"""
    print("📧 Пример 1 (email валидация)... ", end="", flush=True)

    pattern = Pattern("""
        email ::= username "@" domain "." tld
        username ::= [a-zA-Z0-9._%+-]+
        domain ::= [a-zA-Z0-9.-]+
        tld ::= [a-zA-Z]{2,}
    """)

    r1 = pattern.match('email', 'test@example.com')  # True
    r2 = pattern.match('email', 'invalid')           # False

    if r1 is True and r2 is False:
        print("✅ ОК")
        return True
    else:
        print(f"❌ FAIL (got: {r1}, {r2})")
        return False


def check_example_2():
    """Пример 2: Математические выражения (рекурсия)"""
    print("🔢 Пример 2 (мат. выражения)... ", end="", flush=True)

    pattern = Pattern("""
        expr ::= term (("+" | "-") term)*
        term ::= factor (("*" | "/") factor)*
        factor ::= NUMBER | "(" expr ")"
        NUMBER ::= [0-9]+
    """)

    r1 = pattern.match('expr', '2 + 3 * 4')        # True
    r2 = pattern.match('expr', '2 + (3 * 4)')      # True
    r3 = pattern.match('expr', '(2 + 3) * 4')      # True
    tree = pattern.parse('expr', '2 + 3 * 4')      # не None

    if all([r1, r2, r3]) and tree is not None and hasattr(tree, 'pretty'):
        print("✅ ОК")
        return True
    else:
        print(f"❌ FAIL (matches: {r1},{r2},{r3}, tree: {tree})")
        return False


def check_example_3():
    """Пример 3: Валидация дат"""
    print("📅 Пример 3 (даты)... ", end="", flush=True)

    pattern = Pattern("""
        date ::= year "-" month "-" day
        year ::= [0-9]{4}
        month ::= "0"[1-9] | "1"[0-2]
        day ::= "0"[1-9] | [12][0-9] | "3"[01]
    """)

    r1 = pattern.match('date', '2024-01-15')  # True
    r2 = pattern.match('date', '2024-12-31')  # True
    r3 = pattern.match('date', '2024-13-01')  # False (невалидный месяц)

    if r1 is True and r2 is True and r3 is False:
        print("✅ ОК")
        return True
    else:
        print(f"❌ FAIL (got: {r1}, {r2}, {r3})")
        return False


def check_example_4():
    """Пример 4: Валидация URL"""
    print("🌐 Пример 4 (URL)... ", end="", flush=True)

    pattern = Pattern(r"""
        url      ::= scheme "://" authority path? query? fragment?

        scheme   ::= "http" | "https" | "ftp" | "file" | "ssh"
                | "git" | "svn" | "mailto" | "news" | "irc"
                | "rtsp" | "webcal"

        authority ::= userinfo? host port?
        userinfo  ::= [^@]+ "@"
        host      ::= ipv4 | ipv6 | domain
        port      ::= ":" [0-9]{2,5}

        domain   ::= label ("." label)*
        label    ::= [a-zA-Z0-9] ([a-zA-Z0-9-]* [a-zA-Z0-9])?

        ipv4      ::= dec-octet "." dec-octet "." dec-octet "." dec-octet
        dec-octet ::= "25"[0-5]
                    | "2"[0-4][0-9]
                    | "1"[0-9][0-9]
                    | [1-9][0-9]
                    | [0-9]

        path     ::= "/" (path_segment "/")* path_segment?
        path_segment ::= [a-zA-Z0-9\-._~!$&'()*+,;=:@%]+

        query    ::= "?" [a-zA-Z0-9\-._~!$&'()*+,;=:@%?]*
        fragment ::= "#" [a-zA-Z0-9\-._~!$&'()*+,;=:@%?#]*
    """)

    r1 = pattern.match('url', 'https://example.com/path?q=1')  # True
    r2 = pattern.match('url', 'http://192.168.1.1:8080')       # True
    r3 = pattern.match('url', 'not a url')                     # False

    if r1 is True and r2 is True and r3 is False:
        print("✅ ОК")
        return True
    else:
        print(f"❌ FAIL (got: {r1}, {r2}, {r3})")
        return False


def check_quick_functions():
    """Проверка быстрых функций match/parse"""
    print("⚡ Быстрые функции (match/parse)... ", end="", flush=True)

    # Быстрая проверка (regex-бэкенд)
    r1 = match("""
        email ::= [a-z]+@[a-z]+\.[a-z]{2,}
    """, 'email', 'test@example.com')  # True

    # Быстрый парсинг (нужна рекурсия для Lark-бэкенда)
    tree = parse("""
        expr   ::= term (("+" | "-") term)*
        term   ::= factor (("*" | "/") factor)*
        factor ::= NUMBER | "(" expr ")"
        NUMBER ::= [0-9]+
    """, 'expr', '1 + 2 + 3')  # не None

    if r1 is True and tree is not None and hasattr(tree, 'pretty'):
        print("✅ ОК")
        return True
    else:
        print(f"❌ FAIL (match: {r1}, parse tree: {tree})")
        return False


def check_findall():
    """Проверка findall"""
    print("🔍 findall... ", end="", flush=True)

    pattern = Pattern('hashtag ::= "#" [a-z0-9_]+')
    text = "This is #test post with #multiple #hashtags"  # латиница для надёжности
    result = pattern.findall('hashtag', text)

    # Возвращается полное совпадение, включая "#"
    expected = {'#test', '#multiple', '#hashtags'}
    if set(result) == expected:
        print("✅ ОК")
        return True
    else:
        print(f"❌ FAIL (got: {result}, expected: {expected})")
        return False


def check_get_info():
    """Проверка get_info"""
    print("ℹ️  get_info... ", end="", flush=True)

    pattern = Pattern("""
        email ::= username "@" domain "." tld
        username ::= [a-z]+
        domain ::= [a-z]+
        tld ::= [a-z]{2,}
        expr ::= term (("+" | "-") term)*
        term ::= factor (("*" | "/") factor)*
        factor ::= NUMBER | "(" expr ")"
        NUMBER ::= [0-9]+
    """)

    info = pattern.get_info()

    if isinstance(info, dict) and 'regex_rules' in info and 'parser_rules' in info:
        # email, username, domain, tld должны быть в regex (нерекурсивные)
        # expr, term, factor должны быть в parser (рекурсивные)
        if 'email' in info['regex_rules'] and 'expr' in info['parser_rules']:
            print("✅ ОК")
            return True

    print(f"❌ FAIL (info: {info})")
    return False


def check_multiline_rules():
    """Проверка многострочных правил"""
    print("📝 Многострочные правила... ", end="", flush=True)

    pattern = Pattern("""
        scheme ::= "http" | "https" | "ftp" | "file" | "ssh"
                 | "git" | "svn" | "mailto" | "news" | "irc"
                 | "rtsp" | "webcal"
    """)

    r1 = pattern.match('scheme', 'http')    # True
    r2 = pattern.match('scheme', 'https')   # True
    r3 = pattern.match('scheme', 'invalid') # False

    if r1 is True and r2 is True and r3 is False:
        print("✅ ОК")
        return True
    else:
        print(f"❌ FAIL (got: {r1}, {r2}, {r3})")
        return False


def main():
    print("🧪 Проверка примеров из README.ru.md\n")

    checks = [
        check_example_1,           # Email валидация
        check_example_2,           # Мат. выражения
        check_example_3,           # Даты
        check_example_4,           # URL
        check_quick_functions,     # Быстрые функции
        check_findall,             # findall
        check_get_info,            # get_info
        check_multiline_rules,     # Многострочные правила
    ]

    results = [fn() for fn in checks]

    print(f"\n{'='*50}")
    passed = sum(results)
    total = len(results)

    if all(results):
        print(f"🎉 Все {total} примеров работают корректно!")
        print("✅ README готов к публикации на GitHub")
        return 0
    else:
        print(f"⚠️  Пройдено: {passed}/{total}")
        print("❌ Некоторые примеры НЕ работают — исправьте README перед публикацией!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
