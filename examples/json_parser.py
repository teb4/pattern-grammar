#!/usr/bin/env python3
"""
Тестирование Pattern Grammar на JSON
Сравнение результатов с ожидаемыми значениями
(Версия с расширенной статистикой по образцу test_url_rfc3986.py)
"""
from pattern_grammar import Pattern

# =============================================================================
# 1. ГРАММАТИКА JSON
# =============================================================================

JSON_GRAMMAR = """
json ::= value

# Основные типы JSON
value ::= object
        | array
        | string
        | number
        | boolean
        | null

# Объекты
object ::= "{" "}"
         | "{" members "}"

members ::= member ("," member)*

member ::= string ":" value

# Массивы
array ::= "[" "]"
        | "[" elements "]"

elements ::= value ("," value)*

# Строки
string ::= '"' chars '"'

# Символы внутри строки (все кроме кавычки и обратной косой)
chars ::= [^"\\\\]+

# Числа
number ::= "-"? integer fractional? exponent?

integer ::= [0-9]+

fractional ::= "." [0-9]+

exponent ::= [eE] ("+" | "-")? [0-9]+

# Литералы
boolean ::= "true" | "false"
null    ::= "null"

# Базовые компоненты
digit ::= [0-9]
"""

# =============================================================================
# 2. ТЕСТОВЫЕ ДАННЫЕ
# =============================================================================
TEST_CASES = [
    # Простые значения
    ('"hello"', True, 'Простая строка'),
    ('123', True, 'Целое число'),
    ('123.456', True, 'Дробное число'),
    ('-42', True, 'Отрицательное число'),
    ('true', True, 'Boolean true'),
    ('false', True, 'Boolean false'),
    ('null', True, 'Null'),
    # Объекты
    ('{}', True, 'Пустой объект'),
    ('{"key": "value"}', True, 'Простой объект'),
    ('{"a": 1, "b": 2}', True, 'Объект с несколькими полями'),
    ('{"nested": {"inner": true}}', True, 'Вложенный объект'),
    # Массивы
    ('[]', True, 'Пустой массив'),
    ('[1, 2, 3]', True, 'Массив чисел'),
    ('["a", "b", "c"]', True, 'Массив строк'),
    ('[1, "two", true, null]', True, 'Массив смешанных типов'),
    ('[[1, 2], [3, 4]]', True, 'Массив массивов'),
    # Сложные структуры
    ('{"users": [{"name": "Alice"}, {"name": "Bob"}]}', True, 'Объект с массивом объектов'),
    ('{"config": {"debug": true, "ports": [80, 443, 8080]}}', True, 'Сложная вложенность'),
    ('{"a": {"b": {"c": {"d": 1}}}}', True, 'Глубокая вложенность объектов'),
    ('[[[[1]]]]', True, 'Глубокая вложенность массивов'),
    # Числа с экспонентой
    ('1e10', True, 'Число с экспонентой'),
    ('1.5e-10', True, 'Число с отрицательной экспонентой'),
    ('1E+5', True, 'Число с E+'),
    # Невалидные
    ('', False, 'Пустая строка'),
    ('{', False, 'Незакрытый объект'),
    ('{"key": }', False, 'Отсутствует значение'),
    ('{"key" "value"}', False, 'Отсутствует двоеточие'),
    ('[1, 2, 3', False, 'Незакрытый массив'),
    ('[1, , 2]', False, 'Лишняя запятая'),
    ('{"a": 1, "a": 2}', True, 'Дубликат ключей'),
    ('unquoted', False, 'Нецитированная строка'),
    ('{"key": undefined}', False, 'undefined не в JSON'),
    ("{'key': 'value'}", False, 'Одинарные кавычки'),
    ('{"key": "value",}', False, 'Лишняя запятая в конце'),
]

# =============================================================================
# 3. ИНИЦИАЛИЗАЦИЯ
# =============================================================================
print("=" * 90)
print("ТЕСТИРОВАНИЕ JSON (Pattern Grammar)")
print("=" * 90)
print()

# Создаём Pattern Grammar
try:
    pattern = Pattern(JSON_GRAMMAR)
    print("✅ Pattern Grammar успешно загружена")
except Exception as e:
    print(f"❌ Ошибка загрузки грамматики: {e}")
    import sys
    sys.exit(1)

print("\n" + "=" * 90 + "\n")

# =============================================================================
# 4. ИНФОРМАЦИЯ О ГРАММАТИКЕ
# =============================================================================
print("ИНФОРМАЦИЯ О ГРАММАТИКЕ:")
print("-" * 90)
info = pattern.get_info()
print(f"Всего правил:        {info.get('total_rules', 0)}")
print(f"Правила (regex):     {info.get('regex_rules', [])}")
print(f"Правила (parser):    {info.get('parser_rules', [])}")
print()
if info.get('parser_rules'):
    print("✅ Рекурсивные правила обнаружены → будет использоваться Lark parser")
else:
    print("⚠️  Рекурсивные правила НЕ обнаружены → что-то не так!")
print()

# Счётчики
grammar_matches = 0
grammar_vs_expected = 0

# =============================================================================
# 5. ЗАПУСК ТЕСТОВ
# =============================================================================
results = []
for json_str, expected, description in TEST_CASES:
    # Тестируем Pattern Grammar
    try:
        grammar_result = pattern.match('json', json_str)
        if grammar_result:
            grammar_matches += 1
    except Exception as e:
        grammar_result = False

    # Сравниваем с ожиданием (логика из test_url_rfc3986.py)
    g_vs_e = (grammar_result == expected)
    if g_vs_e:
        grammar_vs_expected += 1

    results.append({
        'json': json_str,
        'expected': expected,
        'grammar': grammar_result,
        'description': description,
        'g_vs_e': g_vs_e
    })

# =============================================================================
# 6. ВЫВОД РЕЗУЛЬТАТОВ
# =============================================================================
print("РЕЗУЛЬТАТЫ ПО ТЕСТАМ:")
print("-" * 120)
header = f"{'JSON':<50} {'Ожид.':<6} {'Grammar':<8} {'GvE':<5} {'Описание'}"
print(header)
print("-" * 120)
for r in results:
    # Формируем статус
    g_vs_e_status = "✅" if r['g_vs_e'] else "❌"

    grammar_str = str(r['grammar'])[:6]
    json_display = r['json'][:48] + '..' if len(r['json']) > 50 else r['json']

    print(f"{json_display:<50} {str(r['expected']):<6} {grammar_str:<8} "
          f"{g_vs_e_status:<5} {r['description']}")
print("-" * 120)
print()

# =============================================================================
# 7. СТАТИСТИКА
# =============================================================================
print("СТАТИСТИКА:")
print("-" * 90)
print(f"Всего тестов:                    {len(TEST_CASES)}")
print()
print("СОВПАДЕНИЯ:")
print(f"  Grammar с ожиданием:           {grammar_vs_expected}/{len(TEST_CASES)} ({grammar_vs_expected/len(TEST_CASES)*100:.1f}%)")
print()
print("РАСХОЖДЕНИЯ:")
grammar_errors = len(TEST_CASES) - grammar_vs_expected
print(f"  Grammar с ожиданием:           {grammar_errors}")
print("-" * 90)
print()

# Детальный анализ расхождений
if grammar_errors > 0:
    print("⚠️  НАЙДЕНЫ РАСХОЖДЕНИЯ!")
    print("-" * 90)
    print("\n📌 Grammar НЕ совпадает с ожиданием:")
    for r in results:
        if r['g_vs_e'] is False:
            print(f"  • {r['json']}: grammar={r['grammar']}, ожидалось={r['expected']}")
            print(f"    → {r['description']}")
else:
    print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Pattern Grammar корректно обрабатывает JSON")
print()
print("=" * 90)

# =============================================================================
# 8. ПРИМЕР ДЕРЕВА РАЗБОРА
# =============================================================================
print()
print("ПРИМЕР ДЕРЕВА РАЗБОРА (сложный JSON):")
print("-" * 90)
try:
    tree = pattern.parse('json', '{"users": [{"name": "Alice"}, {"name": "Bob"}]}')
    if tree:
        print(tree.pretty())
    else:
        print("Дерево не получено")
except Exception as e:
    print(f"Ошибка: {e}")
print("=" * 90)
