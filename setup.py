from distutils.core import setup
import os

setup(
    name='sql_schema_diff',
    version='1.0',
    description='Python SQL Schema Parsing and Diffing',
    author='Mike Amy',
    author_email='cocoade@googlemail.com',
    url='https://github.com/MikeAmy/python_sql_schema_comparison',
    packages=['sql_schema_diff',],
    keywords=['SQL', 'database', 'schema', 'postgres', 'sqlite', 'diff'],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
    ],
    long_description=open(
        os.path.join(os.path.dirname(__file__), 'README.rst'),
    ).read().strip(),
#    install_requires=['sql_lexer']
)