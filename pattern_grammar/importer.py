"""
Импорт внешних грамматик в Pattern Grammar.

Поддерживает:
- import "путь/к/файлу.pg"  — импорт из файла
- import "rfc3986-core"      — импорт из встроенной библиотеки
- import "./common.pg"       — относительный путь

Синтаксис:
    import "путь"

Пример:
    import "rfc3986-core"

    url ::= scheme "://" authority path? query? fragment?
    scheme ::= "http" | "https"
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

from .constants import (
    IMPORT_KEYWORD,
    PG_EXTENSION,
    PG_GLOB_PATTERN,
    RULE_SEPARATOR_DOUBLE,
    RULE_SEPARATOR_SINGLE,
    ENCODING_UTF8,
)
# Встроенная мини-библиотека общих правил
BUILTIN_LIBRARIES: Dict[str, str] = {}

# Каталог для встроенных библиотек (может быть расширен)
BUILTIN_DIR: Optional[str] = None


def _load_builtin_libraries():
    """Загружает встроенные библиотеки из пакета."""
    global BUILTIN_LIBRARIES, BUILTIN_DIR

    if BUILTIN_LIBRARIES:
        return  # Уже загружено

    # Пытаемся найти библиотеки в пакете
    try:
        from importlib import resources
    except ImportError:
        import importlib_resources as resources  # type: ignore[import-not-found]

    try:
        lib_dir = resources.files('pattern_grammar.lib')
        # resources.files() возвращает Traversable или pathlib.Path
        if hasattr(lib_dir, 'iter_contents'):
            # Traversable (zip-safe / namespace package)
            for file_name in lib_dir.iter_contents():
                full_path = lib_dir / file_name
                is_pg_file = (full_path.is_file() and full_path.suffix == PG_EXTENSION)
                if is_pg_file:
                    name = full_path.name
                    BUILTIN_LIBRARIES[name] = full_path.read_text(
                        encoding=ENCODING_UTF8
                    )
        else:
            # pathlib.Path (обычный пакет)
            for fp in lib_dir.glob(PG_GLOB_PATTERN):
                if fp.is_file():
                    BUILTIN_LIBRARIES[fp.name] = fp.read_text(
                        encoding=ENCODING_UTF8
                    )
    except Exception:
        pass  # Библиотеки не найдены — не критично


# Автозагрузка при импорте
_load_builtin_libraries()


def _extract_import_name(line: str) -> Optional[str]:
    """
    Извлекает имя из директивы import.

    Поддерживаемые форматы:
        import "file.pg"
        import './file.pg'
        import "rfc3986-core"

    :param line: Строка с директивой import
    :return: Импортируемый путь или None
    """
    line = line.strip()

    # Проверяем, что это директива import
    if not line.startswith(IMPORT_KEYWORD):
        return None

    import_part = line[len(IMPORT_KEYWORD):].strip()

    # Извлекаем путь из кавычек
    is_double_quoted = (import_part.startswith('"') and import_part.endswith('"'))
    if is_double_quoted:
        return import_part[1:-1]
    is_single_quoted = (import_part.startswith("'") and import_part.endswith("'"))
    if is_single_quoted:
        return import_part[1:-1]

    return None


def _is_import_directive(line: str) -> bool:
    """Проверяет, является ли строка директивой import."""
    stripped = line.strip()
    return stripped.startswith(IMPORT_KEYWORD) and len(stripped) > len(IMPORT_KEYWORD)


def _merge_grammar(
    base: str,
    additional: str,
    base_path: Optional[str] = None,
) -> str:
    """
    Объединяет две грамматики, предотвращая конфликты имён правил.

    Если в обеих грамматиках есть правило с одинаковым именем,
    приоритет у base (импортирующая грамматика).

    :param base: Основная грамматика
    :param additional: Импортируемая грамматика
    :param base_path: Базовый путь для разрешения относительных импортов
    :return: Объединённая грамматика
    """
    existing_rules = _extract_rule_names(base)
    additional_cleaned = _remove_imports(additional)

    # Если в additional есть правила, которых нет в base — добавляем
    additional_rules = _extract_rule_names(additional_cleaned)
    new_rules = [r for r in additional_rules if r not in existing_rules]

    if new_rules:
        return base + '\n\n' + additional_cleaned

    return base


def _extract_rule_names(grammar_text: str) -> List[str]:
    """
    Извлекает имена всех правил из текста грамматики.

    :param grammar_text: Текст грамматики
    :return: Список имён правил
    """
    names: List[str] = []
    for line in grammar_text.split('\n'):
        stripped = line.strip()
        has_separator = (RULE_SEPARATOR_DOUBLE in stripped or RULE_SEPARATOR_SINGLE in stripped)
        if has_separator:
            sep = RULE_SEPARATOR_DOUBLE if RULE_SEPARATOR_DOUBLE in stripped else RULE_SEPARATOR_SINGLE
            name = stripped.split(sep, 1)[0].strip()
            if name:
                names.append(name)
    return names


def _remove_imports(grammar_text: str) -> str:
    """
    Удаляет директивы import из текста грамматики.

    :param grammar_text: Текст грамматики с импортами
    :return: Текст без директив import
    """
    lines = grammar_text.split('\n')
    filtered = [line for line in lines if not _is_import_directive(line)]
    return '\n'.join(filtered)


def resolve_import(
    import_path: str,
    base_path: Optional[str] = None,
) -> str:
    """
    Разрешает импорт и возвращает текст грамматики.

    Порядок разрешения:
    1. Встроенная библиотека (BUILTIN_LIBRARIES)
    2. Файл на диске (относительный или абсолютный путь)

    :param import_path: Путь импорта
    :param base_path: Базовый путь для относительных импортов
    :return: Текст грамматики
    :raises FileNotFoundError: Если ресурс не найден
    """
    # 1. Встроенная библиотека
    if import_path in BUILTIN_LIBRARIES:
        return BUILTIN_LIBRARIES[import_path]

    # 2. Разрешение пути на диске (встроено вместо _resolve_import_path)
    path = Path(import_path)
    is_relative_with_base = (not path.is_absolute() and base_path)
    if is_relative_with_base:
        path = Path(base_path).parent / path
    resolved = path.resolve()

    if not os.path.exists(resolved):
        raise FileNotFoundError(
            f"Файл импорта не найден: '{import_path}' "
            f"(разрешено как: '{resolved}')"
        )

    # 3. Чтение файла (встроено вместо _read_grammar_file)
    with open(resolved, 'r', encoding=ENCODING_UTF8) as f:
        return f.read()
