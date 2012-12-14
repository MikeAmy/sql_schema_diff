from distutils.core import setup
import os

setup(
    name='sql_schema_diff',
    version='1.0',
    description='Python SQL Schema Parsing and Diffing',
    author='Mike Amy',
    author_email='cocoade@googlemail.com',
    url='https://github.com/MikeAmy/python_sql_schema_comparison',
    packages=[
        'sql_schema_diff',
        'sql_schema_diff.schema',
        'sql_schema_diff.parse',
        'sql_schema_diff.introspect',
    ],
    keywords=['SQL', 'database', 'schema', 'postgres', 'sqlite', 'diff'],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
    ],
    long_description=open(
        os.path.join(os.path.dirname(__file__), 'readme.rst'),
    ).read().strip(),
#    install_requires=['sql_lexer']
)
