# Pattern Grammar

**Human-readable patterns instead of regular expressions**

---

## 🎯 What is this?

`pattern-grammar` is a library for describing patterns in a human-friendly way.

Instead of an opaque regex:
```python
pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
```

Write readable grammar:
```bnf
email ::= username "@" domain "." tld
username ::= [a-zA-Z0-9._%+-]+
domain ::= [a-zA-Z0-9.-]+
tld ::= [a-zA-Z]{2,}
```

---

## 📦 Installation

### Local installation (for development)

```bash
# Clone the repository
git clone https://github.com/teb4/pattern-grammar.git
cd pattern-grammar

# Install in development mode
pip install -e .

# Or just install dependencies
pip install -r requirements.txt
```

---

## 🚀 Quick Start

### Example 1: Simple validation

```python
from pattern_grammar import Pattern

# Define a pattern
pattern = Pattern("""
    email ::= username "@" domain "." tld
    username ::= [a-zA-Z0-9._%+-]+
    domain ::= [a-zA-Z0-9.-]+
    tld ::= [a-zA-Z]{2,}
""")

# Check
print(pattern.match('email', 'test@example.com'))  # True
print(pattern.match('email', 'invalid'))           # False
```

### Example 2: Complex structure (recursion)

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

# Get parse tree
tree = pattern.parse('expr', '2 + 3 * 4')
print(tree.pretty())
```

---

## 📖 Syntax

### Basic constructs

```bnf
# Rule definition
<name> ::= <body>

# Alternation
expr ::= term | expr "+" term

# Grouping
group ::= "(" expr ")"

# Repetition
list ::= item ("," item)*

# Optional
optional ::= prefix? item

# Ranges
pin ::= digit{4}
byte ::= digit{1,3}
```

### Multi-line rules

Long rules can be split across multiple lines for better readability. Lines with indentation are treated as continuations of the previous rule:

```bnf
# Alternatives on separate lines
scheme ::= "http" | "https" | "ftp"  | "file" | "ssh"
         | "git"  | "svn"  | "mailto"| "news" | "irc"
         | "rtsp" | "webcal"

# Sequence across multiple lines
ipv6_full ::= hex4 ":" hex4 ":" hex4 ":" hex4 ":"
              hex4 ":" hex4 ":" hex4 ":" hex4

# Alternatives with alignment
dec-octet ::= "25"[0-5]
            | "2"[0-4][0-9]
            | "1"[0-9][0-9]
            | [1-9][0-9]
            | [0-9]
```

> **Rule:** a line is treated as a continuation of the previous rule if it starts with a space or tab and does not contain `::=`.


### Comments

Comments start with `#` and **must be on their own line**. Inline comments at the end of a rule line are not supported.

```bnf
# ✅ Correct: comment on its own line
email ::= username "@" domain "." tld
username ::= [a-z]+    # ❌ WRONG: inline comment
domain ::= [a-z]+      # The parser will read this as part of the rule!

# ✅ Correct:
# Domain definition
domain ::= [a-z]+
```

> **Important:** The parser reads the entire line. If you place a `#` after a rule, everything including the comment will be treated as part of the rule. This can lead to unexpected errors.

### Why this design?

This decision was made intentionally to:

- Keep grammar processing simple and fast — no need to escape `#` in rules
- Eliminate ambiguity — it's always clear what's a rule and what's a comment
- Maintain compatibility with BNF-like formats — many parsers require comments on separate lines

### Exception

The `#` character can be used inside string literals and character classes:

```bnf
# ✅ Valid: # inside a string
comment_line ::= "#" [a-zA-Z]+

# ✅ Valid: # in a character class
hex_color ::= "#" [0-9a-fA-F]{6}

# ✅ Valid: # in a string literal
python_comment ::= "#" [^\n]*
```

If you need a rule that ends with `#` (e.g., for hex colors), simply include it in the rule explicitly as shown above.

### Character classes

Character class syntax is the same as in regular expressions:

```bnf
# Letters
alpha ::= [a-z]
alpha ::= [a-zA-Z]

# Digits
digit ::= [0-9]
digit ::= \d

# Letters and digits
alnum ::= [a-zA-Z0-9]

# Any character
any ::= .

# Negation
not_digit ::= [^0-9]
```

### Quote literals

To represent a quote character inside a literal, use the **opposite type of quotes**:

```bnf
# Double-quote literal — wrap in single quotes
string ::= '"' chars '"'

# Single-quote literal — wrap in double quotes
quoted ::= "'" chars "'"
```

Alternatively, use a character class `["]` or `[']`:

```bnf
string ::= ["] chars ["]
```

> ⚠️ **Important:** The `"\""` syntax (escaped quote within the same quote type) is **not supported**. This is intentional — escaping inside Python strings makes grammars unreadable, which defeats the purpose of the library.

### Built-in classes

For convenience, predefined classes are available:

```bnf
digit       ::= [0-9]          # Single digit
digits      ::= [0-9]+         # One or more digits
alpha       ::= [a-zA-Z]       # Single letter
alnum       ::= [a-zA-Z0-9]    # Letter or digit
word        ::= [a-zA-Z0-9_]+  # Word
whitespace  ::= \s             # Whitespace character
```

---

## 🔍 API

### `Pattern(grammar_text: str)`

Creates a pattern from grammar text.

```python
pattern = Pattern("""
    email ::= username "@" domain "." tld
    username ::= [a-z]+
    domain ::= [a-z]+
    tld ::= [a-z]{2,}
""")
```

### `pattern.match(rule_name: str, text: str) -> bool`

Checks whether the text matches the rule.

```python
pattern.match('email', 'test@example.com')  # True
pattern.match('email', 'invalid')           # False
```

### `pattern.parse(rule_name: str, text: str) -> Tree | None`

Parses the text and returns a parse tree (AST).

```python
tree = pattern.parse('expr', '2 + 3 * 4')
print(tree.pretty())
```

### `pattern.findall(rule_name: str, text: str) -> List[str]`

Finds all matches in the text (non-recursive rules only).

```python
pattern = Pattern('hashtag ::= "#" [a-z0-9_]+')
text = "This is a #test post with #multiple #hashtags"
pattern.findall('hashtag', text)
# ['#test', '#multiple', '#hashtags']
```

### `pattern.get_info() -> dict`

Returns information about the grammar.

```python
info = pattern.get_info()
print(info)
```

### Quick functions

```python
from pattern_grammar import match, parse

# Quick check
result = match("""
    email ::= [a-z]+@[a-z]+\.[a-z]{2,}
""", 'email', 'test@example.com')

# Quick parse
tree = parse("""
    expr ::= term (("+"|"-") term)*
    term ::= factor (("*"|"/") factor)*
    factor ::= NUMBER | "(" expr ")"
""", 'expr', '1 + 2 + 3')
```

---

## 🧠 How it works?

### Automatic method selection

The library **automatically** determines how to implement each rule:

| Rule type | Implementation | Why |
|-----------|---------------|-----|
| **Non-recursive** | Regular expression | Fast and efficient |
| **Recursive** | Lark parser | Supports nesting |

```python
pattern = Pattern("""
    # Non-recursive → fast regex
    email ::= username "@" domain "." tld
    username ::= [a-z]+
    
    # Recursive → full parser
    expr ::= term (("+"|"-") term)*
    term ::= factor (("*"|"/") factor)*
    factor ::= NUMBER | "(" expr ")"
""")

# See what was used
print(pattern.get_info())
# {
#   'regex_rules': ['email', 'username', ...],
#   'parser_rules': ['expr', 'term', 'factor']
# }
```

---

## 📚 Examples

### Example 1: Email validation

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

### Example 2: Math expressions

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
    '2 +',  # Invalid
]

for expr in expressions:
    result = pattern.match('expr', expr)
    print(f"{expr:20} -> {result}")
```

### Example 3: Date validation

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
    '2024-13-01',  # Invalid month
]

for date in dates:
    result = pattern.match('date', date)
    print(f"{date} -> {result}")
```

### Example 4: URL validation (multi-line grammar)

The multi-line syntax is especially useful for complex grammars:

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

### Example 5: URL validation — Regex vs Grammar

Compare how complex patterns look in regex versus Pattern Grammar:

#### Regex (sourced from the web. 44 lines of madness — try reading this!):

```python
# Monster regex for URL (RFC 3986/3987)
URL_MONSTER = re.compile(
    r'^(?:[a-zA-Z][a-zA-Z0-9+\-.]*:)?'  # scheme
    r'(?://'  # authority
        r'(?:[a-zA-Z0-9\-._~!$&\'()*+,;=]+@)?'  # userinfo
        r'(?:'  # host
            # IPv4
            r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
            r'|'
            # IPv6 — 15 lines of nightmare!
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

#### Pattern Grammar (full URL grammar):

```bnf
# Main rule
url ::= scheme "://" authority path? query? fragment?

# Scheme (protocol)
scheme ::= "http" | "https" | "ftp"  | "file" | "ssh"
         | "git"  | "svn"  | "mailto"| "news" | "irc"
         | "rtsp" | "webcal"

# Authority (host + optional userinfo and port)
authority ::= userinfo? host port?
userinfo  ::= [^@]+ "@"
host      ::= ipv4 | ipv6 | domain
port      ::= ":" [0-9]{2,5}

# Domain names
domain   ::= label ("." label)*
alnum    ::= [a-zA-Z0-9]
alnumhyp ::= [a-zA-Z0-9-]
label    ::= alnum (alnumhyp* alnum)?

# IPv4 addresses
ipv4      ::= dec-octet "." dec-octet "." dec-octet "." dec-octet
dec-octet ::= "25"[0-5]     # 250-255
            | "2"[0-4][0-9] # 200-249
            | "1"[0-9][0-9] # 100-199
            | [1-9][0-9]    # 10-99
            | [0-9]          # 0-9

# IPv6 addresses (all forms)
ipv6            ::= "[" ( ipv6_full | ipv6_compressed | ipv6_v4mapped | ipv6_linklocal ) "]"
hex4            ::= [0-9a-fA-F]{1,4}

# Full form (8 groups)
ipv6_full       ::= hex4 ":" hex4 ":" hex4 ":" hex4 ":"
                    hex4 ":" hex4 ":" hex4 ":" hex4

# Compressed form with :: (all variants)
ipv6_compressed ::= ipv6_start | ipv6_middle | ipv6_end
ipv6_start      ::= "::" (hex4? (":" hex4)*)
ipv6_middle     ::= hex4 "::" hex4? (":" hex4)*
ipv6_end        ::= hex4 (":" hex4)+ "::" hex4?
                  | hex4 (":" hex4)+ "::"

# Special IPv6 forms
ipv6_v4mapped   ::= "::ffff:" ipv4
ipv6_linklocal  ::= "fe80:" (":" hex4)* "%" [a-zA-Z0-9]+

# Path
path_char    ::= [a-zA-Z0-9\-._~!$&'()*+,;=:@%]
path_segment ::= path_char+
path         ::= "/" (path_segment "/")* path_segment?

# Query parameters
query_char ::= [a-zA-Z0-9\-._~!$&'()*+,;=:@%?]
query      ::= "?" query_char*

# Fragment
fragment_char ::= [a-zA-Z0-9\-._~!$&'()*+,;=:@%?#]
fragment      ::= "#" fragment_char*
```

### Moreover, it turned out the regex isn't entirely correct.

#### What the regex missed:

    ❌ All IPv6 addresses (except the full form)

        http://[2001:db8::1] — IPv6 with compression

        http://[::1] — IPv6 localhost

        http://[::ffff:192.0.2.1] — IPv4-mapped

        http://[fe80::1%eth0] — IPv6 with zone ID

    ❌ http:// — empty host

    ❌ http://.com — dot at the start of the domain

    ❌ http://example..com — double dot in domain

    ❌ http://-example.com — leading hyphen

    ❌ http://example-.com — trailing hyphen

#### Where Pattern Grammar fell short:

    ⚠️ http://256.256.256.256 — marked as valid, even though it's an invalid IPv4 (but could be a valid domain name!)

> **Conclusion:** Regex is not suitable for complex formats — it becomes too convoluted in such cases. Pattern Grammar can be understood, debugged, and maintained.


### Additionally, you can write a longer version that more closely follows RFC terminology and is suitable for further extension:

```bnf
# =============================================================================
# BASIC CHARACTER CLASSES (RFC 3986, Section 2.2-2.4)
# Defined ONCE and reused across all rules
# =============================================================================

# unreserved — always safe characters, no percent-encoding needed
unreserved  ::= [a-zA-Z0-9\-._~]

# gen-delims — general delimiters with special meaning in URLs
gen-delims  ::= [:/?#[]@]

# sub-delims — reserved subset for user data
sub-delims  ::= [!$&'()*+,;=]

# reserved — combined set (gen-delims + sub-delims)
reserved    ::= gen-delims | sub-delims

# pct-encoded — percent-encoding (%XX where XX are hex digits)
pct-encoded ::= "%" [0-9a-fA-F]{2}

# =============================================================================
# COMPOSITION: assembling classes for specific URL parts
# Using alternation (|) instead of duplicating character classes
# =============================================================================

# pchar — primary building block for path, query, fragment (RFC 3986, Section 3.3)
pchar       ::= unreserved | pct-encoded | sub-delims | ":" | "@"

# query-char — extends pchar for query string (adds / and ?)
query-char  ::= pchar | "/" | "?"

# fragment-char — extends pchar for fragment (adds / ? #)
fragment-char ::= pchar | "/" | "?" | "#"

# userinfo-char — for login/password (excludes @, which is a separator)
userinfo-char ::= unreserved | pct-encoded | sub-delims | ":"

# reg-name — for domain names in authority (RFC 3986, Section 3.2)
reg-name    ::= ( unreserved | pct-encoded | sub-delims )+

# =============================================================================
# MAIN URL RULE
# =============================================================================

url         ::= scheme "://" authority path? query? fragment?

# =============================================================================
# SCHEME (PROTOCOL)
# =============================================================================

scheme      ::= "http" | "https" | "ftp"  | "file" | "ssh"
              | "git"  | "svn"  | "mailto"| "news" | "irc"
              | "rtsp" | "webcal"

# =============================================================================
# AUTHORITY (HOST + OPTIONAL USERINFO AND PORT)
# =============================================================================

authority   ::= userinfo? host port?
userinfo    ::= userinfo-char+ "@"
host        ::= ipv4 | ipv6 | domain
port        ::= ":" [0-9]{1,5}

# =============================================================================
# DOMAIN NAMES
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
# IPV6 ADDRESSES (ALL FORMS)
# =============================================================================

ipv6            ::= "[" ( ipv6_full | ipv6_compressed | ipv6_v4mapped | ipv6_linklocal ) "]"
hex4            ::= [0-9a-fA-F]{1,4}

# Full form (8 groups of 4 hex digits)
ipv6_full       ::= hex4 ":" hex4 ":" hex4 ":" hex4 ":"
                    hex4 ":" hex4 ":" hex4 ":" hex4

# Compressed form with :: (all placement variants)
ipv6_compressed ::= ipv6_start | ipv6_middle | ipv6_end
ipv6_start      ::= "::" (hex4? (":" hex4)*)
ipv6_middle     ::= hex4 "::" hex4? (":" hex4)*
ipv6_end        ::= hex4 (":" hex4)+ "::" hex4?
                  | hex4 (":" hex4)+ "::"

# Special IPv6 forms
ipv6_v4mapped   ::= "::ffff:" ipv4
ipv6_linklocal  ::= "fe80:" (":" hex4)* "%" [a-zA-Z0-9]+

# =============================================================================
# PATH
# Using pchar composition instead of monolithic [a-zA-Z0-9\-._~!$&'()*+,;=:@%]
# =============================================================================

path-segment  ::= pchar+
path          ::= "/" (path-segment "/")* path-segment?

# =============================================================================
# QUERY PARAMETERS
# Using query-char composition
# =============================================================================

query         ::= "?" query-char*

# =============================================================================
# FRAGMENT
# Using fragment-char composition
# =============================================================================

fragment      ::= "#" fragment-char*
```

---

## 🧪 Running examples

### Running examples

```bash
# Email validation example
python examples/email_validation.py

# Math expressions example
python examples/math_expressions.py

# Date validation example
python examples/date_validation.py
```

---

## 🆚 Comparison with regular expressions

| Aspect | Regular Expressions | Pattern Grammar |
|--------|---------------------|-----------------|
| **Simple patterns** | ✅ Concise | ✅ Equivalent |
| **Complex patterns** | ❌ A nightmare | ✅ Structured |
| **Readability** | ❌ Poor | ✅ Excellent |
| **Multi-line** | ❌ Not supported | ✅ Built-in |
| **Maintainability** | ❌ Difficult | ✅ Easy |
| **Testing** | ❌ All or nothing | ✅ Rule by rule |
| **Recursion** | ❌ Impossible | ✅ Supported |
| **Documentation** | ❌ Separate | ✅ Built-in |

---

## ⚠️ Known limitations

- **Comments** — only on separate lines (not at the end of rules)
- **Recursion** — recursion depth is limited by Python's stack (typically ~1000)
- **Lookahead/lookbehind** — not supported (this is a characteristic of the BNF approach)
- **Quote escaping** — `\"` is not supported; use different quote types instead


## 📄 License

This project is distributed under the MIT License.

---

## 🙏 Acknowledgments

- [Lark Parser](https://lark-parser.readthedocs.io/) — a powerful parser for Python
- John Backus and Peter Naur — creators of BNF

---

**Happy patterning! 🎉**
