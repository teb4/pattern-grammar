#!/usr/bin/env python3
"""
Value Objects через pattern-grammar.

Демонстрирует принцип разделения синтаксиса и семантики:

    структура  →  грамматика (BNF)
    смысл      →  код (методы класса)

Это то же самое, что ООП сделало с данными и поведением —
но для текстовых типов.

Подробнее: PHILOSOPHY.md
"""
from __future__ import annotations

from pattern_grammar import Pattern, PatternError

# ---------------------------------------------------------------------------
# Вспомогательные данные (в реальном проекте — из конфига или БД)
# ---------------------------------------------------------------------------

DISPOSABLE_DOMAINS = {'mailinator.com', 'tempmail.com', 'throwaway.email'}
CORPORATE_DOMAINS = {'google.com', 'apple.com', 'microsoft.com'}


# ---------------------------------------------------------------------------
# Email — Value Object
#
# Слой 1 (грамматика): отвечает на вопрос "как устроен email?"
# Слой 2 (методы):     отвечает на вопрос "какие правила применяются?"
# ---------------------------------------------------------------------------

class Email:
    """
    Email как тип, а не строка.

    Невозможно создать Email из невалидной строки —
    конструктор физически не позволит.

    Сравните:
        # Валидация — информация теряется, строка остаётся строкой
        if validate_email(s):
            send_email(s)   # send_email снова будет проверять?

        # Парсинг — информация сохраняется в типе
        email = Email(s)    # если дошли сюда — email валиден
        send_email(email)   # send_email принимает Email, проверка не нужна
    """

    # Слой 1: структура — только синтаксис, никакой бизнес-логики
    _pattern = Pattern('''
        local  ::= [a-zA-Z0-9._%+-]+  @fail "некорректная локальная часть email"
        domain ::= [a-zA-Z0-9.-]+     @fail "некорректный домен"
        tld    ::= [a-zA-Z]{2,}       @fail "некорректная доменная зона"
        email  ::= local "@" domain "." tld  @fail "некорректный формат email"
    ''')

    def __init__(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError(f"Ожидалась строка, получено {type(value).__name__}")

        # Слой 2: семантика — бизнес-правила в коде, не в грамматике
        try:
            self._pattern.match('email', value)
        except PatternError as e:
            raise ValueError(str(e)) from None

        parts = value.lower().split('@')
        self.local = parts[0]
        domain_parts = parts[1].rsplit('.', 1)
        self.domain = domain_parts[0]
        self.tld = domain_parts[1]
        self._value = f"{self.local}@{self.domain}.{self.tld}"

        # Семантические правила — то, что грамматика принципиально не может проверить
        if self.local.startswith('.') or self.local.endswith('.'):
            raise ValueError("Локальная часть не может начинаться или заканчиваться точкой")

        if f"{self.domain}.{self.tld}" in DISPOSABLE_DOMAINS:
            raise ValueError(f"Одноразовые домены не принимаются: {self.domain}.{self.tld}")

    # Поведение — тоже часть типа, не разбросано по кодовой базе
    def is_corporate(self) -> bool:
        """Корпоративный ли email."""
        return f"{self.domain}.{self.tld}" in CORPORATE_DOMAINS

    def normalized(self) -> str:
        """Нормализованный email (нижний регистр)."""
        return self._value

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"Email({self._value!r})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Email):
            return self._value == other._value
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._value)


# ---------------------------------------------------------------------------
# Password — Value Object
#
# Ключевой пример: lookahead в regex — это семантика, запихнутая в синтаксис.
#
# Regex с lookahead:   ^(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%]).{8,}$
# С pattern-grammar:   грамматика описывает структуру,
#                      код проверяет смысловые правила.
# ---------------------------------------------------------------------------

class Password:
    """
    Пароль как тип.

    Грамматика говорит: «я доказала, что это структурно допустимая строка».
    Код говорит: «а теперь я проверю, имеет ли этот пароль право существовать».

    Lookahead ((?=.*\\d)) — это не возможность regex, это его архитектурный костыль:
    способ впихнуть семантическую проверку внутрь синтаксического описания.
    Здесь семантика живёт там, где ей место — в коде.
    """

    # Слой 1: структура — допустимые символы и минимальная длина
    _pattern = Pattern(
        r'password ::= [a-zA-Z0-9!@#$%^&*]{8,} @fail "пароль должен содержать минимум 8 символов"'
    )

    def __init__(self, value: str) -> None:
        try:
            self._pattern.match('password', value)
        except PatternError as e:
            raise ValueError(str(e)) from None

        # Слой 2: семантика — бизнес-правила читаются как требования, не как regex
        errors = []
        if not any(c.isupper() for c in value):
            errors.append("хотя бы одна заглавная буква")
        if not any(c.isdigit() for c in value):
            errors.append("хотя бы одна цифра")
        if not any(c in '!@#$%^&*' for c in value):
            errors.append("хотя бы один спецсимвол (!@#$%^&*)")

        if errors:
            raise ValueError("Пароль должен содержать: " + ", ".join(errors))

        self._value = value

    def strength(self) -> str:
        """Оценка сложности пароля."""
        score = sum([
            len(self._value) >= 12,
            any(c.isupper() for c in self._value),
            any(c.islower() for c in self._value),
            any(c.isdigit() for c in self._value),
            any(c in '!@#$%^&*' for c in self._value),
        ])
        if score <= 3:
            return 'weak'
        if score == 4:
            return 'medium'
        return 'strong'

    def __repr__(self) -> str:
        return "Password(***)"


# ---------------------------------------------------------------------------
# Демонстрация
# ---------------------------------------------------------------------------

def demo_email() -> None:
    print("=== Email как Value Object ===\n")

    # Валидные
    email = Email("User@Example.COM")
    print(f"OK:           {email}")
    print(f"  local:      {email.local}")
    print(f"  domain:     {email.domain}")
    print(f"  tld:        {email.tld}")
    print(f"  corporate:  {email.is_corporate()}")
    print(f"  normalized: {email.normalized()}")

    print()

    # Структурные ошибки — ловит грамматика
    structural_errors = [
        ("invalid",           "нет @ — ошибка в домене"),
        ("@nodomain.com",     "нет локальной части"),
        ("user@.com",         "нет домена"),
        ("user@domain",       "нет TLD"),
    ]
    for value, comment in structural_errors:
        try:
            Email(value)
        except ValueError as e:
            print(f"  [{comment}] {e}")

    print()

    # Семантические ошибки — ловит код
    semantic_errors = [
        (".user@example.com",       "точка в начале"),
        ("user@mailinator.com",     "одноразовый домен"),
    ]
    for value, comment in semantic_errors:
        try:
            Email(value)
        except ValueError as e:
            print(f"  [{comment}] {e}")


def demo_password() -> None:
    print("\n=== Password как Value Object ===\n")
    print("Сравните с regex: ^(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%]).{8,}$")
    print("Семантика живёт в коде — читается как требования, не как заклинание.\n")

    cases = [
        ("short",         "слишком короткий"),
        ("alllowercase1!", "нет заглавных"),
        ("ALLUPPERCASE1!", "нет строчных — но это мы не проверяем, ок"),
        ("NoDigits!!!",   "нет цифры"),
        ("NoSpecial1A",   "нет спецсимвола"),
        ("Valid1Pass!",   "валидный"),
        ("Str0ng&Pass!!", "сильный"),
    ]

    for value, comment in cases:
        try:
            pwd = Password(value)
            print(f"  OK [{comment}]: strength={pwd.strength()}")
        except ValueError as e:
            print(f"  FAIL [{comment}]: {e}")


def demo_parse_dont_validate() -> None:
    print("\n=== Parse, don't validate ===\n")

    raw = "admin@google.com"

    # Старый способ: валидация — строка остаётся строкой
    import re
    if re.match(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', raw):
        # raw — всё ещё str, следующая функция не знает что мы проверили
        print(f"  validate: '{raw}' прошёл проверку (но остался строкой)")

    # Новый способ: парсинг — факт существования объекта = доказательство валидности
    email = Email(raw)
    print(f"  parse:    {email!r}")
    print(f"            corporate={email.is_corporate()}")
    print(f"            domain={email.domain}")
    print()
    print("  Email не может существовать в невалидном состоянии.")
    print("  Если объект есть — он валиден. Проверять снова не нужно.")


if __name__ == '__main__':
    demo_email()
    demo_password()
    demo_parse_dont_validate()
