
class Schema(object):
    def __init__(schema):
        schema.tables = dict()

    def add_table(schema, identifier, table):
        schema.tables[identifier] = table
