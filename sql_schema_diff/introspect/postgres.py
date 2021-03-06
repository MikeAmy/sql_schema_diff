
from sql_schema_diff import Schema, Column, Index, Table
from sql_schema_diff.parse import ColumnParser


def Table_introspect_postgres(table, tables, introspection, cursor):
    # Field indices
    columns = table.columns
    for column_name, info_dict in introspection.get_indexes(cursor, table.identifier).iteritems():
        column = columns[column_name]
        if info_dict['primary_key']:
            column.mark_primary()
        if info_dict['unique']:
            column.mark_unique()
    del column

    # Foreign keys
    for column_index, (column_index_other_table, other_table_name) in introspection.get_relations(cursor,
                                                                                                  table.identifier).iteritems():
        column = table.column_at_index(column_index)
        column.references = (other_table_name, column_index_other_table)

    # Indices
    cursor.execute("SELECT relname, indkey, indisunique "
                   "FROM pg_class, pg_index "
                   "WHERE pg_class.oid = pg_index.indexrelid "
                   "AND left(pg_class.relname, 3) <> 'pg_' "
                   "AND pg_class.oid IN ( "
                   "    SELECT indexrelid FROM pg_index, pg_class "
                   "    WHERE pg_class.relname='%s'"
                   "        AND pg_class.oid=pg_index.indrelid "
                   "        AND indisprimary != 't' "
                   ");" % table.identifier)
    for index_name, index_column_numbers, indisunique in cursor.fetchall():
        index = Index(index_name, unique=indisunique)
        index.varchar_pattern_ops = index_name.endswith('_like') # can also look for indclass == 10057
        index.column_ids = map(lambda s: int(s) - 1, str(index_column_numbers).split())
        table.add_index(index)

Table.introspect_postgres = Table_introspect_postgres


def Schema_introspect_postgres(schema, connection):
    cursor = connection.cursor()
    introspection = connection.introspection
    for table_name in introspection.table_names():
        schema.tables[table_name] = Table(schema, table_name)

    # Fields:
    # missing: unsigned
    cursor.execute(
        "SELECT table_name, column_name, ordinal_position, data_type, is_nullable, character_maximum_length, "
        "numeric_precision, numeric_scale, column_default "
        "FROM information_schema.columns "
        "WHERE table_schema='public' AND position('_' in table_name) <> 1;")
    for (table_name, column_name, ordinal_position, data_type, is_nullable,
         character_maximum_length, numeric_precision, numeric_scale, column_default) in cursor.fetchall():
        table = schema.tables[table_name]
        column = Column(schema, table, ordinal_position - 1, column_name)
        column.nullable = (is_nullable == "YES")
        if character_maximum_length:
            column.set_varchar(character_maximum_length)
        elif numeric_precision:
            column.set_numeric(numeric_precision, numeric_scale)
        else:
            # HACK: should not be using a parser
            column_parser = ColumnParser(column, None)
            column_parser.method(data_type.upper().replace(" ", "_"))
        if column_default:
            column.default = column_default
        table.add_column(column_name, column)

    # Table level introspection:
    for table_name, table in schema.tables.iteritems():
        table.introspect_postgres(schema.tables, introspection, cursor)

Schema.introspect_postgres = Schema_introspect_postgres
