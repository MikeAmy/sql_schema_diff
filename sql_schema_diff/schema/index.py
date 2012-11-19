

class Index(object):
    def __init__(index, identifier, unique):
        index.identifier = identifier
        index.column_ids = None
        index.unique = unique
        index.varchar_pattern_ops = False

    def __repr__(index):
        return u"%sINDEX %s (%s)" % (("UNIQUE " if index.unique else ""),
                                     index.identifier,
                                     ", ".join(map(repr, index.columns)))

    def __hash__(index):
        hashcode = 0
        for column in index.columns:
            hashcode ^= hash(column)
        return hashcode

    def __eq__(index, other):
        return (
            other.unique == index.unique
            and other.columns == index.columns
            and index.varchar_pattern_ops == other.varchar_pattern_ops
        )

    def __ne__(index, other):
        return not index == other
