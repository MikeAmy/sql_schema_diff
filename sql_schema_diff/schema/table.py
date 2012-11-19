

class Table(object):
    def __init__(table, schema, identifier):
        table.schema = schema
        table.identifier = identifier
        table.columns = {}
        table.indices = []
        table.ordinal_position = 0

    def __repr__(table):
        return u"TABLE " + table.identifier

    def add_index(table, index):
        table.indices.append(index)

    def add_column(table, column_identifier, column):
        table.columns[column_identifier] = column

    def column_at_index(table, index):
        for column in table.columns.itervalues():
            if column.ordinal_position == index:
                return column
        raise IndexError("Can't find column at index %i in %s" % (index, table))
