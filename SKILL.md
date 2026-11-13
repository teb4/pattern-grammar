---
name: pattern-grammar-regex-replacement
description: Replaces complex regular expressions with human-readable pattern grammar rules using the pattern-grammar library. Use when reviewing code with hard-to-read regex or validating structured formats like URL, email, dates, IP addresses, semver, phone numbers, JSON, and ISO 8601.
version: 1.0.0
author: teb4
---

# Pattern Grammar instead of Regex

Replace opaque regular expressions with small, readable, human-maintainable
grammar rules. Each rule describes **one** piece of a format; the library
compiles the whole grammar into fast regexes for simple rules and a real
parser for recursive ones.

Use this skill whenever you see a regex that is long, hard to read, uses
lookahead/lookbehind as a crutch, or validates a structured format
(URL, email, date, IP, semver, phone, JSON, ISO 8601).

---

## 1. Install and import

```bash
pip install pattern-grammar          # core (depends only on lark)
pip install pattern-grammar[pydantic]  # + Pydantic integration
pip install regex                    # + UNICODE.* character classes
```

```python
from pattern_grammar import Pattern, match, parse, PatternError
```

The core `Pattern` works **without** Pydantic and **without** `regex`.
Only `UNICODE.*` classes and the Pydantic integration need the optional
dependencies. When `regex` is missing and a pattern uses `UNICODE.*`, an
`ImportError` with installation instructions is raised.

---

## 2. What it is (and how it works)

Write BNF-like rules:

```bnf
email ::= username "@" domain "." tld
username ::= [a-zA-Z0-9._%+-]+
domain   ::= [a-zA-Z0-9.-]+
tld      ::= [a-zA-Z]{2,}
```

The library **automatically** chooses an implementation per rule:

| Rule type | Implementation | Why |
|-----------|----------------|-----|
| **Non-recursive** (no rule reference that cycles back to itself) | Regular expression | Fast, zero overhead |
| **Recursive** (participates in, or transitively depends on, a rule-reference cycle) | Lark LALR parser | Supports nesting |

**How recursion is decided.** A rule reference is any token whose name matches
another rule (e.g. `term`, `NUMBER`). A rule becomes a *parser* (Lark) rule
when:

- it (directly or indirectly) references itself — a cycle, **or**
- it transitively depends on a rule that has such a cycle.

Example: `factor ::= NUMBER | "(" expr ")"` references `expr`, and `expr`
references `term` → `factor` → `expr`. That cycle makes `expr`, `term`,
`factor` Lark rules. A standalone `email ::= ...` that only references simple
char-only rules stays a **regex** rule.

**Two consequences you must know:**

1. **Whitespace is auto-ignored ONLY for Lark (recursive) rules**, via
   `%ignore /\s+/`. For regex rules every character — including spaces — is
   literal. So `2 + 3` matches a recursive math grammar (spaces ignored) but
   does **not** match the same operators written for a regex rule unless you
   add `\s` explicitly.
2. **`match()` anchors the whole string.** Regex rules compile to
   `^(?:...)$`, so the entire input must match — no partial matches.

---

## 3. Public API

```python
pattern = Pattern(grammar_text, base_path=None)
```

| Method | Returns | Notes |
|--------|---------|-------|
| `pattern.match(rule, text, *, ignore_case=False) -> bool` | `bool` | Full-string match. On failure raises `PatternError` if the rule (or an inner rule) has `@fail`. |
| `pattern.parse(rule, text, *, ignore_case=False) -> Tree \| None` | Lark `Tree` or regex `Tree('match', …)` or `None` | Returns the parse AST for recursive rules; `None` when the text does not match. |
| `pattern.findall(rule, text, *, ignore_case=False) -> list[str]` | `list[str]` | **Non-recursive (regex) rules only** — raises `PatternError` for recursive rules. |
| `pattern.generate(rule, count=1, max_depth=None) -> list[str]` | `list[str]` | Random strings that match the rule. `count=1` → one-element list. |
| `pattern.get_info() -> dict` | `dict` | `total_rules`, `regex_rules`, `parser_rules`, `rules`. Use `parser_rules` to confirm Lark is used. |
| `pattern.to_json_schema(rule) -> dict` | `dict` | Regex rule → `{"type": "string", "pattern": "<regex>"}`. Parser rule → `{"type": "string", "description": "<BNF>"}`. |

Quick one-shot functions (build a `Pattern` internally):

```python
match(grammar_text, rule, text, base_path=None, *, ignore_case=False) -> bool
parse(grammar_text, rule, text, base_path=None, *, ignore_case=False) -> Tree | None
```

`base_path` resolves relative `import "..."` directives (relative to the
calling file's directory when it is a file path).

**`ignore_case` differs by engine.** For regex rules it uses the `IGNORECASE`
flag. For Lark rules it lower-cases the input (`text.lower()`) before parsing,
so the grammar must contain only lowercase letters.

---

## 4. Grammar syntax reference

```bnf
# Rule definition — "::=" or the shorter ":=" both work
name ::= body

# Alternation
expr ::= term | expr "+" term

# Grouping
group ::= "(" expr ")"

# Quantifiers (postfix) and braced repeats
list ::= item ("," item)*
opt  ::= prefix? item
pin  ::= digit{4}
byte ::= digit{1,3}
```

- **String literals:** `"text"` or `'text'`. To embed a quote, use the
  *opposite* quote type (`'"'` or `["]`). The escaped form `"\""` is
  **not supported** — on purpose.
- **Character classes:** same syntax as regex — `[a-z]`, `[a-zA-Z0-9]`,
  `[^0-9]`, `\d`, `.`.
- **Rule references:** a token equal to another rule's name (e.g. `term`,
  `NUMBER`).
- **Built-in classes** (matched case-insensitively):

  | Name | Expands to | Name | Expands to |
  |------|-----------|------|-----------|
  | `digit` | `[0-9]` | `word` | `[a-zA-Z0-9_]+` |
  | `digits` | `[0-9]+` | `whitespace` | `\s` |
  | `alpha` | `[a-zA-Z]` | `space` | `' '` |
  | `alnum` | `[a-zA-Z0-9]` | `tab` | `'\t'` |
  | | | `newline` | `'\n'` |

- **`@fail "message"`** — attach a custom error to a rule. On a failed match
  a `PatternError` with that message is raised. See §7.
- **Comments** — `#` to end of line.
- **Imports** — `import "path"` (§8).
- **Multi-line rules** — a line is a continuation of the previous rule when
  it starts with a space/tab **and** does not contain `::=` or `:=`. Use this
  to split long rules for readability.

### The `#` character inside character classes

Inside `[...]` the `#` (and `$`, `&`) is replaced with an internal placeholder
and may break matching. Put such characters in a **string literal** instead:

```bnf
hex_color ::= "#" [0-9a-fA-F]{6}     # good: "#" is a literal
# avoid: [#] inside a character class
```

---

## 5. Step-by-step: converting a regex into grammar

1. **Decompose** the regex into its logical components (the human-readable
   meaning of each chunk).
2. **One rule per component.** Give each a descriptive name.
3. **Assemble** the top-level rule from those components, using literals for
   separators and quantifiers for repetition.
4. **Make it recursive when needed.** If the format is nested (math exprs,
   JSON, semver pre-release) the natural rule references already form cycles.
   If you need whitespace ignored around operators, ensure a recursion cycle
   exists or add `\s` explicitly.
5. **Verify** with `match()` / `parse()` against positive and negative cases.

### Regex → grammar conversion table

| Regex | Pattern Grammar |
|-------|-----------------|
| `[^@]+` | `[^@]+` |
| `(?:25[0-5]\|2[0-4][0-9])` | `"25"[0-5] \| "2"[0-4][0-9]` |
| `(?::[0-9]*)?` | `":" [0-9]*` |
| `\[(?:...)\]` | `"[" ( ... ) "]"` |
| `(?:pattern)` | `( pattern )` |
| `^ … $` | implicit — `match()` anchors the whole string |
| `a{3}` / `a{2,4}` | `a{3}` / `a{2,4}` (braced repeat as one token) |

Prefer **composition** over monolithic classes: define a character class once
and reuse it, combining with alternation. This keeps grammars diffable.

---

## 6. Worked examples

### Email (all regex rules)

```bnf
email    ::= username "@" domain "." tld
username ::= [a-zA-Z0-9._%+-]+
domain   ::= [a-zA-Z0-9.-]+
tld      ::= [a-zA-Z]{2,}
```

### Date (regex rules, literal separators)

```bnf
date  ::= year "-" month "-" day
year  ::= [0-9]{4}
month ::= "0"[1-9] | "1"[0-2]
day   ::= "0"[1-9] | [12][0-9] | "3"[01]
```

### Math expressions (recursive → Lark, whitespace ignored)

```bnf
expr   ::= term (("+" | "-") term)*
term   ::= factor (("*" | "/") factor)*
factor ::= NUMBER | "(" expr ")"
NUMBER ::= [0-9]+
```

```python
pattern.match('expr', '2 + 3 * 4')        # True  (spaces ignored by Lark)
tree = pattern.parse('expr', '2 + 3 * 4')
print(tree.pretty())
```

### SemVer

```bnf
semver ::= major "." minor "." patch ("-" pre)? ("+" build)?
major ::= [1-9] [0-9]* | "0"
minor ::= [1-9] [0-9]* | "0"
patch ::= [1-9] [0-9]* | "0"
pre ::= preident ("." preident)*
preident ::= [0-9]+ | [a-zA-Z-]+ [0-9a-zA-Z-]*
build ::= segment ("." segment)*
segment ::= [a-zA-Z0-9-]+
```

> The `-` and `+` are **literal strings** `"-"` / `"+"`, not part of the
> identifier. `"-pre"` would be a literal "-pre" and would not match
> `1.2.3-rc.1`.

### URL / RFC 3986 (multi-line grammar)

```bnf
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
dec-octet ::= "25"[0-5] | "2"[0-4][0-9] | "1"[0-9][0-9] | [1-9][0-9] | [0-9]
ipv6      ::= "[" ( ipv6_full | ipv6_compressed | ipv6_v4mapped | ipv6_linklocal ) "]"
hex4      ::= [0-9a-fA-F]{1,4}
path      ::= "/" (path_segment "/")* path_segment?
path_segment ::= [a-zA-Z0-9\-._~!$&'()*+,;=:@%]+
query     ::= "?" [a-zA-Z0-9\-._~!$&'()*+,;=:@%?]*
fragment  ::= "#" [a-zA-Z0-9\-._~!$&'()*+,;=:@%?#]*
```

This single grammar replaces a ~44-line URL monster regex and correctly handles
compressed IPv6 forms (`[::1]`, `[2001:db8::1]`, `[fe80::1%eth0]`) that the
regex misses.

### JSON (deeply recursive → Lark)

```bnf
json ::= value
value ::= object | array | string | number | boolean | null
object ::= "{" "}" | "{" members "}"
members ::= member ("," member)*
member ::= string ":" value
array ::= "[" "]" | "[" elements "]"
elements ::= value ("," value)*
string ::= '"' chars '"'
chars ::= [^"\\]+
number ::= "-"? integer fractional? exponent?
integer ::= [0-9]+
fractional ::= "." [0-9]+
exponent ::= [eE] ("+" | "-")? [0-9]+
boolean ::= "true" | "false"
null    ::= "null"
```

---

## 7. Error messages with `@fail`

Attach a message to a rule; it is raised as `PatternError` when matching fails.

```bnf
email ::= [a-z]+ "@" [a-z]+ ".com" @fail "invalid email address"
```

```python
pattern.match('email', 'user@example.com')   # True
pattern.match('email', 'invalid')            # raises PatternError: invalid email address
```

**Nested `@fail`.** When a rule references inner rules that each carry their
own `@fail`, a failure reports the message of the **specific sub-rule** that
failed, not just the top-level one:

```bnf
local  ::= [a-z]+        @fail "invalid local part"
domain ::= [a-z]+        @fail "invalid domain"
tld    ::= [a-z]{2,}     @fail "invalid tld"
email  ::= local "@" domain "." tld @fail "invalid email"
```

```python
pattern.match('email', '123@a.com')   # PatternError: invalid local part
pattern.match('email', 'a@123.com')   # PatternError: invalid domain
```

This works for regex rules (via named capture groups) and surfaces the deepest
failing rule.

---

## 8. Importing external grammars

Reuse rules from built-in libraries or `.pg` files:

```bnf
import "rfc3986-core.pg"     # built-in library shipped with the package
import "./common.pg"          # relative to the calling file
import "/abs/path.pg"         # absolute path
```

Imports are resolved before parsing; rules from the imported grammar are merged
in, and an existing rule name wins (the importing grammar is not overwritten).
The package ships `pattern_grammar/lib/rfc3986-core.pg` with the basic URI
character classes (`unreserved`, `pct-encoded`, `sub-delims`, `gen-delims`,
`pchar`, `query-char`, etc.).

---

## 9. Unicode classes

Inside a character class, use `UNICODE.<Class>`. The library auto-switches to
the `regex` package (`\p{...}`):

```bnf
cyrillic_word ::= [UNICODE.Cyrillic]+
mixed_email   ::= [UNICODE.Letter UNICODE.Digit ._%+\-]+
                "@" [UNICODE.Letter UNICODE.Digit .\-]+
                "." [UNICODE.Letter]{2,}
```

```python
pattern.match('cyrillic_word', 'привет')          # True
pattern.match('mixed_email', 'café@münchen.de')   # True
pattern.match('mixed_email', '用户@例子.中国')      # True
```

Available classes: `Letter`, `Lowercase`, `Uppercase`, `Digit`, `Number`,
`Punctuation`, `Separator`, `Symbol`, `Mark`, `Latin`, `Cyrillic`, `Han`,
`Arabic`, `Devanagari`, `Hangul`, `Hiragana`, `Katakana`, `Thai`, `Hebrew`,
`AlphaNum` (`[\p{L}\p{Nd}]`), `Word` (`[\p{L}\p{Nd}_]`).

---

## 10. Pydantic integration

```python
from pydantic import BaseModel
from pattern_grammar import Pattern
from pattern_grammar.integrations.pydantic import PatternType, PatternValidator

email_pattern = Pattern('email ::= [a-z]+ "@" [a-z]+ ".com"')

class User(BaseModel):
    email: PatternType(email_pattern, 'email')

User(email='user@example.com')   # OK
User(email='invalid')            # raises ValidationError
```

- `@fail` messages propagate into `ValidationError` / `ValueError`.
- For nested `@fail`, the failing sub-rule's message is used.
- Pydantic v2 style without the wrapper:

  ```python
  from typing import Annotated
  URI = Annotated[str, PatternValidator(grammar, 'uri')]
  ```

- `pattern.to_json_schema('email')` supplies the JSON Schema for the field.

---

## 11. Value objects — "parse, don't validate"

Model a format as a type whose constructor proves validity. The grammar
describes **structure** (syntax); business rules live in **code** (semantics).
This is the place for checks regex can only fake with lookahead:

```python
from pattern_grammar import Pattern, PatternError

class Password:
    _pattern = Pattern(
        r'password ::= [a-zA-Z0-9!@#$%^&*]{8,} '
        r'@fail "password must be at least 8 characters"'
    )
    def __init__(self, value: str) -> None:
        try:
            self._pattern.match('password', value)
        except PatternError as e:
            raise ValueError(str(e)) from None
        # semantic checks that belong in code, not regex lookahead:
        if not any(c.isupper() for c in value):
            raise ValueError("needs at least one uppercase letter")
        if not any(c.isdigit() for c in value):
            raise ValueError("needs at least one digit")
        if not any(c in '!@#$%^&*' for c in value):
            raise ValueError("needs at least one special character")
        self._value = value
```

The grammar proves the string is structurally well-formed; the class enforces
meaning. A `Password` cannot exist in an invalid state.

---

## 12. Gotchas and limitations (read carefully)

- **No lookahead / lookbehind.** This is inherent to the BNF approach. Encode
  "must contain X" as structure, or move it to code (see §11).
- **Whitespace is literal for regex rules.** Only Lark (recursive) rules ignore
  surrounding whitespace. Add `\s` explicitly for regex rules if you need it.
- **`match()` anchors the whole string** (`^...$`). There is no "search" mode —
  use `findall()` to locate substrings (regex rules only).
- **`#` inside `[...]`** becomes a placeholder and may break matching. Use a
  string literal `"#"` instead.
- **Quote escaping `"\""` is not supported.** Use opposite quotes or `["]`.
- **Recursion depth** is bounded (the analyzer caps at 100 levels); extremely
  deep nesting may not be detected as recursive.
- **`generate()` returns a list** of strings (one element for `count=1`), not a
  bare string.
- **Rule references are case-sensitive** as written; built-in class names match
  case-insensitively.
- **`findall()` raises `PatternError` for recursive (Lark) rules.**

---

## 13. Checklist before you finish

- [ ] Regex split into logical components, one rule each.
- [ ] Separators written as string literals (`"-"`, `":"`, `"@"`).
- [ ] Nested structures form recursion cycles → confirmed via `get_info()['parser_rules']`.
- [ ] Whitespace handled correctly (Lark auto-ignores it; regex rules need explicit `\s`).
- [ ] `#`/`$`/`&` inside classes moved to string literals.
- [ ] `@fail` messages added for user-facing validation.
- [ ] Positive **and** negative test cases pass via `match()` / `parse()`.
- [ ] For recursive rules, verify the AST with `parse(...).pretty()`.

---

## 14. Reference: examples and tests

Runnable examples in `examples/`:

| File | Teaches |
|------|---------|
| `email_validation.py`, `date_validation.py` | Simple regex rules |
| `math_expressions.py` | Recursion → Lark, `parse().pretty()` |
| `semver_validation.py`, `url_validation.py` | Multi-line grammars, regex-vs-grammar comparison |
| `rfc3986_full.py`, `rfc3986_url.py` | Full RFC 3986 URI grammar, composition of character classes |
| `ipv6_validation.py`, `ISO_8601_datetime_validation.py` | Complex date/time formats |
| `phone_validation.py` | E.164 with plain and formatted variants |
| `json_parser.py` | Deeply recursive grammar (objects/arrays) |
| `uk_postcode_validation.py` | Large hand-written format vs regex |
| `value_object.py` | Parse-don't-validate value objects (Email, Password) |
| `pydantic_integration.py`, `rfc3986_pydantic.py` | Pydantic models + `@fail` |
| `check_examples.py` | Validates the README examples |

Run the suite (with coverage):

```bash
pytest --cov=pattern_grammar --cov-report=term-missing
```

---

## 15. Why this over regex

| Aspect | Regex | Pattern Grammar |
|--------|-------|-----------------|
| Simple patterns | Concise | Equivalent |
| Complex patterns | Unreadable nightmare | Structured, rule-by-rule |
| Readability | Poor | Excellent |
| Multi-line | Not supported | Built-in |
| Maintainability | Hard | Easy |
| Testing | All-or-nothing | Per-rule |
| Recursion | Impossible | Supported |
| Documentation | Separate | In the grammar itself |

**Conclusion:** regex is fine for one-liners, but for any structured format it
becomes a brittle incantation. Pattern Grammar is understandable, debuggable,
testable, and self-documenting.
