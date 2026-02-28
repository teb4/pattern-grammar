# setup.py
from setuptools import setup

setup(
    name='pattern-grammar',
    version='0.1.0',
    author='Your Name',
    author_email='your.email@example.com',
    description='Читаемые паттерны вместо регулярных выражений',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/pattern-grammar',
    packages=['pattern_grammar'],  # ← ЯВНО указываем пакет
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
    python_requires='>=3.7',
    keywords='pattern, grammar, regex, parser, bnf',
)
