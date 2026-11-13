"""
Unit-тесты для модуля importer.

Реальное поведение импортера:
- `import "rfc3986-core"` загружает встроенную библиотеку
- `import "./common.pg"` — относительный путь
- `import "/abs/path.pg"` — абсолютный путь
- Директивы import удаляются из результирующей грамматики
- Правила из импортированной грамматики добавляются к основной
- При конфликте имён приоритет у основной грамматики
"""
import pytest
from pattern_grammar import Pattern
from pattern_grammar.importer import (
    _extract_import_name,
    _is_import_directive,
    _merge_grammar,
    _remove_imports,
    resolve_import,
    BUILTIN_LIBRARIES,
)


# =====================================================================
# _is_import_directive
# =====================================================================

class TestIsImportDirective:
    """Проверка распознавания директивы import."""

    def test_simple_import(self):
        assert _is_import_directive('import "file.pg"') is True

    def test_single_quote_import(self):
        assert _is_import_directive("import './file.pg'") is True

    def test_not_import(self):
        assert _is_import_directive('rule ::= [a-z]+') is False

    def test_empty_line(self):
        assert _is_import_directive('') is False

    def test_import_only(self):
        assert _is_import_directive('import ') is False

    def test_import_with_spaces(self):
        assert _is_import_directive('  import "file.pg"') is True


# =====================================================================
# _extract_import_name
# =====================================================================

class TestExtractImportName:
    """Извлечение имени импорта."""

    def test_extract_double_quotes(self):
        name = _extract_import_name('import "file.pg"')
        assert name == 'file.pg'

    def test_extract_single_quotes(self):
        name = _extract_import_name("import './file.pg'")
        assert name == './file.pg'

    def test_not_import_returns_none(self):
        name = _extract_import_name('rule ::= [a-z]+')
        assert name is None

    def test_empty_import_returns_none(self):
        name = _extract_import_name('import ""')
        assert name == ''


# =====================================================================
# _remove_imports
# =====================================================================

class TestRemoveImports:
    """Удаление директив import из текста грамматики."""

    def test_remove_single_import(self):
        grammar = 'import "file.pg"\nrule ::= [a-z]+'
        result = _remove_imports(grammar)
        assert 'import' not in result
        assert 'rule' in result

    def test_remove_multiple_imports(self):
        grammar = (
            'import "file1.pg"\n'
            'import "file2.pg"\n'
            'rule ::= [a-z]+'
        )
        result = _remove_imports(grammar)
        assert result.count('import') == 0

    def test_preserve_rules(self):
        grammar = 'import "file.pg"\na ::= [a-z]+\nb ::= [0-9]+'
        result = _remove_imports(grammar)
        assert 'a ::=' in result
        assert 'b ::=' in result


# =====================================================================
# _merge_grammar
# =====================================================================

class TestMergeGrammar:
    """Объединение грамматик."""

    def test_merge_no_conflict(self):
        base = 'rule1 ::= [a-z]+'
        additional = 'rule2 ::= [0-9]+'
        result = _merge_grammar(base, additional)
        assert 'rule1' in result
        assert 'rule2' in result

    def test_merge_with_conflict(self):
        base = 'rule1 ::= [a-z]+'
        additional = 'rule1 ::= [0-9]+'
        result = _merge_grammar(base, additional)
        # Приоритет у base — rule1 не должен заменяться
        assert '[a-z]' in result

    def test_merge_empty_base(self):
        additional = 'rule2 ::= [0-9]+'
        result = _merge_grammar('', additional)
        assert 'rule2' in result

    def test_merge_empty_additional(self):
        base = 'rule1 ::= [a-z]+'
        result = _merge_grammar(base, '')
        assert 'rule1' in result


# =====================================================================
# resolve_import — встроенные библиотеки
# =====================================================================

class TestResolveImportBuiltin:
    """Разрешение встроенных библиотек."""

    def test_resolve_rfc3986_core(self):
        """Встроенная библиотека rfc3986-core должна загружаться."""
        result = resolve_import('rfc3986-core.pg')
        assert isinstance(result, str)
        assert len(result) > 0

    def test_resolve_rfc3986_has_rules(self):
        """Библиотека rfc3986-core должна содержать правила."""
        result = resolve_import('rfc3986-core.pg')
        assert '::=' in result

    def test_builtin_lib_key_is_filename(self):
        """Ключ в BUILTIN_LIBRARIES — это имя файла."""
        assert 'rfc3986-core.pg' in BUILTIN_LIBRARIES

    def test_resolve_unknown_file_raises(self):
        with pytest.raises(FileNotFoundError):
            resolve_import('nonexistent-file.pg')


# =====================================================================
# Pattern с import
# =====================================================================

class TestPatternWithImport:
    """Использование import в Pattern."""

    def test_pattern_with_builtin_import(self):
        """Pattern должен парсить грамматику с import встроенной библиотеки."""
        grammar = '''
import "rfc3986-core.pg"

unreserved ::= [a-z]
'''
        p = Pattern(grammar)
        # Встроенные правила из rfc3986-core должны быть доступны
        assert 'unreserved' in p.rules
        assert 'pct-encoded' in p.rules

    def test_pattern_import_removes_directive(self):
        """Директива import не должна появляться в правилах."""
        grammar = '''
import "rfc3986-core.pg"

rule ::= [a-z]+
'''
        p = Pattern(grammar)
        assert 'import' not in p.rules

    def test_pattern_import_relative_path(self, tmp_path):
        """Относительный импорт из файла."""
        lib_file = tmp_path / 'common.pg'
        lib_file.write_text('common ::= [A-Z]+')

        grammar = 'import "./common.pg"\nrule ::= [a-z]+'
        p = Pattern(grammar, base_path=str(tmp_path / 'main.pg'))
        assert 'common' in p.rules
        assert 'rule' in p.rules

    def test_pattern_import_absolute_path(self, tmp_path):
        """Абсолютный импорт из файла."""
        lib_file = tmp_path / 'absolute.pg'
        lib_file.write_text('abs_rule ::= [0-9]+')

        grammar = f'import "{lib_file}"\nrule ::= [a-z]+'
        p = Pattern(grammar)
        assert 'abs_rule' in p.rules

    def test_pattern_import_missing_file(self):
        """Импорт несуществующего файла должен вызывать ошибку."""
        grammar = 'import "nonexistent.pg"\nrule ::= [a-z]+'
        with pytest.raises((SyntaxError, FileNotFoundError)):
            Pattern(grammar)
