# Database Schema Standards

## Columns

- **No DB defaults:** Prefer optional fields over column-level defaults. Keep value control at the application layer. Audit columns are the exception — see Tables.
- **Tense-less names:** Use `create_time`, `expire_time`, never `created_at`, `expires_at`.
- **Booleans:** Prefix with `is_` (e.g. `is_active`). No default — make the application set it explicitly.

## Tables

- **Audit columns:** Most tables should have `create_time` and `update_time`. These carry column-level defaults — every writer would otherwise have to remember them, which is what defaults exist to prevent. They are bookkeeping, not business meaning, so the no-defaults rule does not apply.

## Migrations

- **Never edit old migrations.** Applied migrations are history; you cannot change the past. Add a new migration instead.
- **Never hand-author what the tooling generates.** Schema migrations come from the project's generator (Drizzle) diffing the schema — hand-writing them invites drift between the schema and the migration. Changes the generator cannot express are hand-written, as code or as SQL: data backfills, `CREATE INDEX CONCURRENTLY`, and other operational DDL.
