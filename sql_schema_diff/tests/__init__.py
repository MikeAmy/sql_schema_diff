
from sql_schema_diff import Schema, Difference


def test_simple_comparison():
    schema1 = Schema()
    schema1.parse("""BEGIN;
CREATE TABLE "test" (
    "id" serial PRIMARY KEY,
    "recursive_ref" integer REFERENCES "test" ("id"),
    UNIQUE("id", "recursive_ref")
);
COMMIT;
    """)
    schema2 = Schema()
    schema2.parse("""BEGIN;
CREATE TABLE "test" (
    "recursive_ref" integer REFERENCES "test" ("id"),
    "id" serial PRIMARY KEY,
    UNIQUE("recursive_ref", "id")
);
COMMIT;
    """)
    schema1.resolve_references()
    schema2.resolve_references()
    difference = Difference()
    schema1.diff(schema2, difference)
    assert not difference, difference


def test_simple_difference():
    schema1 = Schema()
    schema1.parse("""BEGIN;
CREATE TABLE "test" (
    "id" serial PRIMARY KEY,
    "recursive_ref" integer REFERENCES "test" ("id"),
    "other" varchar(1) NULL DEFAULT 'x',
    "deleted" smallint NULL DEFAULT 1,
    UNIQUE("id", "recursive_ref")
);
COMMIT;
    """)
    schema2 = Schema()
    schema2.parse("""BEGIN;
CREATE TABLE "test" (
    "recursive_ref" integer REFERENCES "test" ("id"),
    "id" serial PRIMARY KEY,
    "other" varchar(255) NOT NULL,
    "added" smallint NULL DEFAULT 1,
    UNIQUE("recursive_ref", "id")
);
COMMIT;
    """)
    schema1.resolve_references()
    schema2.resolve_references()
    difference = Difference()
    schema1.diff(schema2, difference)
    assert len(difference.changes) == 2
    assert len(difference.deletions) == 1
    assert len(difference.additions) == 1
