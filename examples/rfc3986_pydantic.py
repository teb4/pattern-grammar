#!/usr/bin/env python3
"""
Пример: RFC 3986 URI + Pydantic-интеграция.

Показывает как та же грамматика из rfc3986_full.py используется
в Pydantic-моделях — без изменения самой грамматики.

Требует опциональной зависимости:
    pip install pattern-grammar[pydantic]
"""
from __future__ import annotations

import sys

try:
    import pydantic  # noqa: F401
except ModuleNotFoundError:
    sys.exit(
        "Ошибка: для работы примера требуется Pydantic.\n"
        "    pip install pattern-grammar[pydantic]"
    )

from typing import Annotated

from pydantic import BaseModel, ValidationError

from pattern_grammar import Pattern
from pattern_grammar.integrations.pydantic import PatternType, PatternValidator

# Импортируем грамматику из основного примера — грамматика не меняется
from rfc3986_full import RFC3986_GRAMMAR

# =============================================================================
# Загружаем грамматику один раз, переиспользуем во всех моделях
# =============================================================================

grammar = Pattern(RFC3986_GRAMMAR)


# =============================================================================
# Пример 1: PatternType в модели
# Валидируем URI целиком — scheme + authority + path + query + fragment
# =============================================================================

class WebhookConfig(BaseModel):
    """Конфигурация webhook: оба поля — валидные URI по RFC 3986."""

    callback_url: PatternType(grammar, 'uri')
    redirect_uri: PatternType(grammar, 'uri')


def example_basic_model() -> None:
    print("=== Пример 1: PatternType в модели ===")

    cfg = WebhookConfig(
        callback_url="https://api.example.com/webhook",
        redirect_uri="https://app.example.com/oauth/callback",
    )
    print(f"OK: callback={cfg.callback_url}")
    print(f"    redirect={cfg.redirect_uri}")

    try:
        WebhookConfig(callback_url="not a uri at all", redirect_uri="https://ok.com")
    except ValidationError as exc:
        print(f"ValidationError: {exc.errors()[0]['msg']}")


# =============================================================================
# Пример 2: Проверка отдельных компонентов URI
# Грамматика уже содержит sub-правила: scheme, host, ipv4, ipv6
# PatternType(grammar, 'scheme') работает без изменения грамматики
# =============================================================================

class DNSRecord(BaseModel):
    """DNS-запись: host отдельно, scheme отдельно."""

    scheme: PatternType(grammar, 'scheme')
    host: PatternType(grammar, 'host')
    port: str = ""


def example_sub_rules() -> None:
    print("\n=== Пример 2: Sub-правила грамматики ===")

    record = DNSRecord(scheme="https", host="192.168.1.1", port="8080")
    print(f"OK: {record.scheme}://{record.host}:{record.port}")

    try:
        DNSRecord(scheme="1invalid", host="example.com")
    except ValidationError as exc:
        print(f"Плохой scheme: {exc.errors()[0]['msg']}")

    try:
        DNSRecord(scheme="https", host="[2001:db8:::bad]")
    except ValidationError as exc:
        print(f"Плохой IPv6: {exc.errors()[0]['msg']}")


# =============================================================================
# Пример 3: Annotated — стандартный Pydantic V2 стиль
# PatternValidator напрямую, без PatternType-обёртки
# Лучше понимается IDE и mypy
# =============================================================================

# Переиспользуемые типы — определяются один раз
URI = Annotated[str, PatternValidator(grammar, 'uri')]
Scheme = Annotated[str, PatternValidator(grammar, 'scheme')]
Host = Annotated[str, PatternValidator(grammar, 'host')]

class ServiceEndpoint(BaseModel):
    """Эндпоинт сервиса с типизированными компонентами."""

    name: str
    base_url: URI
    health_url: URI


def example_annotated() -> None:
    print("\n=== Пример 3: Annotated (Pydantic V2 стиль) ===")

    svc = ServiceEndpoint(
        name="auth-service",
        base_url="https://auth.internal:9000/api/v2",
        health_url="https://auth.internal:9000/health",
    )
    print(f"OK: {svc.name} → {svc.base_url}")

    try:
        ServiceEndpoint(name="bad", base_url="://missing-scheme", health_url="https://ok.com")
    except ValidationError as exc:
        print(f"ValidationError: {exc.errors()[0]['msg']}")


# =============================================================================
# Пример 4: to_json_schema — regex vs глубокие нерекурсивные правила
#
# RFC 3986 — отличный пример: в одной грамматике есть
# простые regex-правила (scheme, hex4) и нерекурсивные, но глубокие (uri, ipv6),
# которые сжались в огромный regex.
# =============================================================================

def example_json_schema() -> None:
    print("\n=== Пример 4: JSON Schema для RFC 3986 правил ===")

    # Простые regex-правила — короткий pattern
    for rule in ('scheme', 'hex4', 'dec-octet', 'pct-encoded'):
        schema = grammar.to_json_schema(rule)
        print(f"  {rule:<15} → {schema}")

    print()

    # Глубокие нерекурсивные правила — огромный regex (но валидация работает!)
    for rule in ('uri', 'ipv6', 'ipv6_compressed', 'hier-part'):
        schema = grammar.to_json_schema(rule)
        print(f"  {rule:<15} → {schema}")

    print()
    print("  Pydantic model_json_schema для WebhookConfig:")

    import json
    schema = WebhookConfig.model_json_schema()
    print(f"  {json.dumps(schema, ensure_ascii=False, indent=4)}")


# =============================================================================
# Точка входа
# =============================================================================

if __name__ == '__main__':
    example_basic_model()
    example_sub_rules()
    example_annotated()
    example_json_schema()
