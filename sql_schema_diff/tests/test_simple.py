
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

def test_comments():
    schema1 = Schema()
    schema1.parse("""
-- Comment 1
--

BEGIN; -- comment
-- Comment 2

CREATE TABLE "test" (
    "recursive_ref" integer REFERENCES "test" ("id"),
    "id" serial PRIMARY KEY,
    "other" varchar(255) NOT NULL,
    "added" smallint NULL DEFAULT 1,
    UNIQUE ("recursive_ref", "id")
)
;
-- The following references should be added but depend on non-existent tables:
-- ALTER TABLE "accounts_bookaccount" ADD CONSTRAINT "office_id_refs_id_d6f61038" FOREIGN KEY ("office_id") REFERENCES "company_office" ("id") DEFERRABLE INITIALLY DEFERRED;

COMMIT;
-- Comment 3
"""
    )


def test_big_schema():
    schema1 = Schema()
    schema1.parse("""
BEGIN;
CREATE TABLE "auth_permission" (
    "id" serial NOT NULL PRIMARY KEY,
    "name" varchar(50) NOT NULL,
    "content_type_id" integer NOT NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED,
    "codename" varchar(100) NOT NULL,
    UNIQUE ("content_type_id", "codename")
)
;
CREATE TABLE "auth_group_permissions" (
    "id" serial NOT NULL PRIMARY KEY,
    "group_id" integer NOT NULL,
    "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("group_id", "permission_id")
)
;
CREATE TABLE "auth_group" (
    "id" serial NOT NULL PRIMARY KEY,
    "name" varchar(80) NOT NULL UNIQUE
)
;
ALTER TABLE "auth_group_permissions" ADD CONSTRAINT "group_id_refs_id_3cea63fe" FOREIGN KEY ("group_id") REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE "auth_user_user_permissions" (
    "id" serial NOT NULL PRIMARY KEY,
    "user_id" integer NOT NULL,
    "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("user_id", "permission_id")
)
;
CREATE TABLE "auth_user_groups" (
    "id" serial NOT NULL PRIMARY KEY,
    "user_id" integer NOT NULL,
    "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("user_id", "group_id")
)
;
CREATE TABLE "auth_user" (
    "id" serial NOT NULL PRIMARY KEY,
    "username" varchar(30) NOT NULL UNIQUE,
    "first_name" varchar(30) NOT NULL,
    "last_name" varchar(30) NOT NULL,
    "email" varchar(75) NOT NULL,
    "password" varchar(128) NOT NULL,
    "is_staff" boolean NOT NULL,
    "is_active" boolean NOT NULL,
    "is_superuser" boolean NOT NULL,
    "last_login" timestamp with time zone NOT NULL,
    "date_joined" timestamp with time zone NOT NULL
)
;
ALTER TABLE "auth_user_user_permissions" ADD CONSTRAINT "user_id_refs_id_f2045483" FOREIGN KEY ("user_id") REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "auth_user_groups" ADD CONSTRAINT "user_id_refs_id_831107f1" FOREIGN KEY ("user_id") REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "auth_permission_content_type_id" ON "auth_permission" ("content_type_id");
CREATE TABLE "django_content_type" (
    "id" serial NOT NULL PRIMARY KEY,
    "name" varchar(100) NOT NULL,
    "app_label" varchar(100) NOT NULL,
    "model" varchar(100) NOT NULL,
    UNIQUE ("app_label", "model")
)
;
CREATE TABLE "django_session" (
    "session_key" varchar(40) NOT NULL PRIMARY KEY,
    "session_data" text NOT NULL,
    "expire_date" timestamp with time zone NOT NULL
)
;
CREATE INDEX "django_session_expire_date" ON "django_session" ("expire_date");
CREATE TABLE "django_site" (
    "id" serial NOT NULL PRIMARY KEY,
    "domain" varchar(100) NOT NULL,
    "name" varchar(50) NOT NULL
)
;
CREATE TABLE "django_admin_log" (
    "id" serial NOT NULL PRIMARY KEY,
    "action_time" timestamp with time zone NOT NULL,
    "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "content_type_id" integer REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED,
    "object_id" text,
    "object_repr" varchar(200) NOT NULL,
    "action_flag" smallint CHECK ("action_flag" >= 0) NOT NULL,
    "change_message" text NOT NULL
)
;
CREATE INDEX "django_admin_log_user_id" ON "django_admin_log" ("user_id");
CREATE INDEX "django_admin_log_content_type_id" ON "django_admin_log" ("content_type_id");
CREATE TABLE "reversion_revision" (
    "id" serial NOT NULL PRIMARY KEY,
    "manager_slug" varchar(200) NOT NULL,
    "date_created" timestamp with time zone NOT NULL,
    "user_id" integer REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "comment" text NOT NULL
)
;
CREATE TABLE "reversion_version" (
    "id" serial NOT NULL PRIMARY KEY,
    "revision_id" integer NOT NULL REFERENCES "reversion_revision" ("id") DEFERRABLE INITIALLY DEFERRED,
    "object_id" text NOT NULL,
    "object_id_int" integer,
    "content_type_id" integer NOT NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED,
    "format" varchar(255) NOT NULL,
    "serialized_data" text NOT NULL,
    "object_repr" text NOT NULL,
    "type" smallint CHECK ("type" >= 0) NOT NULL
)
;
CREATE INDEX "reversion_revision_manager_slug" ON "reversion_revision" ("manager_slug");
CREATE INDEX "reversion_revision_manager_slug_like" ON "reversion_revision" ("manager_slug" varchar_pattern_ops);
CREATE INDEX "reversion_revision_user_id" ON "reversion_revision" ("user_id");
CREATE INDEX "reversion_version_revision_id" ON "reversion_version" ("revision_id");
CREATE INDEX "reversion_version_object_id_int" ON "reversion_version" ("object_id_int");
CREATE INDEX "reversion_version_content_type_id" ON "reversion_version" ("content_type_id");
CREATE INDEX "reversion_version_type" ON "reversion_version" ("type");
CREATE TABLE "south_migrationhistory" (
    "id" serial NOT NULL PRIMARY KEY,
    "app_name" varchar(255) NOT NULL,
    "migration" varchar(255) NOT NULL,
    "applied" timestamp with time zone NOT NULL
)
;
CREATE TABLE "geo_currency" (
    "id" serial NOT NULL PRIMARY KEY,
    "code" varchar(5) NOT NULL UNIQUE,
    "name" varchar(30) NOT NULL,
    "symbol" varchar(5)
)
;
CREATE TABLE "geo_country" (
    "id" serial NOT NULL PRIMARY KEY,
    "iso_code" varchar(2) NOT NULL UNIQUE,
    "iso3_code" varchar(3) NOT NULL UNIQUE,
    "num_code" varchar(3) NOT NULL UNIQUE,
    "name" varchar(100) NOT NULL,
    "fullname" varchar(100) NOT NULL,
    "region" integer,
    "continent" varchar(2) NOT NULL,
    "currency_id" integer REFERENCES "geo_currency" ("id") DEFERRABLE INITIALLY DEFERRED
)
;
CREATE TABLE "geo_administrativeareatype" (
    "id" serial NOT NULL PRIMARY KEY,
    "name" varchar(100) NOT NULL,
    "country_id" integer NOT NULL REFERENCES "geo_country" ("id") DEFERRABLE INITIALLY DEFERRED,
    "parent_id" integer,
    "_order" integer NOT NULL,
    "lft" integer CHECK ("lft" >= 0) NOT NULL,
    "rght" integer CHECK ("rght" >= 0) NOT NULL,
    "tree_id" integer CHECK ("tree_id" >= 0) NOT NULL,
    "level" integer CHECK ("level" >= 0) NOT NULL
)
;
ALTER TABLE "geo_administrativeareatype" ADD CONSTRAINT "parent_id_refs_id_44c44985" FOREIGN KEY ("parent_id") REFERENCES "geo_administrativeareatype" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE "geo_administrativearea" (
    "id" serial NOT NULL PRIMARY KEY,
    "name" varchar(255) NOT NULL,
    "code" varchar(10),
    "parent_id" integer,
    "country_id" integer NOT NULL REFERENCES "geo_country" ("id") DEFERRABLE INITIALLY DEFERRED,
    "type_id" integer NOT NULL REFERENCES "geo_administrativeareatype" ("id") DEFERRABLE INITIALLY DEFERRED,
    "_order" integer NOT NULL,
    "lft" integer CHECK ("lft" >= 0) NOT NULL,
    "rght" integer CHECK ("rght" >= 0) NOT NULL,
    "tree_id" integer CHECK ("tree_id" >= 0) NOT NULL,
    "level" integer CHECK ("level" >= 0) NOT NULL,
    UNIQUE ("name", "country_id", "type_id")
)
;
ALTER TABLE "geo_administrativearea" ADD CONSTRAINT "parent_id_refs_id_176733b3" FOREIGN KEY ("parent_id") REFERENCES "geo_administrativearea" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE "geo_location" (
    "id" serial NOT NULL PRIMARY KEY,
    "country_id" integer NOT NULL REFERENCES "geo_country" ("id") DEFERRABLE INITIALLY DEFERRED,
    "area_id" integer REFERENCES "geo_administrativearea" ("id") DEFERRABLE INITIALLY DEFERRED,
    "type" integer NOT NULL,
    "is_capital" boolean NOT NULL,
    "is_administrative" boolean NOT NULL,
    "name" varchar(255) NOT NULL,
    "description" varchar(100),
    "lat" numeric(18, 12),
    "lng" numeric(18, 12),
    "acc" integer,
    "_order" integer NOT NULL
)
;
CREATE INDEX "geo_country_name" ON "geo_country" ("name");
CREATE INDEX "geo_country_name_like" ON "geo_country" ("name" varchar_pattern_ops);
CREATE INDEX "geo_country_fullname" ON "geo_country" ("fullname");
CREATE INDEX "geo_country_fullname_like" ON "geo_country" ("fullname" varchar_pattern_ops);
CREATE INDEX "geo_country_currency_id" ON "geo_country" ("currency_id");
CREATE INDEX "geo_administrativeareatype_name" ON "geo_administrativeareatype" ("name");
CREATE INDEX "geo_administrativeareatype_name_like" ON "geo_administrativeareatype" ("name" varchar_pattern_ops);
CREATE INDEX "geo_administrativeareatype_country_id" ON "geo_administrativeareatype" ("country_id");
CREATE INDEX "geo_administrativeareatype_parent_id" ON "geo_administrativeareatype" ("parent_id");
CREATE INDEX "geo_administrativeareatype_lft" ON "geo_administrativeareatype" ("lft");
CREATE INDEX "geo_administrativeareatype_rght" ON "geo_administrativeareatype" ("rght");
CREATE INDEX "geo_administrativeareatype_tree_id" ON "geo_administrativeareatype" ("tree_id");
CREATE INDEX "geo_administrativeareatype_level" ON "geo_administrativeareatype" ("level");
CREATE INDEX "geo_administrativearea_name" ON "geo_administrativearea" ("name");
CREATE INDEX "geo_administrativearea_name_like" ON "geo_administrativearea" ("name" varchar_pattern_ops);
CREATE INDEX "geo_administrativearea_code" ON "geo_administrativearea" ("code");
CREATE INDEX "geo_administrativearea_code_like" ON "geo_administrativearea" ("code" varchar_pattern_ops);
CREATE INDEX "geo_administrativearea_parent_id" ON "geo_administrativearea" ("parent_id");
CREATE INDEX "geo_administrativearea_country_id" ON "geo_administrativearea" ("country_id");
CREATE INDEX "geo_administrativearea_type_id" ON "geo_administrativearea" ("type_id");
CREATE INDEX "geo_administrativearea_lft" ON "geo_administrativearea" ("lft");
CREATE INDEX "geo_administrativearea_rght" ON "geo_administrativearea" ("rght");
CREATE INDEX "geo_administrativearea_tree_id" ON "geo_administrativearea" ("tree_id");
CREATE INDEX "geo_administrativearea_level" ON "geo_administrativearea" ("level");
CREATE INDEX "geo_location_country_id" ON "geo_location" ("country_id");
CREATE INDEX "geo_location_area_id" ON "geo_location" ("area_id");
CREATE INDEX "geo_location_name" ON "geo_location" ("name");
CREATE INDEX "geo_location_name_like" ON "geo_location" ("name" varchar_pattern_ops);
CREATE TABLE "django_session" (
    "session_key" varchar(40) NOT NULL PRIMARY KEY,
    "session_data" text NOT NULL,
    "expire_date" timestamp with time zone NOT NULL
)
;
CREATE INDEX "django_session_expire_date" ON "django_session" ("expire_date");
CREATE TABLE "crashlog_error" (
    "id" serial NOT NULL PRIMARY KEY,
    "class_name" varchar(128) NOT NULL,
    "message" text NOT NULL,
    "traceback" text NOT NULL,
    "time" timestamp with time zone NOT NULL,
    "url" varchar(200),
    "server_name" varchar(128) NOT NULL,
    "username" varchar(100)
)
;
CREATE INDEX "crashlog_error_server_name" ON "crashlog_error" ("server_name");
CREATE INDEX "crashlog_error_server_name_like" ON "crashlog_error" ("server_name" varchar_pattern_ops);
CREATE INDEX "crashlog_error_username" ON "crashlog_error" ("username");
CREATE INDEX "crashlog_error_username_like" ON "crashlog_error" ("username" varchar_pattern_ops);
CREATE TABLE "company_office_countries" (
    "id" serial NOT NULL PRIMARY KEY,
    "office_id" integer NOT NULL,
    "country_id" integer NOT NULL REFERENCES "geo_country" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("office_id", "country_id")
)
;
CREATE TABLE "company_office" (
    "id" serial NOT NULL PRIMARY KEY,
    "version" bigint NOT NULL,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "name" varchar(50) NOT NULL,
    "country_id" integer NOT NULL REFERENCES "geo_country" ("id") DEFERRABLE INITIALLY DEFERRED,
    "type" integer NOT NULL,
    "slug" varchar(50) NOT NULL UNIQUE
)
;
ALTER TABLE "company_office_countries" ADD CONSTRAINT "office_id_refs_id_2c28e1b6" FOREIGN KEY ("office_id") REFERENCES "company_office" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE "company_marketingcampaign_geographical_areas" (
    "id" serial NOT NULL PRIMARY KEY,
    "marketingcampaign_id" integer NOT NULL,
    "administrativearea_id" integer NOT NULL REFERENCES "geo_administrativearea" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("marketingcampaign_id", "administrativearea_id")
)
;
CREATE TABLE "company_marketingcampaign" (
    "id" serial NOT NULL PRIMARY KEY,
    "version" bigint NOT NULL,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "office_id" integer NOT NULL REFERENCES "company_office" ("id") DEFERRABLE INITIALLY DEFERRED,
    "name" varchar(50) NOT NULL,
    "status" integer NOT NULL,
    "type" integer NOT NULL,
    "country_id" integer NOT NULL REFERENCES "geo_country" ("id") DEFERRABLE INITIALLY DEFERRED,
    "start_date" date NOT NULL,
    "end_date" date,
    "external_code" varchar(255) NOT NULL,
    "slug" varchar(50) NOT NULL,
    UNIQUE ("office_id", "name"),
    UNIQUE ("office_id", "slug")
)
;
ALTER TABLE "company_marketingcampaign_geographical_areas" ADD CONSTRAINT "marketingcampaign_id_refs_id_1e9e628e" FOREIGN KEY ("marketingcampaign_id") REFERENCES "company_marketingcampaign" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE "company_userprofile" (
    "id" serial NOT NULL PRIMARY KEY,
    "user_id" integer NOT NULL UNIQUE REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "language" varchar(2) NOT NULL,
    "time_zone" varchar(50) NOT NULL
)
;
CREATE TABLE "company_partner" (
    "id" serial NOT NULL PRIMARY KEY,
    "version" bigint NOT NULL,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "office_id" integer NOT NULL REFERENCES "company_office" ("id") DEFERRABLE INITIALLY DEFERRED,
    "name" varchar(50) NOT NULL,
    "address" varchar(300) NOT NULL,
    "status" integer NOT NULL,
    "type" integer NOT NULL,
    "logo" varchar(100),
    "slug" varchar(50) NOT NULL UNIQUE,
    UNIQUE ("office_id", "name")
)
;
CREATE TABLE "company_partnerrole" (
    "id" serial NOT NULL PRIMARY KEY,
    "version" bigint NOT NULL,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "role" varchar(50) NOT NULL UNIQUE,
    "description" varchar(300)
)
;
CREATE INDEX "company_office_last_modified_user_id" ON "company_office" ("last_modified_user_id");
CREATE INDEX "company_office_country_id" ON "company_office" ("country_id");
CREATE INDEX "company_marketingcampaign_last_modified_user_id" ON "company_marketingcampaign" ("last_modified_user_id");
CREATE INDEX "company_marketingcampaign_office_id" ON "company_marketingcampaign" ("office_id");
CREATE INDEX "company_marketingcampaign_country_id" ON "company_marketingcampaign" ("country_id");
CREATE INDEX "company_marketingcampaign_slug" ON "company_marketingcampaign" ("slug");
CREATE INDEX "company_marketingcampaign_slug_like" ON "company_marketingcampaign" ("slug" varchar_pattern_ops);
CREATE INDEX "company_partner_last_modified_user_id" ON "company_partner" ("last_modified_user_id");
CREATE INDEX "company_partner_office_id" ON "company_partner" ("office_id");
CREATE INDEX "company_partnerrole_last_modified_user_id" ON "company_partnerrole" ("last_modified_user_id");
CREATE TABLE "registration_person" (
    "id" serial NOT NULL PRIMARY KEY,
    "version" bigint NOT NULL,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "uuid" uuid NOT NULL UNIQUE,
    "last_name" varchar(255) NOT NULL,
    "first_name" varchar(255) NOT NULL,
    "middle_name" varchar(255),
    "location_id" integer REFERENCES "geo_location" ("id") DEFERRABLE INITIALLY DEFERRED,
    "phone_number" varchar(255),
    "mobile_number" varchar(255),
    "office_id" integer NOT NULL REFERENCES "company_office" ("id") DEFERRABLE INITIALLY DEFERRED,
    "subscriber_id" integer,
    "subscriber_role" integer,
    "country_id" integer REFERENCES "geo_country" ("id") DEFERRABLE INITIALLY DEFERRED,
)
;
CREATE TABLE "registration_affiliatecandidacy" (
    "id" serial NOT NULL PRIMARY KEY,
    "person_id" integer NOT NULL REFERENCES "registration_person" ("id") DEFERRABLE INITIALLY DEFERRED,
    "subscriber_id" integer NOT NULL UNIQUE
)
;
CREATE TABLE "registration_document" (
    "id" serial NOT NULL PRIMARY KEY,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "person_id" integer NOT NULL REFERENCES "registration_person" ("id") DEFERRABLE INITIALLY DEFERRED,
    "document_type" integer NOT NULL,
    "document_provider" varchar(5) NOT NULL,
    "document_num" varchar(255)
)
;
CREATE TABLE "registration_documentproviderrule" (
    "id" serial NOT NULL PRIMARY KEY,
    "document_provider" varchar(5) NOT NULL,
    "document_type" integer NOT NULL,
    "regex" varchar(300) NOT NULL,
    UNIQUE ("document_provider", "document_type")
)
;
CREATE TABLE "registration_subscriber" (
    "id" serial NOT NULL PRIMARY KEY,
    "version" bigint NOT NULL,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "office_id" integer NOT NULL REFERENCES "company_office" ("id") DEFERRABLE INITIALLY DEFERRED,
    "uuid" uuid NOT NULL UNIQUE,
    "name" varchar(255) NOT NULL,
    "location_id" integer REFERENCES "geo_location" ("id") DEFERRABLE INITIALLY DEFERRED,
    "address" varchar(300),
    "refugee_status" integer,
    "claimed_member_count" integer NOT NULL,
    "registration_user_id" integer REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "registration_date" date
)
;
ALTER TABLE "registration_person" ADD CONSTRAINT "subscriber_id_refs_id_c1f9e7c" FOREIGN KEY ("subscriber_id") REFERENCES "registration_subscriber" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "registration_affiliatecandidacy" ADD CONSTRAINT "subscriber_id_refs_id_3411342a" FOREIGN KEY ("subscriber_id") REFERENCES "registration_subscriber" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE "registration_fingerprint" (
    "id" serial NOT NULL PRIMARY KEY,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "person_id" integer NOT NULL REFERENCES "registration_person" ("id") DEFERRABLE INITIALLY DEFERRED,
    "hand" varchar(1) NOT NULL,
    "finger" integer NOT NULL,
    "image" text NOT NULL,
    "code" text NOT NULL,
    "code_provider" integer NOT NULL,
    UNIQUE ("person_id", "finger", "hand")
)
;
CREATE TABLE "registration_registrationlayout" (
    "id" serial NOT NULL PRIMARY KEY,
    "office_id" integer NOT NULL REFERENCES "company_office" ("id") DEFERRABLE INITIALLY DEFERRED,
    "name" varchar(100) NOT NULL,
    "layout" text NOT NULL
)
;
CREATE TABLE "registration_account" (
    "id" serial NOT NULL PRIMARY KEY,
    "version" bigint NOT NULL,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "person_id" integer NOT NULL REFERENCES "registration_person" ("id") DEFERRABLE INITIALLY DEFERRED,
    "number" varchar(255) NOT NULL,
    UNIQUE ("person_id", "number")
)
;
CREATE INDEX "registration_person_last_modified_user_id" ON "registration_person" ("last_modified_user_id");
CREATE INDEX "registration_person_location_id" ON "registration_person" ("location_id");
CREATE INDEX "registration_person_office_id" ON "registration_person" ("office_id");
CREATE INDEX "registration_person_subscriber_id" ON "registration_person" ("subscriber_id");
CREATE INDEX "registration_person_country_id" ON "registration_person" ("country_id");
CREATE INDEX "registration_affiliatecandidacy_person_id" ON "registration_affiliatecandidacy" ("person_id");
CREATE INDEX "registration_document_last_modified_user_id" ON "registration_document" ("last_modified_user_id");
CREATE INDEX "registration_document_person_id" ON "registration_document" ("person_id");
CREATE INDEX "registration_subscriber_last_modified_user_id" ON "registration_subscriber" ("last_modified_user_id");
CREATE INDEX "registration_subscriber_office_id" ON "registration_subscriber" ("office_id");
CREATE INDEX "registration_subscriber_location_id" ON "registration_subscriber" ("location_id");
CREATE INDEX "registration_subscriber_registration_user_id" ON "registration_subscriber" ("registration_user_id");
CREATE INDEX "registration_fingerprint_last_modified_user_id" ON "registration_fingerprint" ("last_modified_user_id");
CREATE INDEX "registration_fingerprint_person_id" ON "registration_fingerprint" ("person_id");
CREATE INDEX "registration_registrationlayout_office_id" ON "registration_registrationlayout" ("office_id");
CREATE INDEX "registration_account_last_modified_user_id" ON "registration_account" ("last_modified_user_id");
CREATE INDEX "registration_account_person_id" ON "registration_account" ("person_id");
CREATE TABLE "sales_productgroup" (
    "id" serial NOT NULL PRIMARY KEY,
    "version" bigint NOT NULL,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "name" varchar(255) NOT NULL UNIQUE,
    "description" varchar(300),
    "slug" varchar(50) NOT NULL
)
;
CREATE TABLE "sales_units" (
    "id" serial NOT NULL PRIMARY KEY,
    "version" bigint NOT NULL,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "name" varchar(255) NOT NULL,
    "code" varchar(20) NOT NULL
)
;
CREATE TABLE "sales_product" (
    "id" serial NOT NULL PRIMARY KEY,
    "version" bigint NOT NULL,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "sales_group_id" integer NOT NULL REFERENCES "sales_productgroup" ("id") DEFERRABLE INITIALLY DEFERRED,
    "name" varchar(50) NOT NULL,
    "code" varchar(20) NOT NULL,
    "description" varchar(300),
    "standard_unit_id" integer NOT NULL REFERENCES "sales_units" ("id") DEFERRABLE INITIALLY DEFERRED,
    "slug" varchar(50) NOT NULL UNIQUE
)
;
CREATE TABLE "sales_posunitofmeasure" (
    "id" serial NOT NULL PRIMARY KEY,
    "version" bigint NOT NULL,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "office_id" integer NOT NULL REFERENCES "company_office" ("id") DEFERRABLE INITIALLY DEFERRED,
    "sales_id" integer NOT NULL REFERENCES "sales_product" ("id") DEFERRABLE INITIALLY DEFERRED,
    "name" varchar(50) NOT NULL,
    "code" varchar(20) NOT NULL,
    "conversion_unit_id" integer REFERENCES "sales_units" ("id") DEFERRABLE INITIALLY DEFERRED,
    "conversion_factor" numeric(6, 2) NOT NULL,
    "description" varchar(300),
    "slug" varchar(50) NOT NULL,
    UNIQUE ("office_id", "slug"),
    UNIQUE ("office_id", "name")
)
;
CREATE INDEX "sales_productgroup_last_modified_user_id" ON "sales_productgroup" ("last_modified_user_id");
CREATE INDEX "sales_productgroup_slug" ON "sales_productgroup" ("slug");
CREATE INDEX "sales_productgroup_slug_like" ON "sales_productgroup" ("slug" varchar_pattern_ops);
CREATE INDEX "sales_units_last_modified_user_id" ON "sales_units" ("last_modified_user_id");
CREATE INDEX "sales_product_last_modified_user_id" ON "sales_product" ("last_modified_user_id");
CREATE INDEX "sales_product_product_group_id" ON "sales_product" ("sales_group_id");
CREATE INDEX "sales_product_standard_unit_id" ON "sales_product" ("standard_unit_id");
CREATE INDEX "sales_posunitofmeasure_last_modified_user_id" ON "sales_posunitofmeasure" ("last_modified_user_id");
CREATE INDEX "sales_posunitofmeasure_office_id" ON "sales_posunitofmeasure" ("office_id");
CREATE INDEX "sales_posunitofmeasure_product_id" ON "sales_posunitofmeasure" ("sales_id");
CREATE INDEX "sales_posunitofmeasure_conversion_unit_id" ON "sales_posunitofmeasure" ("conversion_unit_id");
CREATE INDEX "sales_posunitofmeasure_slug" ON "sales_posunitofmeasure" ("slug");
CREATE INDEX "sales_posunitofmeasure_slug_like" ON "sales_posunitofmeasure" ("slug" varchar_pattern_ops);
CREATE TABLE "redemption_retailer" (
    "id" serial NOT NULL PRIMARY KEY,
    "version" bigint NOT NULL,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "office_id" integer NOT NULL REFERENCES "company_office" ("id") DEFERRABLE INITIALLY DEFERRED,
    "name" varchar(50) NOT NULL,
    "location_id" integer REFERENCES "geo_location" ("id") DEFERRABLE INITIALLY DEFERRED,
    "address" varchar(300),
    "contact_name" varchar(255),
    "phone_number" varchar(255),
    "mobile_number" varchar(255),
    "fax_number" varchar(255),
    "e_mail" varchar(75),
    "external_code" varchar(50),
    "can_top_up" boolean NOT NULL,
    "slug" varchar(50) NOT NULL UNIQUE,
    UNIQUE ("office_id", "name")
)
;
CREATE TABLE "redemption_terminal" (
    "id" serial NOT NULL PRIMARY KEY,
    "version" bigint NOT NULL,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "device" integer NOT NULL,
    "make" varchar(50) NOT NULL,
    "model" varchar(50) NOT NULL,
    UNIQUE ("device", "make", "model")
)
;
CREATE TABLE "redemption_pointofsaleterminal" (
    "id" serial NOT NULL PRIMARY KEY,
    "version" bigint NOT NULL,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "office_id" integer NOT NULL REFERENCES "company_office" ("id") DEFERRABLE INITIALLY DEFERRED,
    "terminal_id" integer NOT NULL REFERENCES "redemption_terminal" ("id") DEFERRABLE INITIALLY DEFERRED,
    "company_number" varchar(50) NOT NULL UNIQUE,
    "serial_number" varchar(50) NOT NULL UNIQUE,
    "slug" varchar(50) NOT NULL UNIQUE,
    "assigned_retailer_id" integer REFERENCES "redemption_retailer" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("terminal_id", "serial_number")
)
;
CREATE INDEX "redemption_retailer_last_modified_user_id" ON "redemption_retailer" ("last_modified_user_id");
CREATE INDEX "redemption_retailer_office_id" ON "redemption_retailer" ("office_id");
CREATE INDEX "redemption_retailer_location_id" ON "redemption_retailer" ("location_id");
CREATE INDEX "redemption_terminal_last_modified_user_id" ON "redemption_terminal" ("last_modified_user_id");
CREATE INDEX "redemption_pointofsaleterminal_last_modified_user_id" ON "redemption_pointofsaleterminal" ("last_modified_user_id");
CREATE INDEX "redemption_pointofsaleterminal_office_id" ON "redemption_pointofsaleterminal" ("office_id");
CREATE INDEX "redemption_pointofsaleterminal_terminal_id" ON "redemption_pointofsaleterminal" ("terminal_id");
CREATE INDEX "redemption_pointofsaleterminal_assigned_retailer_id" ON "redemption_pointofsaleterminal" ("assigned_retailer_id");
CREATE TABLE "promotions_distributionmodel" (
    "id" serial NOT NULL PRIMARY KEY,
    "version" bigint NOT NULL,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "name" varchar(100) NOT NULL,
    "cash_only" boolean NOT NULL
)
;
CREATE TABLE "promotions_deliverymechanism" (
    "id" serial NOT NULL PRIMARY KEY,
    "version" bigint NOT NULL,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "office_id" integer NOT NULL REFERENCES "company_office" ("id") DEFERRABLE INITIALLY DEFERRED,
    "name" varchar(100) NOT NULL,
    "type_id" integer NOT NULL REFERENCES "promotions_distributionmodel" ("id") DEFERRABLE INITIALLY DEFERRED,
    "token" integer NOT NULL,
    "mandatory_fields" text,
    "description" varchar(300),
    "modality" integer NOT NULL,
    UNIQUE ("office_id", "name", "type_id")
)
;
CREATE TABLE "promotions_bundle" (
    "id" serial NOT NULL PRIMARY KEY,
    "version" bigint NOT NULL,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "office_id" integer NOT NULL REFERENCES "company_office" ("id") DEFERRABLE INITIALLY DEFERRED,
    "name" varchar(50) NOT NULL,
    "modality" integer NOT NULL,
    "description" varchar(300),
    "slug" varchar(50) NOT NULL,
    UNIQUE ("office_id", "name")
)
;
CREATE TABLE "promotions_ration" (
    "id" serial NOT NULL PRIMARY KEY,
    "version" bigint NOT NULL,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "pos_product_id" integer NOT NULL REFERENCES "sales_posunitofmeasure" ("id") DEFERRABLE INITIALLY DEFERRED,
    "bundle_id" integer NOT NULL REFERENCES "promotions_bundle" ("id") DEFERRABLE INITIALLY DEFERRED,
    "quantity" numeric(6, 2),
    "price" numeric(6, 2),
    UNIQUE ("bundle_id", "pos_product_id")
)
;
CREATE TABLE "promotions_viewergroup" (
    "id" serial NOT NULL PRIMARY KEY,
    "version" bigint NOT NULL,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "name" varchar(255) NOT NULL UNIQUE
)
;
CREATE TABLE "promotions_activity_viewer_groups" (
    "id" serial NOT NULL PRIMARY KEY,
    "activity_id" integer NOT NULL,
    "viewergroup_id" integer NOT NULL REFERENCES "promotions_viewergroup" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("activity_id", "viewergroup_id")
)
;
CREATE TABLE "promotions_activity" (
    "id" serial NOT NULL PRIMARY KEY,
    "version" bigint NOT NULL,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "name" varchar(255) NOT NULL
)
;
ALTER TABLE "promotions_activity_viewer_groups" ADD CONSTRAINT "activity_id_refs_id_8699927d" FOREIGN KEY ("activity_id") REFERENCES "promotions_activity" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE "promotions_promotion_viewer_groups" (
    "id" serial NOT NULL PRIMARY KEY,
    "promotion_id" integer NOT NULL,
    "viewergroup_id" integer NOT NULL REFERENCES "promotions_viewergroup" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("promotion_id", "viewergroup_id")
)
;
CREATE TABLE "promotions_promotion" (
    "id" serial NOT NULL PRIMARY KEY,
    "version" bigint NOT NULL,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "marketingcampaign_id" integer NOT NULL REFERENCES "company_marketingcampaign" ("id") DEFERRABLE INITIALLY DEFERRED,
    "name" varchar(50) NOT NULL,
    "activity_id" integer NOT NULL REFERENCES "promotions_activity" ("id") DEFERRABLE INITIALLY DEFERRED,
    "conditionality" integer NOT NULL,
    "verification_required" boolean NOT NULL,
    "start_date" date NOT NULL,
    "end_date" date,
    "slug" varchar(50) NOT NULL,
    "allowed_sales_affiliate" integer,
    "target_number_of_subscribers" integer,
    "weeks_per_cycle" integer,
    "delivery_mechanism_id" integer NOT NULL REFERENCES "promotions_deliverymechanism" ("id") DEFERRABLE INITIALLY DEFERRED,
    "transfer_subscriber_dependency" integer,
    UNIQUE ("name", "marketingcampaign_id"),
    UNIQUE ("slug", "marketingcampaign_id")
)
;
ALTER TABLE "promotions_promotion_viewer_groups" ADD CONSTRAINT "promotion_id_refs_id_df7b2425" FOREIGN KEY ("promotion_id") REFERENCES "promotions_promotion" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE "promotions_promotionforarea_retailers" (
    "id" serial NOT NULL PRIMARY KEY,
    "promotionforarea_id" integer NOT NULL,
    "retailer_id" integer NOT NULL REFERENCES "redemption_retailer" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("promotionforarea_id", "retailer_id")
)
;
CREATE TABLE "promotions_promotionforarea" (
    "id" serial NOT NULL PRIMARY KEY,
    "version" bigint NOT NULL,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "promotion_id" integer NOT NULL REFERENCES "promotions_promotion" ("id") DEFERRABLE INITIALLY DEFERRED,
    "geographical_area_id" integer NOT NULL REFERENCES "geo_administrativearea" ("id") DEFERRABLE INITIALLY DEFERRED,
    "default_bundle_id" integer REFERENCES "promotions_bundle" ("id") DEFERRABLE INITIALLY DEFERRED,
    "bundle_quantity" integer,
    "transfer_cash_value" numeric(6, 2),
    UNIQUE ("promotion_id", "geographical_area_id")
)
;
ALTER TABLE "promotions_promotionforarea_retailers" ADD CONSTRAINT "promotionforarea_id_refs_id_3ba48ab7" FOREIGN KEY ("promotionforarea_id") REFERENCES "promotions_promotionforarea" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE "promotions_partnerroleinarea" (
    "id" serial NOT NULL PRIMARY KEY,
    "version" bigint NOT NULL,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "promotion_for_area_id" integer NOT NULL REFERENCES "promotions_promotionforarea" ("id") DEFERRABLE INITIALLY DEFERRED,
    "partner_id" integer REFERENCES "company_partner" ("id") DEFERRABLE INITIALLY DEFERRED,
    "role_id" integer NOT NULL REFERENCES "company_partnerrole" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("promotion_for_area_id", "role_id")
)
;

COMMIT;
""")
    schema1.resolve_references()

def test_big_schema_with_comments():
    schema = Schema()
    schema.parse(
    """BEGIN;
CREATE TABLE "company_office" (
    "id" serial NOT NULL PRIMARY KEY,
    "version" bigint NOT NULL,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "name" varchar(50) NOT NULL,
    "country_id" integer NOT NULL,
    "type" integer NOT NULL,
    "slug" varchar(50) NOT NULL UNIQUE
)
;
CREATE TABLE "company_project_geographical_areas" (
    "id" serial NOT NULL PRIMARY KEY,
    "project_id" integer NOT NULL,
    "administrativearea_id" integer NOT NULL,
    UNIQUE ("project_id", "administrativearea_id")
)
;
CREATE TABLE "company_project" (
    "id" serial NOT NULL PRIMARY KEY,
    "version" bigint NOT NULL,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "office_id" integer NOT NULL REFERENCES "company_office" ("id") DEFERRABLE INITIALLY DEFERRED,
    "name" varchar(50) NOT NULL,
    "status" integer NOT NULL,
    "type" integer NOT NULL,
    "country_id" integer NOT NULL,
    "start_date" date NOT NULL,
    "end_date" date,
    "external_code" varchar(255) NOT NULL,
    "slug" varchar(50) NOT NULL,
    UNIQUE ("office_id", "name"),
    UNIQUE ("office_id", "slug")
)
;
ALTER TABLE "company_project_geographical_areas" ADD CONSTRAINT "project_id_refs_id_1e9e628e" FOREIGN KEY ("project_id") REFERENCES "company_project" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE "company_userprofile" (
    "id" serial NOT NULL PRIMARY KEY,
    "user_id" integer NOT NULL UNIQUE,
    "language" varchar(2) NOT NULL,
    "time_zone" varchar(50) NOT NULL
)
;
CREATE TABLE "company_partner" (
    "id" serial NOT NULL PRIMARY KEY,
    "version" bigint NOT NULL,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "office_id" integer NOT NULL REFERENCES "company_office" ("id") DEFERRABLE INITIALLY DEFERRED,
    "name" varchar(50) NOT NULL,
    "address" varchar(300) NOT NULL,
    "status" integer NOT NULL,
    "type" integer NOT NULL,
    "logo" varchar(100),
    "slug" varchar(50) NOT NULL UNIQUE,
    UNIQUE ("office_id", "name")
)
;
CREATE TABLE "company_partnerrole" (
    "id" serial NOT NULL PRIMARY KEY,
    "version" bigint NOT NULL,
    "last_modified_date" timestamp with time zone NOT NULL,
    "last_modified_user_id" integer NOT NULL,
    "hash" varchar(255),
    "date_removed" timestamp with time zone,
    "role" varchar(50) NOT NULL UNIQUE,
    "description" varchar(300)
)
;
-- The following references should be added but depend on non-existent tables:
-- ALTER TABLE "company_office_countries" ADD CONSTRAINT "country_id_refs_id_bebf0b9b" FOREIGN KEY ("country_id") REFERENCES "geo_country" ("id") DEFERRABLE INITIALLY DEFERRED;
-- ALTER TABLE "company_office" ADD CONSTRAINT "country_id_refs_id_2437e634" FOREIGN KEY ("country_id") REFERENCES "geo_country" ("id") DEFERRABLE INITIALLY DEFERRED;
-- ALTER TABLE "company_project" ADD CONSTRAINT "country_id_refs_id_849a0702" FOREIGN KEY ("country_id") REFERENCES "geo_country" ("id") DEFERRABLE INITIALLY DEFERRED;
-- ALTER TABLE "company_project_geographical_areas" ADD CONSTRAINT "administrativearea_id_refs_id_8a616b7" FOREIGN KEY ("administrativearea_id") REFERENCES "geo_administrativearea" ("id") DEFERRABLE INITIALLY DEFERRED;
-- ALTER TABLE "company_office" ADD CONSTRAINT "last_modified_user_id_refs_id_8902c876" FOREIGN KEY ("last_modified_user_id") REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED;
-- ALTER TABLE "company_project" ADD CONSTRAINT "last_modified_user_id_refs_id_9241258" FOREIGN KEY ("last_modified_user_id") REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED;
-- ALTER TABLE "company_userprofile" ADD CONSTRAINT "user_id_refs_id_3c991a59" FOREIGN KEY ("user_id") REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED;
-- ALTER TABLE "company_partner" ADD CONSTRAINT "last_modified_user_id_refs_id_7d008b63" FOREIGN KEY ("last_modified_user_id") REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED;
COMMIT;
    """)
    schema.resolve_references()
