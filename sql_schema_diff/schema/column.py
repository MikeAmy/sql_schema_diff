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
        column.name = column.table.identifier + "." + column.identifier
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
        return column.name

    def __unicode__(column):
        return u"COLUMN " + column.name

    def create_index(column, unique):
        index = Index(column.name.replace(".", '_'), unique=unique)
        index.column_ids = (column.identifier,)
        column.table.add_index(index)

    def mark_primary(column):
        column.primary = True
        column.nullable = False # I guess
        column.create_index(unique=True)

    def mark_unique(column):
        column.unique = True
        column.create_index(unique=True)

    def set_data_type(column, data_type):
        assert column.data_type is None, (column, column.data_type, data_type)
        column.data_type = data_type

    def __eq__(column, other):
        return column.identifier == other.identifier

    def __ne__(column, other):
        return not column == other

    def __hash__(column):
        return hash(column.identifier)

