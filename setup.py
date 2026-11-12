# setup.py
from setuptools import setup

try:
    with open('README.md', encoding='utf-8') as readme_file:
        long_description = readme_file.read()
except FileNotFoundError:
    long_description = 'Pattern Grammar - Читаемые паттерны вместо регулярных выражений'

setup(
    name='pattern-grammar',
    version='0.1.0',
    author='Pattern Grammar Contributors',
    author_email='pattern-grammar@example.com',
    description='Читаемые паттерны вместо регулярных выражений',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/pattern-grammar/pattern-grammar',
    packages=['pattern_grammar'],
    install_requires=[
        'lark>=1.1.0',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries',
        'Topic :: Text Processing',
    ],
    python_requires='>=3.9',
    keywords='pattern, grammar, regex, parser, bnf',
)
