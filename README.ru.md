# Pattern Grammar

**Читаемые паттерны вместо регулярных выражений**

---

## 🤖 Скилл для LLM

В проекте есть **скилл для LLM-агентов** — руководство по замене regex на pattern grammar.
При работе с этим репозиторием, если нужно конвертировать regex → pattern grammar,
сначала прочитайте скилл: **[docs/knowledge-base/skills/use-pattern-grammar-for-regex.md](docs/knowledge-base/skills/use-pattern-grammar-for-regex.md)**

---

## 🎯 Что это?

`pattern-grammar` — это библиотека для описания паттернов в понятном человеку виде.

Вместо непонятной регулярки:
```python
pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
```

Пишите читаемую грамматику:
```bnf
email ::= username "@" domain "." tld
username ::= [a-zA-Z0-9._%+-]+
domain ::= [a-zA-Z0-9.-]+
tld ::= [a-zA-Z]{2,}
```

---

## 📦 Установка

### Локальная установка (для разработки)

```bash
# Клонируем репозиторий
git clone https://github.com/teb4/pattern-grammar.git
cd pattern-grammar

# Установка в режиме разработки
pip install -e .

# Или просто установка зависимостей
pip install -r requirements.txt
```

---

## 🚀 Быстрый старт

### Пример 1: Простая валидация

```python
from pattern_grammar import Pattern

# Определяем паттерн
pattern = Pattern("""
    email ::= username "@" domain "." tld
    username ::= [a-zA-Z0-9._%+-]+
    domain ::= [a-zA-Z0-9.-]+
    tld ::= [a-zA-Z]{2,}
""")

# Проверяем
print(pattern.match('email', 'test@example.com'))  # True
print(pattern.match('email', 'invalid'))           # False
```

### Пример 2: Сложная структура (рекурсия)

```python
pattern = Pattern("""
    expr ::= term (("+" | "-") term)*
    term ::= factor (("*" | "/") factor)*
    factor ::= NUMBER | "(" expr ")"
    NUMBER ::= [0-9]+
""")

print(pattern.match('expr', '2 + 3 * 4'))        # True
print(pattern.match('expr', '2 + (3 * 4)'))      # True
print(pattern.match('expr', '(2 + 3) * 4'))      # True

# Получаем дерево разбора
tree = pattern.parse('expr', '2 + 3 * 4')
print(tree.pretty())
```

---

## 📖 Синтаксис

### Основные конструкции

```bnf
# Определение правила
<имя> ::= <тело>

# Альтернатива
expr ::= term | expr "+" term

# Группировка
group ::= "(" expr ")"

# Повторение
list ::= item ("," item)*

# Опциональность
optional ::= prefix? item

# Диапазоны
pin ::= digit{4}
byte ::= digit{1,3}
```

### Многострочные правила

Длинные правила можно разбивать на несколько строк для лучшей читаемости. Строки с отступом считаются продолжением предыдущего правила:

```bnf
# Альтернативы на отдельных строках
scheme ::= "http" | "https" | "ftp"  | "file" | "ssh"
         | "git"  | "svn"  | "mailto"| "news" | "irc"
         | "rtsp" | "webcal"

# Последовательность на нескольких строках
ipv6_full ::= hex4 ":" hex4 ":" hex4 ":" hex4 ":"
              hex4 ":" hex4 ":" hex4 ":" hex4

# Альтернативы с выравниванием
dec-octet ::= "25"[0-5]
            | "2"[0-4][0-9]
            | "1"[0-9][0-9]
            | [1-9][0-9]
            | [0-9]
```

> **Правило:** строка является продолжением предыдущего правила, если она начинается с пробела или таба и не содержит `::=`.


### Комментарии

Комментарии начинаются с `#` и могут быть размещены на отдельной строке или inline в конце строки с правилом. Парсер корректно игнорирует символы `#` внутри строковых литералов и символьных классов.

```bnf
# ✅ Правильно: комментарий на отдельной строке
email ::= username "@" domain "." tld

# ✅ Правильно: inline-комментарий
username ::= [a-z]+    # определение имени пользователя
domain   ::= [a-z]+    # определение домена
```

### Исключение

Символ # можно использовать внутри строковых литералов и символьных классов — он будет сохранён как часть правила:

```bnf
# ✅ Корректно: # внутри строки
comment_line ::= "#" [a-zA-Z]+

# ✅ Корректно: # в символьном классе
hex_color ::= "#" [0-9a-fA-F]{6}

# ✅ Корректно: # в строковом литерале
python_comment ::= "#" [^\n]*
```

Если вам нужно, чтобы правило заканчивалось символом # (например, для hex-цветов), просто включите его в правило явно, как показано выше.

### Символьные классы

Синтаксис символьных классов такой же, как в регулярных выражениях:

```bnf
# Буквы
alpha ::= [a-z]
alpha ::= [a-zA-Z]

# Цифры
digit ::= [0-9]
digit ::= \d

# Буквы и цифры
alnum ::= [a-zA-Z0-9]

# Любой символ
any ::= .

# Отрицание
not_digit ::= [^0-9]
```

### Литералы кавычек

Для обозначения символа кавычки в литерале используйте **противоположный тип кавычек**:

```bnf
# Литерал двойной кавычки — оборачиваем в одинарные
string ::= '"' chars '"'

# Литерал одинарной кавычки — оборачиваем в двойные
quoted ::= "'" chars "'"
```

Альтернатива — символьный класс `["]` или `[']`:

```bnf
string ::= ["] chars ["]
```

> ⚠️ **Важно:** синтаксис `"\""` (экранированная кавычка внутри того же типа кавычек) **не поддерживается**. Это сделано намеренно — экранирование внутри Python-строк делает грамматику нечитаемой, что противоречит цели библиотеки.

### Встроенные классы

Для удобства доступны предопределённые классы:

```bnf
digit       ::= [0-9]          # Одна цифра
digits      ::= [0-9]+         # Одна или более цифр
alpha       ::= [a-zA-Z]       # Одна буква
alnum       ::= [a-zA-Z0-9]    # Буква или цифра
word        ::= [a-zA-Z0-9_]+  # Слово
whitespace  ::= \s             # Пробельный символ
```

### Сообщения об ошибках с `@fail`

Прикрепите к любому правилу пользовательское сообщение об ошибке через `@fail`. Сообщение будет выброшено как `PatternError`, если текст **не** соответствует правилу:

```bnf
email ::= [a-z]+ "@" [a-z]+ ".com" @fail "неверный email"
```

```python
pattern.match('email', 'user@example.com')   # True
# pattern.match('email', 'invalid')          # raises PatternError: неверный email
```

### Импорт внешних грамматик

Переиспользуйте правила из встроенных библиотек или внешних `.pg` файлов:

```bnf
import "rfc3986-core.pg"

url ::= scheme "://" authority path? query? fragment?
```

Поддерживаемые формы импорта:

| Синтаксис | Описание |
|-----------|----------|
| `import "rfc3986-core.pg"` | Встроенная библиотека |
| `import "./common.pg"` | Относительный путь (относительно вызывающего файла) |
| `import "/abs/path.pg"` | Абсолютный путь |

---

## 🔍 API

### `Pattern(grammar_text: str)`

Создаёт паттерн из текста грамматики.

```python
pattern = Pattern("""
    email ::= username "@" domain "." tld
    username ::= [a-z]+
    domain ::= [a-z]+
    tld ::= [a-z]{2,}
""")
```

### `pattern.match(rule_name: str, text: str) -> bool`

Проверяет, соответствует ли текст правилу.

```python
pattern.match('email', 'test@example.com')  # True
pattern.match('email', 'invalid')           # False
```

### `pattern.parse(rule_name: str, text: str) -> Tree | None`

Парсит текст и возвращает дерево разбора (AST).

```python
tree = pattern.parse('expr', '2 + 3 * 4')
print(tree.pretty())
```

### `pattern.findall(rule_name: str, text: str) -> List[str]`

Находит все совпадения в тексте (только для нерекурсивных правил).

```python
pattern = Pattern('hashtag ::= "#" [a-z0-9_]+')
text = "Это #тестовый пост с #несколькими #хештегами"
pattern.findall('hashtag', text)
# ['#тестовый', '#несколькими', '#хештегами']
```

### `pattern.get_info() -> dict`

Возвращает информацию о грамматике.

```python
info = pattern.get_info()
print(info)
```

### `pattern.generate(rule_name: str, count: int = 1, max_depth: int = 20) -> List[str]`

Генерирует случайные строки, соответствующие правилу:

```python
pattern = Pattern("""
    digit   ::= [0-9]
    pin     ::= digit{4}
""")

print(pattern.generate('pin'))         # "3847"
print(pattern.generate('pin', count=5)) # ["1234", "5678", ...]
```

### Быстрые функции

```python
from pattern_grammar import match, parse

# Быстрая проверка
result = match("""
    email ::= [a-z]+@[a-z]+\.[a-z]{2,}
""", 'email', 'test@example.com')

# Быстрый парсинг
tree = parse("""
    expr ::= term (("+"|"-") term)*
    term ::= factor (("*"|"/") factor)*
    factor ::= NUMBER | "(" expr ")"
""", 'expr', '1 + 2 + 3')
```

---

## 🧠 Как это работает?

### Автоматический выбор метода

Библиотека **автоматически** определяет, как реализовать каждое правило:

| Тип правила | Реализация | Почему |
|-------------|------------|--------|
| **Нерекурсивное** | Регулярное выражение | Быстро и эффективно |
| **Рекурсивное** | Lark парсер | Поддерживает вложенность |

```python
pattern = Pattern("""
    # Нерекурсивные → быстрые регулярки
    email ::= username "@" domain "." tld
    username ::= [a-z]+
    
    # Рекурсивные → полноценный парсер
    expr ::= term (("+"|"-") term)*
    term ::= factor (("*"|"/") factor)*
    factor ::= NUMBER | "(" expr ")"
""")

# Смотрим, что использовано
print(pattern.get_info())
# {
#   'regex_rules': ['email', 'username', ...],
#   'parser_rules': ['expr', 'term', 'factor']
# }
```

---

## 📚 Примеры

### Пример 1: Валидация email

```python
from pattern_grammar import Pattern

pattern = Pattern("""
    email    ::= username "@" domain "." tld
    username ::= [a-zA-Z0-9._%+-]+
    domain   ::= [a-zA-Z0-9.-]+
    tld      ::= [a-zA-Z]{2,}
""")

tests = [
    'test@example.com',
    'user.name+tag@sub.domain.co.uk',
    'invalid-email',
    '@example.com',
]

for test in tests:
    result = pattern.match('email', test)
    print(f"{test:40} -> {result}")
```

### Пример 2: Математические выражения

```python
pattern = Pattern("""
    expr   ::= term (("+" | "-") term)*
    term   ::= factor (("*" | "/") factor)*
    factor ::= NUMBER | "(" expr ")"
    NUMBER ::= [0-9]+
""")

expressions = [
    '2 + 3',
    '2 + 3 * 4',
    '2 + (3 * 4)',
    '(2 + 3) * 4',
    '10 / 2 + 3',
    '2 +',  # Невалидное
]

for expr in expressions:
    result = pattern.match('expr', expr)
    print(f"{expr:20} -> {result}")
```

### Пример 3: Валидация дат

```python
pattern = Pattern("""
    date  ::= year "-" month "-" day
    year  ::= [0-9]{4}
    month ::= "0"[1-9] | "1"[0-2]
    day   ::= "0"[1-9] | [12][0-9] | "3"[01]
""")

dates = [
    '2024-01-15',
    '2024-12-31',
    '2024-02-29',
    '2024-13-01',  # Невалидный месяц
]

for date in dates:
    result = pattern.match('date', date)
    print(f"{date} -> {result}")
```

### Пример 4: Валидация URL (многострочная грамматика)

Многострочный синтаксис особенно полезен для сложных грамматик:

```python
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

print(pattern.match('url', 'https://example.com/path?q=1'))   # True
print(pattern.match('url', 'http://192.168.1.1:8080'))        # True
print(pattern.match('url', 'not a url'))                      # False
```

### Пример 5: URL валидация — Regex против Grammar

Сравните, как выглядят сложные паттерны на regex и на Pattern Grammar:

#### Regex (взят из Сети. 44 строки ада — попробуйте это прочитать!):

```python
# Монструозный regex для URL (RFC 3986/3987)
URL_MONSTER = re.compile(
    r'^(?:[a-zA-Z][a-zA-Z0-9+\-.]*:)?'  # scheme
    r'(?://'  # authority
        r'(?:[a-zA-Z0-9\-._~!$&\'()*+,;=]+@)?'  # userinfo
        r'(?:'  # host
            # IPv4
            r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
            r'|'
            # IPv6 — 15 строк кошмара!
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
```

#### Pattern Grammar (полная грамматика URL):

```bnf
# Основное правило
url ::= scheme "://" authority path? query? fragment?

# Схема (протокол)
scheme ::= "http" | "https" | "ftp"  | "file" | "ssh"
         | "git"  | "svn"  | "mailto"| "news" | "irc"
         | "rtsp" | "webcal"

# Authority (хост + опционально пользователь и порт)
authority ::= userinfo? host port?
userinfo  ::= [^@]+ "@"
host      ::= ipv4 | ipv6 | domain
port      ::= ":" [0-9]{2,5}

# Доменные имена
domain   ::= label ("." label)*
alnum    ::= [a-zA-Z0-9]
alnumhyp ::= [a-zA-Z0-9-]
label    ::= alnum (alnumhyp* alnum)?

# IPv4 адреса
ipv4      ::= dec-octet "." dec-octet "." dec-octet "." dec-octet
dec-octet ::= "25"[0-5]     # 250-255
            | "2"[0-4][0-9] # 200-249
            | "1"[0-9][0-9] # 100-199
            | [1-9][0-9]    # 10-99
            | [0-9]          # 0-9

# IPv6 адреса (все формы)
ipv6            ::= "[" ( ipv6_full | ipv6_compressed | ipv6_v4mapped | ipv6_linklocal ) "]"
hex4            ::= [0-9a-fA-F]{1,4}

# Полная форма (8 групп)
ipv6_full       ::= hex4 ":" hex4 ":" hex4 ":" hex4 ":"
                    hex4 ":" hex4 ":" hex4 ":" hex4

# Сжатая форма с :: (все варианты)
ipv6_compressed ::= ipv6_start | ipv6_middle | ipv6_end
ipv6_start      ::= "::" (hex4? (":" hex4)*)
ipv6_middle     ::= hex4 "::" hex4? (":" hex4)*
ipv6_end        ::= hex4 (":" hex4)+ "::" hex4?
                  | hex4 (":" hex4)+ "::"

# Специальные формы IPv6
ipv6_v4mapped   ::= "::ffff:" ipv4
ipv6_linklocal  ::= "fe80:" (":" hex4)* "%" [a-zA-Z0-9]+

# Путь
path_char    ::= [a-zA-Z0-9\-._~!$&'()*+,;=:@%]
path_segment ::= path_char+
path         ::= "/" (path_segment "/")* path_segment?

# Query параметры
query_char ::= [a-zA-Z0-9\-._~!$&'()*+,;=:@%?]
query      ::= "?" query_char*

# Фрагмент
fragment_char ::= [a-zA-Z0-9\-._~!$&'()*+,;=:@%?#]
fragment      ::= "#" fragment_char*
```

### К тому же, как оказалось, regex не вполне правильный.

#### Что пропустил regex:

    ❌ Все IPv6 адреса (кроме полной формы)

        http://[2001:db8::1] — IPv6 с сокращением

        http://[::1] — IPv6 localhost

        http://[::ffff:192.0.2.1] — IPv4-mapped

        http://[fe80::1%eth0] — IPv6 с зоной

    ❌ http:// — пустой хост

    ❌ http://.com — точка в начале домена

    ❌ http://example..com — две точки в домене

    ❌ http://-example.com — дефис в начале

    ❌ http://example-.com — дефис в конце

#### Где ошиблась Pattern Grammar:

    ⚠️ http://256.256.256.256 — помечен как валидный, хотя это невалидный IPv4 (но может быть валидным доменным именем!)

> **Вывод:** Regex не подходит для сложных форматов - он слишком запутан в таких случаях. Pattern Grammar можно понять, отладить и поддерживать.


### Кроме того, можно сделать вариант длиннее, но более соответствующий терминологии стандарта и пригодный для дальнейшего расширения:

```bnf
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
```

---

## 🧪 Запуск примеров

### Запуск примеров

```bash
# Пример валидации email
python examples/email_validation.py

# Пример математических выражений
python examples/math_expressions.py

# Пример валидации дат
python examples/date_validation.py
```

---

## 🆚 Сравнение с регулярными выражениями

| Аспект | Регулярные выражения | Pattern Grammar |
|--------|---------------------|-----------------|
| **Простые паттерны** | ✅ Лаконично | ✅ Эквивалентно |
| **Сложные паттерны** | ❌ Ад | ✅ Структурировано |
| **Читаемость** | ❌ Плохая | ✅ Отличная |
| **Многострочность** | ❌ Не поддерживается | ✅ Встроена |
| **Поддержка** | ❌ Трудно | ✅ Легко |
| **Тестирование** | ❌ Всё или ничего | ✅ По частям |
| **Рекурсия** | ❌ Невозможно | ✅ Поддерживается |
| **Документация** | ❌ Отдельно | ✅ Встроена |

---

## 🌍 Unicode-классы

Для работы с символами, выходящими за пределы ASCII (кириллица, греческий,
арабский, китайский и т.д.), используйте синтаксис `UNICODE.<Класс>` внутри
символьных классов. Библиотека автоматически переключается на пакет
[`regex`](https://pypi.org/project/regex/), который поддерживает Unicode-свойства
(`\p{...}`).

```python
from pattern_grammar import Pattern

# Кириллические слова
pattern = Pattern("""
    cyrillic_word ::= [UNICODE.Cyrillic]+
""")
print(pattern.match('cyrillic_word', 'привет'))  # True
print(pattern.match('cyrillic_word', 'hello'))   # False

# Смешанные ASCII и Unicode
pattern = Pattern("""
    email ::= [UNICODE.Letter UNICODE.Digit ._%+\\-]+
            "@" [UNICODE.Letter UNICODE.Digit .\\-]+
            "." [UNICODE.Letter]{2,}
""")
print(pattern.match('email', 'café@münchen.de'))  # True
print(pattern.match('email', '用户@例子.中国'))    # True
```

### Доступные Unicode-классы

| Класс | Regex-эквивалент | Описание |
|-------|-----------------|---------|
| `UNICODE.Letter` | `\p{L}` | Любая буква |
| `UNICODE.Lowercase` | `\p{Ll}` | Строчная буква |
| `UNICODE.Uppercase` | `\p{Lu}` | Заглавная буква |
| `UNICODE.Digit` | `\p{Nd}` | Десятичная цифра |
| `UNICODE.Number` | `\p{N}` | Любое число |
| `UNICODE.Punctuation` | `\p{P}` | Знак пунктуации |
| `UNICODE.Separator` | `\p{Z}` | Разделитель (пробел) |
| `UNICODE.Symbol` | `\p{S}` | Символ |
| `UNICODE.Mark` | `\p{M}` |_combining mark_ |
| `UNICODE.Latin` | `\p{Script=Latin}` | Латиница |
| `UNICODE.Cyrillic` | `\p{Script=Cyrillic}` | Кириллица |
| `UNICODE.Han` | `\p{Script=Han}` | Китайские иероглифы |
| `UNICODE.Arabic` | `\p{Script=Arabic}` | Арабская письменность |
| `UNICODE.Devanagari` | `\p{Script=Devanagari}` | Хинди/маратхи |
| `UNICODE.Hangul` | `\p{Script=Hangul}` | Корейский |
| `UNICODE.Hiragana` | `\p{Script=Hiragana}` | Хирагана |
| `UNICODE.Katakana` | `\p{Script=Katakana}` | Катакана |
| `UNICODE.Thai` | `\p{Script=Thai}` | Тайский |
| `UNICODE.Hebrew` | `\p{Script=Hebrew}` | Еврейский |
| `UNICODE.AlphaNum` | `[\p{L}\p{Nd}]` | Буква или цифра |
| `UNICODE.Word` | `[\p{L}\p{Nd}_]` | Символ слова |

> **Примечание:** Unicode-классы требуют пакета `regex`. Установите его командой:
> `pip install regex`. Когда `regex` недоступен и в паттерне используется
> `UNICODE.*`, возникает `ImportError` с инструкцией по установке.

---

## ⚠️ Известные ограничения

- **Комментарии** — полная поддержка (inline и на отдельных строках)
- **Рекурсия** — глубина рекурсии ограничена стеком Python (обычно ~1000)
- **Lookahead/lookbehind** — не поддерживаются (это особенность BNF-подхода)
- **Экранирование кавычек** — не поддерживается `\"`, используйте разные типы кавычек
- **Hash в символьных классах** — `#` внутри `[...]` заменяется на заполнитель, что может повлиять на совпадение


## 🛠 Разработка

### Линтинг

```bash
ruff check pattern_grammar/
```

### Проверка типов

```bash
mypy pattern_grammar/
```

### Тестирование

```bash
pytest --cov=pattern_grammar --cov-report=term-missing
```

---

## 🔌 Интеграция с Pydantic

Ядро `Pattern` работает **без Pydantic**:

```bash
pip install pattern-grammar
```

Для интеграции с Pydantic установите опциональные зависимости:

```bash
pip install pattern-grammar[pydantic]
```

### Пример

```python
from pydantic import BaseModel, ValidationError
from pattern_grammar import Pattern
from pattern_grammar.integrations.pydantic import PatternType

email_pattern = Pattern('email ::= [a-z]+ "@" [a-z]+ ".com"')

class User(BaseModel):
    email: PatternType(email_pattern, 'email')

user = User(email='user@example.com')  # OK
# User(email='invalid')               # raises ValidationError
```

### Кастомные сообщения об ошибках через `@fail`

```python
fail_pattern = Pattern(
    'email ::= [a-z]+ "@" [a-z]+ ".com" @fail "неверный email"'
)

class UserWithFail(BaseModel):
    email: PatternType(fail_pattern, 'email')

UserWithFail(email='123@example.com')
# raises ValueError: неверный email
```

См. также: [examples/pydantic_integration.py](examples/pydantic_integration.py)

---

## 📄 Лицензия

Этот проект распространяется под лицензией MIT.

---

## 🙏 Благодарности

- [Lark Parser](https://lark-parser.readthedocs.io/) — мощный парсер для Python
- Джону Бэкусу и Петеру Науру — создателям БНФ

---

**Счастливого паттернинга! 🎉**
