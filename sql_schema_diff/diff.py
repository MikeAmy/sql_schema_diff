
from sql_schema_diff.schema import Table, Index, Column
from sql_schema_diff.schema import Schema


class Difference(object):
    def __init__(diff):
        diff.additions = []
        diff.deletions = []
        diff.changes = []

    def __nonzero__(diff):
        return bool(diff.deletions or diff.additions or diff.changes)

    def __unicode__(diff):
        return (u'''%i differences:
%i additions:
    %s
%i deletions:
    %s
%i changes:
    %s
'''
        ) % (
            len(diff.additions) + len(diff.deletions) + len(diff.changes),
            len(diff.additions),
            u"\n    ".join(map(unicode, diff.additions)),
            len(diff.deletions),
            u"\n    ".join(map(unicode, diff.deletions)),
            len(diff.changes),
            u"\n    ".join(map(unicode, diff.changes))
        )

    def changed(diff, thing):
        diff.changes.append(thing)

    def compare_dicts(diff, this, other):
        this_keys = set(this.keys())
        other_keys = set(other.keys())
        for name in this_keys.intersection(other_keys):
            this[name].diff(other[name], diff)
        for name in this_keys.difference(other_keys):
            diff.deletions.append(this[name])
        for name in other_keys.difference(this_keys):
            diff.additions.append(other[name])


def Column_diff(column, other_column, diff):
    for attribute in (
        'data_type',
        'nullable',
        'primary',
        'references',
        'unsigned',
        'default',
    ):
        column_attr_value = getattr(column, attribute)
        other_attr_value = getattr(other_column, attribute)
        if column_attr_value != other_attr_value:
            diff.changed(u"%(marker)s%(column)s %(attribute)s: %(column_value)s -> %(other_value)s " % dict(
                marker=(" " if attribute == 'references' else ''),
                column=column,
                attribute=attribute,
                column_value=column_attr_value,
                other_value=other_attr_value
            ))
Column.diff = Column_diff


def Table_diff(table, other, diff):
    diff.compare_dicts(table.columns, other.columns)
    table_indices = set(table.indices)
    other_indices = set(other.indices)
    for index in table_indices.difference(other_indices):
        diff.deletions.append(index)
    for index in other_indices.difference(table_indices):
        diff.additions.append(index)
Table.diff = Table_diff


def Index_diff(index, other_index, diff):
    if index.columns != other_index.columns:
        diff.changed(index)
Index.diff = Index_diff


def Schema_diff(schema, other, diff):
    diff.compare_dicts(schema.tables, other.tables)
Schema.diff = Schema_diff
