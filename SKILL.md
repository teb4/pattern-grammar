---
id: skill-regex-001
type: skill
name: use-pattern-grammar-for-regex-replacement
version: 1.0.0
status: proven
created: 2026-06-21
updated: 2026-06-21

# Метаданные для LLM-агентов
trigger: |
  Применять, когда нужно заменить регулярное выражение на читаемую грамматику,
  особенно для сложных паттернов (URL, email, даты, математические выражения,
  IPv4/IPv6, семантическое.versioning). Также применять при ревью кода,
  когда обнаружено использование regex для валидации.
inputs:
  - name: regex_pattern
    type: string
    description: Исходное регулярное выражение для замены
    required: false
  - name: description
    type: string
    description: Описание, что валидирует паттерн
    required: true
outputs:
  - name: grammar_text
    type: string
    description: BNF-подобная грамматика, заменяющая regex
  - name: python_example
    type: string
    description: Пример использования через Pattern API
related_skills:
  - write-graveyard-entry
related_mental_models:
  - epistemic-architecture
graveyard_refs:
  - failed-knowledge-organizations
---

# Использование pattern-grammar для замены regex

## Когда применять

Когда в коде обнаружено регулярное выражение, которое:
- Сложно читать (более 3 строк, множество экранирований)
- Валидирует структурированный формат (URL, email, даты, семантическое.versioning)
- Требует поддержки рекурсии (вложенные структуры)
- Должно быть тестируемо по частям (rule-by-rule)

## Принцип

Вместо непрозрачного regex:
```python
r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
```

Пишем читаемую грамматику:
```bnf
email ::= username "@" domain "." tld
username ::= [a-zA-Z0-9._%+-]+
domain ::= [a-zA-Z0-9.-]+
tld ::= [a-zA-Z]{2,}
```

## Алгоритм замены

### 1. Декомпозиция regex на логические части

Разбейте regex на смысловые компоненты:
- `^[a-zA-Z0-9._%+-]+@` → `username`
- `[a-zA-Z0-9.-]+` → `domain`
- `\.[a-zA-Z]{2,}$` → `"." tld`

### 2. Создание BNF-правил

Каждому компоненту — отдельное правило:
```bnf
email ::= username "@" domain "." tld
username ::= [a-zA-Z0-9._%+-]+
domain ::= [a-zA-Z0-9.-]+
tld ::= [a-zA-Z]{2,}
```

### 3. Обработка специальных конструкций

| Regex | Pattern Grammar |
|-------|----------------|
| `[^@]+` | `[^@]+` |
| `(?:25[0-5]|2[0-4][0-9])` | `"25"[0-5] \| "2"[0-4][0-9]` |
| `(?::[0-9]*)?` | `":" [0-9]*` |
| `\[(?:...)\]` | `"[" ( ... ) "]"` |
| `(?:pattern)` | `( pattern )` |

### 4. Обработка многозадачных правил

Для сложных случаев (IPv6, URL) используйте многострочные правила:
```bnf
scheme ::= "http" | "https" | "ftp"  | "file" | "ssh"
         | "git"  | "svn"  | "mailto"| "news" | "irc"
         | "rtsp" | "webcal"
```

### 5. Проверка

```python
from pattern_grammar import Pattern

pattern = Pattern("""
    email ::= username "@" domain "." tld
    username ::= [a-zA-Z0-9._%+-]+
    domain ::= [a-zA-Z0-9.-]+
    tld ::= [a-zA-Z]{2,}
""")

assert pattern.match('email', 'test@example.com') == True
assert pattern.match('email', 'invalid') == False
```

## Критические грабли

- ❌ **Inline-комментарии** — `#` в конце строки считается частью правила. Комментарии только на отдельных строках.
- ✅ **Inline-комментарии** — `#` вне кавычек и символьных классов (`[...]`) начинает комментарий и обрезает строку. Могут стоять в конце строки после правила.
- ❌ **Экранирование кавычек** — `\"` не поддерживается. Используйте разные типы: `'"'` или `["]`.
- ❌ **Глубокая рекурсия** — ограничена 100 шагами анализатора рекурсии (`MAX_RECURSION_DEPTH` в `constants.py`), а не глубиной стека Python. Для очень глубоких вложенностей может не сработать.
- ❌ **Lookahead/lookbehind** — не поддерживаются. Это ограничение BNF-подхода.
- ✅ **Многострочные правила** — строки без `::=` и с отступом считаются продолжением предыдущего правила.
- ✅ **Рекурсивные правила** — автоматически определяются и компилируются в Lark-парсер.
- ✅ **Простые правила** — автоматически компилируются в regex для производительности.

## Примеры замены

### Email

**Был regex:**
```python
r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
```

**Стал grammar:**
```bnf
email ::= username "@" domain "." tld
username ::= [a-zA-Z0-9._%+-]+
domain ::= [a-zA-Z0-9.-]+
tld ::= [a-zA-Z]{2,}
```

### URL (RFC 3986)

**Был regex:** 44 строки кошмара с экранированиями

**Стал grammar:**
```bnf
url ::= scheme "://" authority path? query? fragment?
scheme ::= "http" | "https" | "ftp" | "file" | "ssh"
authority ::= userinfo? host port?
host ::= ipv4 | ipv6 | domain
ipv4 ::= dec-octet "." dec-octet "." dec-octet "." dec-octet
dec-octet ::= "25"[0-5] | "2"[0-4][0-9] | "1"[0-9][0-9] | [1-9][0-9] | [0-9]
```

### Семантическое versioning

**Был regex:**
```python
r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
```

**Стал grammar:**
```bnf
semver ::= major "." minor "." patch ("-" pre)? ("+" build)?
major ::= [1-9] [0-9]* | "0"
minor ::= [1-9] [0-9]* | "0"
patch ::= [1-9] [0-9]* | "0"
pre ::= preident ("." preident)*
preident ::= [0-9]+ | [a-zA-Z-]+ [0-9a-zA-Z-]*
build ::= buildident ("." buildident)*
buildident ::= [0-9a-zA-Z-]+
```

> ⚠️ Разделитель — это литерал `"-"` (минус) и `"+"` (плюс), а не `"-pre"`.
> `"-pre"` интерпретируется как буквальный строковый литерал «-pre» и не будет
> совпадать с `1.2.3-rc.1`. Правильно: `( "-" pre )` и `( "+" build )`.

### Математические выражения

**Был regex:** невозможно (рекурсия)

**Стал grammar:**
```bnf
expr ::= term (("+" | "-") term)*
term ::= factor (("*" | "/") factor)*
factor ::= NUMBER | "(" expr ")"
NUMBER ::= [0-9]+
```

## Чек-лист перед запуском

- [ ] Regex разбит на логические компоненты
- [ ] Каждому компоненту — отдельное правило
- [ ] Использованы встроенные классы (`digit`, `digits`, `alpha`, `word`) где уместно
- [ ] Многострочные правила для сложных случаев (URL, IPv6)
- [ ] Нет inline-комментариев (только отдельные строки)
- [ ] Inline-комментарии разрешены (но `#` внутри кавычек и классов `[...]` — часть правила)
- [ ] Нет экранирования кавычек (использованы разные типы: `'"'` / `["]`)
- [ ] Проверено через `pattern.match()` и `pattern.parse()`
- [ ] Для рекурсивных правил проверено через `pattern.parse()` с `tree.pretty()`

## Связанные знания

**Теория:** [[epistemic-architecture]] — почему читаемость важнее компактности
**Graveyard:** [[failed-knowledge-organizations]] — как НЕ надо организовывать документацию
