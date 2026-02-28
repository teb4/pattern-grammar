#!/usr/bin/env python3
"""
Тестирование Pattern Grammar на математических выражениях
Проверка рекурсивных правил (Lark parser)
"""
from pattern_grammar import Pattern
# =============================================================================
# 1. ГРАММАТИКА МАТЕМАТИЧЕСКИХ ВЫРАЖЕНИЙ
# =============================================================================
MATH_GRAMMAR = """
expr ::= term (("+" | "-") term)*
term ::= factor (("*" | "/") factor)*
factor ::= NUMBER | "(" expr ")"
NUMBER ::= [0-9]+
"""
# =============================================================================
# 2. ТЕСТОВЫЕ ДАННЫЕ
# =============================================================================
TEST_CASES = [
# (выражение, должно_совпасть, описание)
('123', True, 'Простое число'),
('1 + 2', True, 'Сложение'),
('1 - 2', True, 'Вычитание'),
('2 * 3', True, 'Умножение'),
('10 / 2', True, 'Деление'),
('1 + 2 * 3', True, 'Приоритет операций'),
('(1 + 2) * 3', True, 'Скобки'),
('((1 + 2) * 3)', True, 'Вложенные скобки'),
('1 + 2 + 3 + 4', True, 'Цепочка сложения'),
('1 * 2 * 3 * 4', True, 'Цепочка умножения'),
('1 + 2 * 3 - 4 / 2', True, 'Смешанные операции'),
('(1 + 2) * (3 + 4)', True, 'Две группы скобок'),
('(((1)))', True, 'Три уровня скобок'),
('1 + (2 * (3 + 4))', True, 'Вложенные скобки с операциями'),
('', False, 'Пустая строка'),
('+', False, 'Только оператор'),
('1 +', False, 'Незавершённое выражение'),
('+ 1', False, 'Оператор в начале'),
('1 2', False, 'Нет оператора между числами'),
('(1 + 2', False, 'Незакрытая скобка'),
('1 + 2)', False, 'Лишняя закрывающая скобка'),
('()', False, 'Пустые скобки'),
('1 + + 2', False, 'Два оператора подряд'),
]
# =============================================================================
# 3. ИНИЦИАЛИЗАЦИЯ
# =============================================================================
print("=" * 80)
print("ТЕСТИРОВАНИЕ МАТЕМАТИЧЕСКИХ ВЫРАЖЕНИЙ (Lark parser)")
print("=" * 80)
print()
# Создаём Pattern Grammar
pattern = Pattern(MATH_GRAMMAR)
# Показываем информацию о грамматике
info = pattern.get_info()
print("ИНФОРМАЦИЯ О ГРАММАТИКЕ:")
print("-" * 80)
print(f"Всего правил:        {info.get('total_rules', 0)}")
print(f"Правила (regex):     {info.get('regex_rules', [])}")
print(f"Правила (parser):    {info.get('parser_rules', [])}")
print()
# Проверка: используем ли Lark?
if info.get('parser_rules'):
    print("✅ Рекурсивные правила обнаружены → будет использоваться Lark parser")
else:
    print("⚠️  Рекурсивные правила НЕ обнаружены → что-то не так!")
print()
# =============================================================================
# 4. ЗАПУСК ТЕСТОВ
# =============================================================================
results = []
grammar_vs_expected = 0
grammar_errors = 0

print("РЕЗУЛЬТАТЫ ПО ТЕСТАМ:")
print("-" * 120)
header = f"{'Выражение':<25} {'Ожид.':<6} {'Результат':<10} {'GvE':<5} {'Описание'}"
print(header)
print("-" * 120)

for expr, expected, description in TEST_CASES:
    try:
        result = pattern.match('expr', expr)
    except Exception as e:
        result = f"ERROR: {e}"

    # Сравниваем с ожиданием
    g_vs_e = None
    if isinstance(result, bool):
        g_vs_e = (result == expected)
        if g_vs_e:
            grammar_vs_expected += 1
        else:
            grammar_errors += 1

    g_vs_e_status = "✅" if g_vs_e else "❌" if g_vs_e is False else "?"
    result_str = str(result)[:10]
    expr_display = expr[:23] + '..' if len(expr) > 25 else expr

    results.append({
        'expr': expr,
        'expected': expected,
        'result': result,
        'description': description,
        'g_vs_e': g_vs_e
    })

    print(f"{expr_display:<25} {str(expected):<6} {result_str:<10} {g_vs_e_status:<5} {description}")

print("-" * 120)
print()
# =============================================================================
# 5. СТАТИСТИКА
# =============================================================================
print("СТАТИСТИКА:")
print("-" * 80)
print(f"Всего тестов:                    {len(TEST_CASES)}")
print()
print("СОВПАДЕНИЯ:")
print(f"  Grammar с ожиданием:           {grammar_vs_expected}/{len(TEST_CASES)} ({grammar_vs_expected/len(TEST_CASES)*100:.1f}%)")
print()
print("РАСХОЖДЕНИЯ:")
print(f"  Grammar с ожиданием:            {grammar_errors}")
print("-" * 80)
print()
# =============================================================================
# 6. ДЕТАЛЬНЫЙ АНАЛИЗ РАСХОЖДЕНИЙ
# =============================================================================
if grammar_errors > 0:
    print("⚠️  НАЙДЕНЫ РАСХОЖДЕНИЯ!")
    print("-" * 80)
    print("📌 Grammar НЕ совпадает с ожиданием:")
    for r in results:
        if r['g_vs_e'] is False:
            print(f"  • {r['expr']}: grammar={r['result']}, ожидалось={r['expected']}")
            print(f"    → {r['description']}")
else:
    print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Lark parser работает корректно")
print()
print("=" * 80)
# =============================================================================
# 7. ПРИМЕР ДЕРЕВА РАЗБОРА
# =============================================================================
print()
print("ПРИМЕР ДЕРЕВА РАЗБОРА (2 + 3 * 4):")
print("-" * 80)
try:
    tree = pattern.parse('expr', '2 + 3 * 4')
    if tree:
        print(tree.pretty())
    else:
        print("Дерево не получено")
except Exception as e:
    print(f"Ошибка: {e}")
print()
print("ПРИМЕР ДЕРЕВА РАЗБОРА ((1 + 2) * 3):")
print("-" * 80)
try:
    tree = pattern.parse('expr', '(1 + 2) * 3')
    if tree:
        print(tree.pretty())
    else:
        print("Дерево не получено")
except Exception as e:
    print(f"Ошибка: {e}")
print("=" * 80)
