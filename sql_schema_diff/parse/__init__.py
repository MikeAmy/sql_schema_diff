
import sqlparse.lexer
from sqlparse.tokens import Newline, Whitespace, Punctuation, Keyword, Token
from sqlparse.keywords import KEYWORDS

from sql_schema_diff import Table, Index, Column

assert 'VARCHAR' in KEYWORDS

whitespace = (Newline, Whitespace)


class Tokens(object):
    def __init__(tokens, pairs, unneeded=whitespace):
        if unneeded:
            tokens.pairs = [pair for pair in pairs if pair[0] not in unneeded]
        else:
            tokens.pairs = pairs

    def split(tokens, joining_token):
        piece = []
        split_ttype = joining_token.ttype
        split_value = joining_token.value
        for token_pair in tokens.pairs:
            ttype, value = token_pair
            if ttype is split_ttype and value == split_value:
                yield Tokens(piece)
                piece = []
            else:
                piece.append(token_pair)
        if piece:
            yield Tokens(piece)

    def peek(tokens):
        """Returns next value without popping"""
        if len(tokens.pairs):
            return tokens.pairs[0][1]
        else:
            return None

    def next(tokens):
        """Pops next token value"""
        return tokens.pairs.pop(0)[1]

    def next_token_pair(tokens):
        """Pops next token, as a pair (type, value)"""
        return tokens.pairs.pop(0)

    def next_token(tokens):
        """Pops next token"""
        return Token(*tokens.pairs.pop(0))

    def expect(tokens, *pattern):
        """Pops tokens and asserts values match pattern.
        Pattern is a variable argument list of strings and callables.

        If callables are mixed into the pattern, call them with the token
        value in their position and return the transformed values.
        """
        result = []
        for step in pattern:
            token_value = tokens.pairs.pop(0)[1]
            if callable(step):
                result.append(step(token_value))
            else:
                assert token_value == step
        return result

    def __nonzero__(tokens):
        return len(tokens.pairs) > 0


def sqlid(identifier):
    id = identifier.strip('"')
    assert id != ','
    return id


class ColumnParser(object):
    def __init__(parser, column):
        parser.column = column

    def parse(parser, tokens):
        while tokens:
            token_type, token_value = tokens.next_token_pair()
            if token_value in (u',', u')'):
                return
            else:
                try:
                    parse_method = getattr(parser, token_value.upper().replace(' ', '_'))
                except AttributeError:
                    raise Exception("%s: can't parse %s token %s" % (
                        parser.column,
                        token_type,
                        token_value
                    ))
                else:
                    parse_method(tokens)

    def VARCHAR(parser, tokens):
        parser.column.set_data_type("varchar(%i)" % tokens.expect('(', int, ')'))

    def NUMERIC(parser, tokens):
        parser.column.set_data_type("numeric(%i, %i)" % tokens.expect('(', int, ',', int, ')'))

    def UUID(parser, _):
        parser.column.set_data_type("UUID")

    def INTEGER(parser, _):
        parser.column.set_data_type("numeric(32)")

    def DATETIME(parser, _):
        parser.column.set_data_type("datetime")

    def TIMESTAMP(parser, tokens):
        parser.column.set_data_type("datetime")
        if tokens.next() == "with":
            if tokens.next() == "time":
                tokens.expect("zone")
                parser.column.set_data_type("datetime with time zone")

    def TIMESTAMP_WITH_TIME_ZONE(parser, tokens):
        parser.column.set_data_type("datetime with time zone")

    def DATE(parser, _):
        parser.column.set_data_type("date")

    def BOOL(parser, _):
        parser.column.set_data_type("boolean")
    BOOLEAN = BOOL

    def BIGINT(parser, _):
        parser.column.set_data_type('numeric(64)')

    def DECIMAL(parser, _):
        parser.column.set_data_type('decimal')

    def TEXT(parser, _):
        parser.column.set_data_type('text')

    def SMALLINT(parser, _):
        parser.column.set_data_type('numeric(16)')

    def CHAR(parser, tokens):
        if tokens.peek() == '(':
            tokens.next()
            count = tokens.next()
            tokens.expect(')')
            parser.column.set_data_type("char(%s)" % count)
        else:
            parser.column.set_data_type('char')

    def NOT_NULL(parser, _):
        parser.column.nullable = False

    def NULL(parser, _):
        parser.column.nullable = True

    def UNIQUE(parser, _):
        parser.column.mark_unique()

    def PRIMARY(parser, tokens):
        if tokens.peek() == "KEY":
            tokens.next()
        parser.column.mark_primary()

    def UNSIGNED(parser, _):
        parser.column.signed = True

    def REFERENCES(parser, tokens):
        table_name = sqlid(tokens.next())
        tokens.next()
        column_id = sqlid(tokens.next())
        tokens.next()
        parser.column.references = (table_name, column_id)

    def DEFAULT(parser, tokens):
        parser.default = tokens.next()

    def SERIAL(parser, _):
        column = parser.column
        column.serial = True
        column.set_data_type("numeric(32)")
        column.default = "nextval('%s_seq'::regclass)" % column.identifier.replace(".", "_")

    def DEFERRABLE(parser, tokens):
        parser.column.deferrable = True
        if tokens.next() == 'INITIALLY':
            tokens.expect("DEFERRED")

    def CHECK(parser, tokens):
        # TODO: use CHECKs
        tokens.expect('(')
        next = tokens.next()
        while next != ")":
            next = tokens.next()
            assert next != "("
Column.Parser = ColumnParser


class TableParser(object):
    def __init__(parser, table):
        parser.table = table

    def parse(parser, tokens):
        tokens.expect('(')
        while tokens:
            token_type, token_value = tokens.next_token_pair()
            if token_type == Keyword:
                getattr(parser, token_value)(tokens)
            elif token_value == ')':
                return
            elif token_value == ',':
                continue
            else:
                column_identifier = sqlid(token_value)
                table = parser.table
                column = Column(table.schema, parser, table.ordinal_position, column_identifier)
                table.ordinal_position += 1
                column.parse(tokens)
                table.columns[column_identifier] = column

    def UNIQUE(parser, tokens):
        IndexParser(Index()).parse_index_spec(tokens)

    def ADD_CONSTRAINT(parser, tables, tokens):
        constraint_id, constraint_type = tokens.expect(sqlid, str)
        table = parser.table
        if constraint_type == "FOREIGN":
            column_id, foreign_table_id, foreign_column_id = tokens.expect('KEY', '(', sqlid, ')', 'REFERENCES', sqlid, '(', sqlid, ')')
            column = table.columns[column_id]
            column.references = foreign_table_id, foreign_column_id
            if tokens.next() == "DEFERRABLE":
                if tokens.next() == "INITIALLY":
                    tokens.expect('DEFERRED')
        else:
            raise Exception()
Table.Parser = TableParser


class IndexParser(object):
    def __init__(parser, index, table):
        parser.index = index
        parser.table = table

    def parse(parser, tokens, identifier):
        table = parser.table
        index = parser.index
        tokens.expect('(')
        column_ids = []
        varchar_pattern_ops = False
        while tokens:
            token_value = tokens.next()
            if token_value == ')':
                break
            elif token_value == ',':
                continue
            if token_value == 'varchar_pattern_ops':
                varchar_pattern_ops = True
                continue
            else:
                column_id = sqlid(token_value)
                try:
                    column_ids.append(column_id)
                except KeyError:
                    raise Exception(
                        "%s UNIQUE constraint refers to unknown column %s" % (
                            identifier,
                            column_id
                        )
                    )
        index.identifier = "_".join([table.identifier] + column_ids)
        index.column_ids = column_ids
        index.unique = True
        index.varchar_pattern_ops = varchar_pattern_ops
        table.add_index(index)

Index.Parser = IndexParser


class SchemaParser(object):
    def __init__(parser, schema):
        parser.schema = schema

    def parse(parser, statements_string):
        schema_tokens = Tokens(sqlparse.lexer.tokenize(statements_string))
        for statement_tokens in schema_tokens.split(Token(Punctuation, ';')):
            if statement_tokens:
                first_token = statement_tokens.next_token()
                try:
                    getattr(parser, first_token.value)(statement_tokens)
                except AttributeError:
                    print first_token.ttype
                    raise

    def BEGIN(parser, _):
        pass

    def COMMIT(parser, _):
        pass

    def CREATE(parser, tokens):
        keyword = tokens.next()
        if keyword == "UNIQUE":
            keyword = keyword + "_" + tokens.next()
        identifier = sqlid(tokens.next())
        getattr(parser, "CREATE_" + keyword)(identifier, tokens)

    def CREATE_TABLE(parser, identifier, tokens):
        schema = parser.schema
        table = Table(schema, identifier)
        table.parse(tokens)
        schema.tables[identifier] = table

    def parse_index(parser, identifier, index, tokens):
        schema = parser.schema
        table_id = tokens.expect('ON', sqlid)
        table = schema.tables[table_id]
        IndexParser(index, table).parse(tokens, identifier)

    def CREATE_INDEX(parser, identifier, tokens):
        index = Index(identifier)
        parser.parse_index(identifier, index, tokens)

    def CREATE_UNIQUE_INDEX(parser, identifier, tokens):
        index = Index(identifier, unique=True)
        parser.parse_index(identifier, index, tokens)

    def ALTER(parser, tokens):
        if tokens.next() == "TABLE":
            table_name = sqlid(tokens.next())
            schema = parser.schema
            table = schema.tables[table_name]
            keyword = tokens.next()
            if keyword == "ADD":
                keyword = keyword + "_" + tokens.next()
            getattr(table, keyword)(schema.tables, tokens)

schema.Parser = SchemaParser