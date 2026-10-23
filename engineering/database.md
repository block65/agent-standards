# Database Schema Standards

## Columns

- **No column defaults:** Make the field optional and set the value in the
  application, booleans included. The exception is the audit columns
  `create_time` and `update_time`, which most tables should have and which
  carry defaults so no writer has to remember them.
- **Tense-less names:** In SQL written by hand and in schemas defined outside
  Drizzle, use `create_time`, `expire_time`, never `created_at`, `expires_at`.
- **Booleans:** Prefix with `is_` (e.g. `is_active`).

## Migrations

- **Never edit an applied migration.** Add a new one.
- **Generate schema migrations** with the project's generator (Drizzle) from the
  schema; a hand-written one drifts from the schema. Hand-write only what the
  generator cannot express, as code or SQL: data backfills,
  `CREATE INDEX CONCURRENTLY`, and other operational DDL.
