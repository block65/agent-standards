# Database Schema Standards

## Columns

- **No DB defaults:** Prefer optional fields over column-level defaults. Keep value control at the application layer.
- **Tense-less names:** Use `create_time`, `expire_time`, never `created_at`, `expires_at`.
- **Booleans:** Prefix with `is_` (e.g. `is_active`). No default — make the application set it explicitly.

## Tables

- **Audit columns:** Most tables should have `create_time` and `update_time`.
