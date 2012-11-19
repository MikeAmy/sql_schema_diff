from sql_schema_diff.schema import Index

class Column(object):
    def __init__(column, schema, table, ordinal_position, identifier,
        data_type=None,
        nullable=True,
        unique=False,
        primary=False,
        references=None,
        unsigned=None,
        default=None,
        serial=False,
        deferrable=False
    ):
        column.schema = schema
        column.table = table

        column.identifier = identifier
        column.ordinal_position = ordinal_position

        column.data_type = data_type
        column.nullable = nullable
        column.unique = unique
        column.primary = primary
        column.references = references
        column.unsigned = unsigned
        column.default = default
        column.serial = serial
        column.deferrable = deferrable

    def __repr__(column):
        return column.identifier

    def __unicode__(column):
        return u"FIELD " + column.identifier

    def mark_primary(column):
        column.primary = True
        column.nullable = False # I guess
        index = Index(column.identifier.replace(".", '_'), unique=True)
        index.column_ids = (column.identifier,)
        column.table.add_index(index)

    def mark_unique(column):
        column.unique = True
        index = Index(column.identifier.replace(".", '_'), unique=True)
        index.column_ids = (column.identifier,)
        column.table.add_index(index)

    def set_data_type(column, data_type):
        assert column.data_type is None, (column, column.data_type, data_type)
        column.data_type = data_type

    def __eq__(column, other):
        return column.identifier == other.identifier

    def __ne__(column, other):
        return not column == other

    def __hash__(column):
        return hash(column.identifier)

