
from . import Column, Index, Schema, Table


def Schema_resolve_references(schema):
    for table in schema.tables.itervalues():
        table.resolve_references(schema.tables)
Schema.resolve_references = Schema_resolve_references


def Table_resolve_references(table, other_tables):
    for column in table.columns.itervalues():
        column.resolve_references(other_tables)
    for index in table.indices:
        index.resolve_references(table)
Table.resolve_references = Table_resolve_references


def Column_resolve_references(column, tables):
    if isinstance(column.references, tuple):
        other_table_name, other_column_id = column.references
        other_table = tables[other_table_name]
        column.references = other_table.resolve_column(other_column_id)
        # Postgres adds indices for foreign keys
        index = Index(column.identifier.replace(".", '_') + "_" + column.references.identifier.replace(".", "_"))
        index.unique = False
        index.columns = (column,)
        column.table.add_index(index)
Column.resolve_references = Column_resolve_references


def Index_resolve_references(index, table):
    column_list = map(table.resolve_column, index.column_ids)
    # sort columns if postgres
    column_list.sort(key=lambda column:column.identifier)
    index.columns = tuple(column_list)
Index.resolve_references = Table_resolve_references


def Table_resolve_column(table, column_spec):
    if isinstance(column_spec, Column):
        return column_spec
    elif isinstance(column_spec, int):
        return table.column_at_index(column_spec)
    else:
        return table.columns[column_spec]
Table.resolve_column = Table_resolve_column
