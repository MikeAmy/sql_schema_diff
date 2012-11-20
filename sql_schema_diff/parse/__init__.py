
from sql_lexer.sql import Token
from sql_lexer.lexer import tokenize
from sql_lexer.tokens import (
    Newline, Whitespace, Punctuation, Keyword, Comment, Name
)
from sql_lexer.keywords import KEYWORDS

from sql_schema_diff import Schema, Table, Index, Column

assert 'VARCHAR' in KEYWORDS

whitespace_or_comment = (Newline, Whitespace, Comment.Single)


class Tokens(object):
    def __init__(tokens, pairs, unneeded=whitespace_or_comment):
        tokens.pairs = [pair for pair in pairs if pair[0] not in unneeded]

    def split(tokens, joining_token, use_tokens):
        piece = []
        split_ttype = joining_token.ttype
        split_value = joining_token.value
        for token_pair in tokens.pairs:
            ttype, value = token_pair
            if ttype is split_ttype and value == split_value:
                if piece:
                    use_tokens(Tokens(piece))
                piece = []
            else:
                piece.append(token_pair)
        if piece:
            if piece:
                use_tokens(Tokens(piece))

    def next(tokens):
        """Pops next token value"""
        return tokens.next_pair()[1]

    def next_pair(tokens):
        """Pops next token, as a pair (type, value)"""
        pair = tokens.pairs.pop(0)
        #print pair
        return pair

    def expect(tokens, *pattern):
        """Pops tokens and asserts values match pattern.
        Pattern is a variable argument list of strings and callables.

        If callables are mixed into the pattern, call them with the token
        value in their position and return the transformed values.
        """
        result = []
        for step in pattern:
            token_value = tokens.next_pair()[1]
            if callable(step):
                result.append(step(token_value))
            else:
                assert token_value == step
        return result

    def match(tokens, *patterns):
        """Takes (pattern => use_matches) pairs

        Match patterns and use the longest completely matched pattern.
        If two patterns are the longest, use the last one.
        callables must be side-effect free, and raise exceptions to indicate failure to match
        """
        matches = {}
        still_possible = []
        use_matches = {}
        longest_completely_matched_pattern = None
        for pattern, use_match in patterns:
            matches[pattern] = []
            still_possible.append(pattern)
            use_matches[pattern] = use_match
        max_pattern_length = max(map(len, matches.iterkeys()))
        for ahead in range(max_pattern_length + 1):
            token_value = tokens.pairs[ahead][1]
            for pattern in list(still_possible):
                if ahead == len(pattern):
                    # the pattern has been fully matched,
                    # keep it in case other patterns don't match
                    longest_completely_matched_pattern = pattern
                    still_possible.remove(pattern)
                else:
                    pattern_step = pattern[ahead]
                    if callable(pattern_step):
                        try:
                            # add a result
                            matches[pattern].append(pattern_step(token_value))
                        except:
                            # callable failed => mismatch
                            still_possible.remove(pattern)
                    else:
                        if token_value != pattern_step:
                            # mismatch
                            still_possible.remove(pattern)
                        else:
                            # match
                            pass
        if longest_completely_matched_pattern is None:
            raise Exception(
                "Can't match %s from %s" % (
                    matches,
                    tokens.pairs[:max_pattern_length]
                )
            )
        else:
            matched_pattern = longest_completely_matched_pattern
            for pattern_step in matched_pattern:
                tokens.pairs.pop(0)
            use_matches[matched_pattern](*matches[matched_pattern])

    def __nonzero__(tokens):
        return len(tokens.pairs) > 0


def sqlid(identifier):
    id = identifier.strip('"')
    assert id != ','
    return id


class Parser(object):
    def method(parser, keyword):
        """Returns the parsing method specified by keyword.

        Raises an exception if not found.
        """
        try:
            method = getattr(parser, keyword)
        except AttributeError:
            raise Exception(
                "%s: Could not parse %s" % (
                    parser,
                    keyword,
                )
            )
        else:
            method()

class ColumnParser(Parser):
    def __init__(parser, column, tokens):
        parser.column = column
        parser.tokens = tokens

    def parse(parser):
        tokens = parser.tokens
        while tokens:
            token_type, token_value = tokens.next_pair()
            if token_value in (u',', u')'):
                return
            else:
                keyword = token_value.upper().replace(' ', '_')
                parser.method(keyword)

    def VARCHAR(parser):
        parser.tokens.match(
            (('(', int, ')'), parser.column.set_varchar)
        )

    def NUMERIC(parser):
        parser.tokens.match(
            (('(', int, ',', int, ')'), parser.column.set_numeric)
        )

    def UUID(parser):
        parser.column.set_data_type("UUID")

    def INTEGER(parser):
        parser.column.set_data_type("numeric(32)")

    def DATETIME(parser):
        parser.column.set_data_type("datetime")

    def TIMESTAMP(parser):
        parser.tokens.match(
            ((),
                lambda: parser.column.set_data_type("datetime")),
            (('with', 'time', 'zone'),
                lambda: parser.column.set_data_type("datetime with time zone"))
        )

    def TIMESTAMP_WITH_TIME_ZONE(parser):
        parser.column.set_data_type("datetime with time zone")

    def DATE(parser):
        parser.column.set_data_type("date")

    def BOOL(parser):
        parser.column.set_data_type("boolean")
    BOOLEAN = BOOL

    def BIGINT(parser):
        parser.column.set_data_type('numeric(64)')

    def DECIMAL(parser):
        parser.column.set_data_type('decimal')

    def TEXT(parser):
        parser.column.set_data_type('text')

    def SMALLINT(parser):
        parser.column.set_data_type('numeric(16)')

    def CHAR(parser):
        parser.tokens.match(
            (('(', int, ')'), parser.column.set_char),
            ((), lambda: parser.column.set_data_type('char'))
        )

    def NOT_NULL(parser):
        parser.column.nullable = False

    def NOT(parser):
        parser.tokens.match(
            (("NULL",), parser.column.set_nullable)
        )

    def NULL(parser):
        parser.column.nullable = True

    def UNIQUE(parser):
        parser.column.mark_unique()

    def PRIMARY(parser):
        parser.tokens.match(
            ((), parser.column.mark_primary),
            (('KEY',), parser.column.mark_primary)
        )

    def UNSIGNED(parser):
        parser.column.signed = True

    def DEFAULT(parser):
        parser.default = parser.tokens.next()

    def SERIAL(parser):
        column = parser.column
        column.serial = True
        column.set_data_type("numeric(32)")
        # postgres:
        column.default = "nextval('%s_%s_seq'::regclass)" % (
            column.table.identifier,
            column.identifier
        )

    def REFERENCES(parser):
        parser.tokens.match(
            ((sqlid, '(', sqlid, ')'), parser.column.set_reference)
        )

    def DEFERRABLE(parser):
        parser.column.deferrable = True
        parser.tokens.match(
            (("INITIALLY", "DEFERRED"), lambda: None),
            ((), lambda: None)
        )

    def CHECK(parser):
        # TODO: use CHECKs
        tokens = parser.tokens
        if tokens.next() == '(':
            nesting = 1
            while nesting != 0:
                next = tokens.next()
                if next == "(":
                    nesting += 1
                elif next == ")":
                    nesting -= 1


class TableParser(Parser):
    def __init__(parser, table, tokens):
        parser.table = table
        parser.tokens = tokens

    def parse(parser):
        tokens = parser.tokens
        tokens.expect('(')
        while tokens:
            token_type, token_value = tokens.next_pair()
            # Should only be Keyword. Problem in the lexer.
            if token_type in (Keyword, Name):
                parser.method(token_value)
            elif token_value == ')':
                break
            elif token_value == ',':
                continue
            else:
                column_identifier = sqlid(token_value)
                table = parser.table
                column = Column(table.schema,
                                table,
                                table.ordinal_position,
                                column_identifier)
                table.ordinal_position += 1
                ColumnParser(column, tokens).parse()
                table.add_column(column_identifier, column)
#        assert not tokens

    def UNIQUE(parser):
        table = parser.table
        index_parser = IndexParser(Index("uniq", unique=True), table, parser.tokens)
        index_parser.parse(table.identifier)

    def ADD_CONSTRAINT(parser):
        table = parser.table
        tokens = parser.tokens
        constraint_id, constraint_type = tokens.expect(sqlid, str)
        if constraint_type == "FOREIGN":
            column_id, foreign_table_id, foreign_column_id = tokens.expect(
                'KEY', '(', sqlid, ')', 'REFERENCES', sqlid, '(', sqlid, ')'
            )
            column = table.columns[column_id]
            column.references = foreign_table_id, foreign_column_id
            if tokens.next() == "DEFERRABLE":
                if tokens.next() == "INITIALLY":
                    tokens.expect('DEFERRED')
        else:
            raise Exception(
                "Don't understand ADD CONSTRAINT syntax for %s" % constraint_id
            )


class IndexParser(Parser):
    def __init__(parser, index, table, tokens):
        parser.index = index
        parser.table = table
        parser.tokens = tokens

    def parse(parser, identifier):
        table = parser.table
        index = parser.index
        tokens = parser.tokens
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
        index.varchar_pattern_ops = varchar_pattern_ops
        table.add_index(index)


class SchemaParser(Parser):
    def __init__(parser, schema, statements_string):
        parser.schema = schema
        parser.schema_tokens = Tokens(tokenize(statements_string))

    def parse(parser):
        parser.schema_tokens.split(Token(Punctuation, ';'), parser.parse_statement)

    def parse_statement(parser, statement_tokens):
        parser.tokens = statement_tokens
        parser.method(statement_tokens.next())

    # ignored statements:
    def BEGIN(parser):
        pass

    def COMMIT(parser):
        pass

    # alter statements
    def ALTER(parser):
        tokens = parser.tokens
        if tokens.next() == "TABLE":
            table_name = sqlid(tokens.next())
            schema = parser.schema
            table = schema.tables[table_name]
            keyword = tokens.next()
            if keyword == "ADD":
                keyword = keyword + "_" + tokens.next()
            TableParser(table, tokens).method(keyword)

    # create statements
    def CREATE(parser):
        tokens = parser.tokens
        keyword = tokens.next()
        if keyword == "UNIQUE":
            keyword = keyword + "_" + tokens.next()
        parser.method("CREATE_" + keyword)

    def CREATE_TABLE(parser):
        tokens = parser.tokens
        schema = parser.schema
        identifier = sqlid(tokens.next())
        table = Table(schema, identifier)
        TableParser(table, tokens).parse()
        schema.tables[identifier] = table

    # create index statements
    def parse_index(parser, unique):
        schema = parser.schema
        tokens = parser.tokens
        identifier = sqlid(tokens.next())
        index = Index(identifier, unique=unique)
        table_id, = tokens.expect('ON', sqlid)
        table = schema.tables[table_id]
        IndexParser(index, table, tokens).parse(identifier)

    def CREATE_INDEX(parser):
        parser.parse_index(False)

    def CREATE_UNIQUE_INDEX(parser):
        parser.parse_index(True)


def Schema_parse(schema, statements_string):
    statements_string=("\n".join(string for string in statements_string.split("\n") if not string.startswith("--")))
    SchemaParser(schema, statements_string).parse()
Schema.parse = Schema_parse
