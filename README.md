# Pattern Grammar

**Читаемые паттерны вместо регулярных выражений**

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

### Из PyPI

```bash
pip install pattern-grammar
```

### Локальная установка (для разработки)

```bash
# Клонируем репозиторий
git clone https://github.com/yourusername/pattern-grammar.git
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

Комментарии начинаются с `#` и **должны находиться на отдельной строке**. Комментарии в конце строки с правилом не поддерживаются.

```bnf
# ✅ Правильно: комментарий на отдельной строке
email ::= username "@" domain "." tld
username ::= [a-z]+    # ❌ НЕПРАВИЛЬНО: комментарий в конце строки
domain ::= [a-z]+      # Парсер прочитает это как часть правила!

# ✅ Правильно:
# Определение домена
domain ::= [a-z]+
```

> **Важно:** Парсер читает строку целиком. Если после правила поставить #, всё, включая комментарий, будет считаться частью правила. Это может привести к неожиданным ошибкам.

### Почему так?

Такое решение принято намеренно для:

    Простой и быстрой обработки грамматики — не нужно экранировать # в правилах

    Отсутствия неоднозначности — всегда понятно, где правило, а где комментарий

    Совместимости с BNF-подобными форматами — многие парсеры требуют комментарии на отдельных строках

### Исключение

Символ # можно использовать внутри строковых литералов и символьных классов:

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
# ['тестовый', 'несколькими', 'хештегами']
```

### `pattern.get_info() -> dict`

Возвращает информацию о грамматике.

```python
info = pattern.get_info()
print(info)
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
    term ::= [0-9]+
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

    scheme   ::= "http" | "https" | "ftp"  | "file" | "ssh"
               | "git"  | "svn"  | "mailto"| "news" | "irc"
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
    query    ::= "?" [a-zA-Z0-9\-._~!$&'()*+,;=:@%?]*
    fragment ::= "#" [a-zA-Z0-9\-._~!$&'()*+,;=:@%?#]*
""")

print(pattern.match('url', 'https://example.com/path?q=1'))  # True
print(pattern.match('url', 'http://192.168.1.1:8080'))        # True
print(pattern.match('url', 'not a url'))                      # False
```

---

## 🧪 Запуск примеров и тестов

### Запуск примеров

```bash
# Пример валидации email
python examples/email_validation.py

# Пример математических выражений
python examples/math_expressions.py

# Пример валидации дат
python examples/date_validation.py
```

### Запуск тестов

```bash
# Все тесты
pytest tests/ -v

# Конкретный тест
pytest tests/test_simple_patterns.py -v

# С покрытием кода
pytest tests/ -v --cov=pattern_grammar
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

## ⚠️ Известные ограничения

- **Комментарии** — только на отдельных строках (не в конце правил)
- **Рекурсия** — глубина рекурсии ограничена стеком Python (обычно ~1000)
- **Lookahead/lookbehind** — не поддерживаются (это особенность BNF-подхода)
- **Экранирование кавычек** — не поддерживается `\"`, используйте разные типы кавычек


## 📄 Лицензия

Этот проект распространяется под лицензией MIT.

---

## 🙏 Благодарности

- [Lark Parser](https://lark-parser.readthedocs.io/) — мощный парсер для Python
- Джону Бэкусу и Петеру Науру — создателям БНФ

---

**Счастливого паттернинга! 🎉**
