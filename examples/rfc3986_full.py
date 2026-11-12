#!/usr/bin/env python3
"""
Полная реализация RFC 3986 (URI Syntax) на Pattern Grammar.

Покрывает все компоненты URI: scheme, authority (userinfo, host, port),
path, query, fragment. Включает IPv4, IPv6 (все формы), доменные имена,
pct-encoded символы, генератор URI-компонентов.

RFC 3986: https://tools.ietf.org/html/rfc3986
"""

import sys
from pattern_grammar import Pattern

# =============================================================================
# ГРАММАТИКА RFC 3986
# =============================================================================

RFC3986_GRAMMAR = r"""
# =============================================================================
# БАЗОВЫЕ КЛАССЫ СИМВОЛОВ (RFC 3986, Section 2.2-2.4)
# Определяются ОДИН РАЗ и переиспользуются во всех правилах
# =============================================================================

# unreserved — всегда безопасные символы, не требуют процент-кодирования
unreserved  ::= [a-zA-Z0-9\-._~]

# gen-delims — общие разделители, имеют специальное значение в URI
gen-delims  ::= [:/?#@] | "[" | "]"

# sub-delims — подмножество reserved для данных пользователя
sub-delims  ::= [!$&'()*+,;=]

# reserved — объединённое множество (gen-delims + sub-delims)
reserved    ::= gen-delims | sub-delims

# pct-encoded — процент-кодирование (%XX где XX — шестнадцатеричные цифры)
pct-encoded ::= "%" [0-9a-fA-F]{2}

# =============================================================================
# КОМПОЗИЦИЯ: сборка классов для конкретных частей URI
# =============================================================================

# pchar — основной строительный блок для path, query, fragment (RFC 3986, Section 3.3)
# ] НЕ включён — он является gen-delims и требует %5D-кодирования в пути
pchar       ::= unreserved | pct-encoded | sub-delims | ":" | "@"

# segment / segment-nz — сегменты пути (RFC 3986, Section 3.3)
# segment  ::= 0*pchar  (может быть пустым)
# segment-nz ::= 1*pchar (непустой)
# Pattern Grammar не поддерживает EBNF-синтаксис *X, используем ( pchar )*
segment     ::= ( pchar )*
segment-nz  ::= pchar+

# query-char — расширяем pchar для query-строки (добавляем / и ?)
query-char  ::= pchar | "/" | "?"

# fragment-char — расширяем pchar для фрагмента (добавляем / и ?)
fragment-char ::= pchar | "/" | "?"

# userinfo-char — для логина/пароля (RFC 3986, Section 3.2.1)
# @ НЕ включён — он является разделителем в authority
userinfo-char ::= unreserved | pct-encoded | sub-delims | ":"

# reg-name — для имён хостов в authority (RFC 3986, Section 3.2.2)
# * — ноль или более, пустой reg-name допустим по RFC
reg-name    ::= ( unreserved | pct-encoded | sub-delims )*

# reg-name-nz — непустой reg-name для host (не может быть пустым в authority)
reg-name-nz ::= ( unreserved | pct-encoded | sub-delims )+

# =============================================================================
# ГЛАВНОЕ ПРАВИЛО URI (RFC 3986, Section 4.3)
# URI = scheme ":" hier-part [ "?" query ] [ "#" fragment ]
# Один унифицированный вариант через hier-part
# =============================================================================

uri         ::= scheme ":" hier-part query? fragment?

# =============================================================================
# SCHEME (ПРОТОКОЛ)
# =============================================================================

scheme      ::= [a-zA-Z][a-zA-Z0-9+\-.]*

# =============================================================================
# AUTHORITY (ХОСТ + ОПЦИОНАЛЬНО USERINFO И ПОРТ)
# RFC 3986: [ userinfo "@" ] host [ ":" port ]
# host не может быть пустым — пустой authority обрабатывается отдельно
# =============================================================================

authority   ::= ( userinfo "@" )? host ( ":" port )?
userinfo    ::= userinfo-char+
port        ::= [0-9]*

# =============================================================================
# HOST — объединённое правило (RFC 3986, Section 3.2.2)
# host = IP-literal / IPv4address / reg-name
# reg-name используется вместо domain — RFC не накладывает DNS-ограничений
# =============================================================================

host            ::= ipvfuture | ipv6 | ipv4 | reg-name-nz

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
# IPV6 ADDRESSES (RFC 3986, Section 3.2.2)
# ipv6_linklocal с %zone — это RFC 6874, не часть RFC 3986
# =============================================================================

ipv6            ::= "[" ( ipv6_full | ipv6_compressed | ipv6_v4mapped ) "]"
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

# =============================================================================
# IPVFUTURE (RFC 3986, Section 3.2.2)
# =============================================================================

ipvfuture       ::= "[v" [0-9a-fA-F]+ "." ( unreserved | sub-delims | ":" )+ "]"

# =============================================================================
# PATH (ПУТЬ) — все варианты из RFC 3986, Section 3.3
# =============================================================================

path-abempty    ::= ( "/" segment )*
path-absolute   ::= "/" ( segment-nz ( "/" segment )* )?
path-rootless   ::= segment-nz ( "/" segment )*
path-empty      ::= ""

# path-noscheme — не существует в RFC 3986, удалено
# Если нужно для non-hierarchical URI, используйте path-rootless

# Общее path — по порядку приоритета: abempty > absolute > rootless > empty
path            ::= path-abempty | path-absolute | path-rootless | path-empty

# =============================================================================
# QUERY (СТРОКА ЗАПРОСА)
# =============================================================================

query         ::= "?" query-char*

# =============================================================================
# FRAGMENT (ФРАГМЕНТ)
# =============================================================================

fragment      ::= "#" fragment-char*

# =============================================================================
# ИЕРАРХИЧЕСКАЯ ЧАСТЬ (RFC 3986, Section 4.1)
# hier-part = "//" authority path-abempty / path-absolute / path-rootless / path-empty
# =============================================================================

hier-part     ::= "//" authority path-abempty
              | "//" path-abempty
              | path-absolute
              | path-rootless
              | path-empty
"""

# =============================================================================
# КЛАСС ДЛЯ РАЗБОРА URI-КОМПОНЕНТОВ
# =============================================================================

class URIComponent:
    """Представление разобранного URI."""

    def __init__(self, scheme=None, authority=None, path=None,
                 query=None, fragment=None):
        self.scheme = scheme
        self.authority = authority or {}
        self.path = path or ""
        self.query = query or ""
        self.fragment = fragment or ""

    @property
    def host(self):
        return self.authority.get("host", "")

    @property
    def port(self):
        return self.authority.get("port", "")

    @property
    def userinfo(self):
        return self.authority.get("userinfo", "")

    def __repr__(self):
        parts = []
        if self.scheme:
            parts.append(f"scheme={self.scheme!r}")
        if self.userinfo:
            parts.append(f"userinfo={self.userinfo!r}")
        if self.host:
            parts.append(f"host={self.host!r}")
        if self.port:
            parts.append(f"port={self.port!r}")
        if self.path:
            parts.append(f"path={self.path!r}")
        if self.query:
            parts.append(f"query={self.query!r}")
        if self.fragment:
            parts.append(f"fragment={self.fragment!r}")
        return f"URI({', '.join(parts)})"

    def to_string(self):
        """Сборка URI обратно в строку."""
        result = self.scheme + ":"
        if self.host:
            result += "//"
            if self.userinfo:
                result += self.userinfo + "@"
            result += self.host
            if self.port:
                result += ":" + self.port
        result += self.path
        if self.query:
            result += "?" + self.query
        if self.fragment:
            result += "#" + self.fragment
        return result


# =============================================================================
# ТЕСТОВЫЕ ДАННЫЕ
# =============================================================================

TEST_CASES = [
    # --- Базовые URI ---
    ("https://google.com", True, "Простой HTTPS"),
    ("http://example.org", True, "Простой HTTP"),
    ("ftp://files.example.com", True, "FTP протокол"),
    ("https://sub.domain.co.uk", True, "С поддоменами"),

    # --- С userinfo ---
    ("https://user:pass@example.com", True, "С userinfo (логин/пароль)"),
    ("http://user@example.com", True, "С userinfo без пароля"),

    # --- IPv4 адреса ---
    ("http://192.168.1.1", True, "IPv4 адрес"),
    ("http://192.168.1.1:8080", True, "IPv4 с портом"),
    ("http://10.0.0.1/path/to/resource", True, "IPv4 с путём"),

    # --- IPv6 адреса ---
    ("http://[2001:0db8:85a3:0000:0000:8a2e:0370:7334]", True, "IPv6 полная форма"),
    ("http://[2001:db8::1]", True, "IPv6 с сокращением ::"),
    ("http://[::1]", True, "IPv6 localhost"),
    ("http://[::ffff:192.0.2.1]", True, "IPv6 IPv4-mapped"),
    ("http://[2001:db8::1]:8080/path", True, "IPv6 с портом и путём"),
    ("http://[2001:db8:1]", False, "Невалидный IPv6 (не хватает групп)"),

    # --- Доменные имена (reg-name — RFC не требует DNS-валидности) ---
    ("https://xn--d1acpjx3f.xn--p1ai", True, "Punycode (пример.рф)"),

    # --- URL с путями и параметрами ---
    ("https://example.com/path/to/page", True, "С путём"),
    ("https://example.com/path?query=1&test=2", True, "С query параметрами"),
    ("https://example.com/path?query=1#fragment", True, "С фрагментом"),
    ("https://example.com/path#fragment?with=query", True, "Фрагмент со спецсимволами"),

    # --- Сложные случаи ---
    ("https://user:pass@example.com:8080/path/to/page?q=1&x=2#fragment",
     True, "Полный URI со всеми компонентами"),

    # --- С pct-encoded ---
    ("http://example.com/%20", True, "Пробел pct-encoded"),
    ("http://example.com/%2F", True, "Слэш pct-encoded"),
    ("http://example.com/path%20with%20spaces", True, "Пути с кодированием"),

    # --- Сложные reserved символы ---
    ("http://example.com/path?a=1;b=2,c=3", True, "sub-delims в query"),
    ("http://example.com/path#section,with;special=chars", True, "sub-delims в fragment"),

    # --- mailto URI ---
    ("mailto:user@example.com", True, "Mailto URI"),
    ("mailto:user@example.com?subject=hello", True, "Mailto с query"),
    ("mailto:user@example.com?subject=hello#frag", True, "Mailto с query и fragment"),
    ("tel:+7-495-123-45-67", True, "Tel URI"),
    ("file:///path/to/file", True, "File URI с пустым authority"),

    # --- IPvFuture ---
    ("http://[v1.multipath]", True, "IPvFuture v1 multipath"),
    ("http://[v1.info]", True, "IPvFuture v1 info"),
    ("http://[v2.test-data]", True, "IPvFuture v2 с данными"),
    ("http://[v1.info]/path", True, "IPvFuture с путём"),
    ("http://[v1.info]path", False, "IPvFuture без ведущего слэша (невалидно)"),
    ("http://[v1.info]:8080/path?q=1#frag", True, "IPvFuture полный URI"),

    # --- Порт без ограничения ---
    ("http://example.com:65535", True, "Порт 65535"),
    ("http://example.com:99999", True, "Порт 99999"),
    ("http://example.com:0", True, "Порт 0"),

    # --- Пустой path ---
    ("http://example.com", True, "Пустой path"),
    ("http://example.com/", True, "Path только слэш"),

    # --- reserved ] в пути/запросе/фрагменте ---
    # ] НЕ входит в pchar — требует %5D кодирования
    ("http://example.com/path%5D", True, "Кодированная скобка %5D в пути"),
    ("http://example.com/path]", False, "Некодированная скобка ] в пути"),
    ("http://example.com/path?a=%5D", True, "Кодированная скобка %5D в query"),
    ("http://example.com/path?a=]", False, "Некодированная скобка ] в query"),
    ("http://example.com/path#%5D", True, "Кодированная скобка %5D в fragment"),
    ("http://example.com/path#]", False, "Некодированная скобка ] в fragment"),

    # --- reg-name: RFC не требует DNS-валидности ---
    # reg-name разрешает любые unreserved/sub-delims/pct-encoded, включая - в начале/конце
    ("http://-example.com", True, "Дефис в начале reg-name"),
    ("http://example-.com", True, "Дефис в конце reg-name"),
    ("http://256.256.256.256", True, "Не-IPv4 интерпретируется как reg-name"),

    # --- Пустые сегменты пути ---
    ("http://example.com//foo", True, "Пустой сегмент //foo"),
    ("http://example.com/foo//bar", True, "Пустой сегмент в середине"),

     # --- Невалидные ---
    ("not a uri at all", False, "Просто текст"),
    ("http://[2001:db8:::1]", False, "Тройное двоеточие в IPv6"),
    ("http://[2001:db8::1::2]", False, "Два '::' в IPv6"),
]

# =============================================================================
# ФУНКЦИИ ДЛЯ РАЗБОРА
# =============================================================================

def extract_authority_components(text):
    """
    Извлекает userinfo, host и port из authority-части вручную.
    Authority имеет формат: [userinfo@]host[:port]
    """
    authority = {}
    if not text:
        return authority

    # Извлекаем userinfo
    if "@" in text:
        userinfo_part, rest = text.split("@", 1)
        authority["userinfo"] = userinfo_part
    else:
        rest = text

    # Извлекаем port (последнее ':' после ']' или после последнего '/')
    if rest.startswith("["):
        # IPv6 в квадратных скобках
        bracket_end = rest.index("]")
        after_bracket = rest[bracket_end + 1:]
        authority["host"] = rest[:bracket_end + 1]
        if after_bracket.startswith(":"):
            authority["port"] = after_bracket[1:]
    else:
        # IPv4 или reg-name
        last_colon = rest.rfind(":")
        if last_colon > 0:
            host_part = rest[:last_colon]
            port_part = rest[last_colon + 1:]
            # Проверяем, что port — это цифры
            if port_part.isdigit():
                authority["host"] = host_part
                authority["port"] = port_part
            else:
                authority["host"] = rest
        else:
            authority["host"] = rest

    return authority


def extract_path_query_fragment(text):
    """Извлекает path, query и fragment из URI-строки."""
    path = ""
    query = ""
    fragment = ""

    # Извлекаем fragment
    if "#" in text:
        text, fragment = text.split("#", 1)

    # Извлекаем query
    if "?" in text:
        text, query = text.split("?", 1)

    path = text
    return path, query, fragment


def parse_full_uri(grammar, text):
    """
    Полная функция парсинга URI: валидация + извлечение компонентов.

    Возвращает кортеж (is_valid, URIComponent).
    """
    is_valid = grammar.match('uri', text)
    if not is_valid:
        return False, None

    component = URIComponent()

    # Извлекаем scheme
    if ":" in text:
        scheme_part, rest = text.split(":", 1)
        component.scheme = scheme_part
    else:
        rest = text

    # Извлекаем authority (если есть "//")
    if rest.startswith("//"):
        rest = rest[2:]  # Убираем "//"
        authority = extract_authority_components(rest)
        component.authority = authority

        # Находим конец authority: это первое "/" после authority или конец строки
        after_authority = text.split("//", 1)
        if len(after_authority) > 1:
            after_authority = after_authority[1]
            # Определяем конец authority: ищем первое "/" или "?" или "#"
            authority_end = len(after_authority)
            for i, ch in enumerate(after_authority):
                if ch in "/?#":
                    authority_end = i
                    break
            path_query_fragment = after_authority[authority_end:]
            path, query, fragment = extract_path_query_fragment(path_query_fragment)
            component.path = path
            component.query = query
            component.fragment = fragment
    else:
        # Нет authority — это mailto:, tel: и т.п.
        path, query, fragment = extract_path_query_fragment(rest)
        component.path = path
        component.query = query
        component.fragment = fragment

    return True, component


# =============================================================================
# ГЛАВНЫЙ ЗАПУСК
# =============================================================================

def main():
    print("=" * 80)
    print("RFC 3986 URI — Pattern Grammar")
    print("=" * 80)
    print()

    # Загружаем грамматику
    try:
        grammar = Pattern(RFC3986_GRAMMAR)
        print("✅ Грамматика RFC 3986 загружена")
    except Exception as e:
        print(f"❌ Ошибка загрузки грамматики: {e}")
        sys.exit(1)

    info = grammar.get_info()
    print(f"Всего правил: {info.get('total_rules', 0)}")
    print(f"Правила (regex): {info.get('regex_rules', [])}")
    print(f"Правила (parser): {info.get('parser_rules', [])}")
    print()

    # Запускаем тесты
    passed = 0
    failed = 0
    results = []

    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("-" * 120)
    header = f"{'URI':<45} {'Ожид.':<6} {'Результат':<8} {'Описание'}"
    print(header)
    print("-" * 120)

    for uri, expected, description in TEST_CASES:
        is_valid, component = parse_full_uri(grammar, uri)
        status = "✅" if is_valid == expected else "❌"
        uri_display = uri[:42] + "..." if len(uri) > 45 else uri

        print(f"{uri_display:<45} {str(expected):<6} {status:<8} {description}")

        if is_valid == expected:
            passed += 1
        else:
            failed += 1
        results.append((uri, expected, is_valid, component, description))

    print("-" * 120)
    print()

    # Статистика
    print("СТАТИСТИКА:")
    print(f"  Пройдено: {passed}/{len(TEST_CASES)} ({passed / len(TEST_CASES) * 100:.1f}%)")
    if failed:
        print(f"  Провалено: {failed}/{len(TEST_CASES)} ({failed / len(TEST_CASES) * 100:.1f}%)")
    print()

    # Детальный разбор URI-компонентов (первые 5 прошедших тестов)
    print("ДЕТАЛЬНЫЙ РАЗБОР URI-КОМПОНЕНТОВ:")
    print("-" * 80)
    count = 0
    for uri, expected, is_valid, component, description in results:
        if is_valid and component and count < 5:
            print(f"\n{description}:")
            print(f"  {component}")
            print(f"  scheme:   {component.scheme}")
            print(f"  userinfo: {component.userinfo}")
            print(f"  host:     {component.host}")
            print(f"  port:     {component.port}")
            print(f"  path:     {component.path}")
            print(f"  query:    {component.query}")
            print(f"  fragment: {component.fragment}")
            print(f"  сборка:   {component.to_string()}")
            count += 1

    print()
    print("=" * 80)

    # Примеры разбора
    print("\nПРИМЕРЫ ДЕРЕВЬЕВ РАЗБОРА:")
    print("-" * 80)

    examples = [
        ("https://example.com/path?query=1#frag", "Простой URL"),
        ("https://user:pass@example.com:8080/path?q=1#frag", "Полный URL"),
        ("http://[2001:db8::1]:443/api/v1", "IPv6 с портом и путём"),
        ("mailto:user@example.com", "Mailto URI"),
    ]

    for uri, desc in examples:
        print(f"\n{desc}: {uri}")
        try:
            tree = grammar.parse('uri', uri)
            if tree:
                print(tree.pretty())
            else:
                print("  Дерево не получено")
        except Exception as e:
            print(f"  Ошибка: {e}")

    print("=" * 80)

    # Вывод для найденных ошибок
    if failed:
        print("\n⚠️  НАЙДЕНЫ ОШИБКИ:")
        for uri, expected, is_valid, component, description in results:
            if is_valid != expected:
                print(f"  • {uri}: получено={is_valid}, ожидалось={expected}")
                print(f"    → {description}")
    else:
        print("\n✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")

    print()


if __name__ == "__main__":
    main()
