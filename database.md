# Database Design Conventions — zeroFIR

Source of truth for **how to write schema-changing code** that won't
break on deploy. Every lesson from the CyberFraud FK-collation
incident (2026-06-20) is codified here from day one.

> **TL;DR for migration authors:** new tables/columns that reference
> an existing column **must match its `CHARSET`, `COLLATE`, and
> exact type**. If you're adding an FK, copy the referenced column's
> full definition verbatim. Anything else risks MySQL error 3780.

---

## 1. Production database parameters

| Property | Value |
|---|---|
| Server | MySQL 8+ (Ubuntu 24.04) |
| Database | `zerofir` |
| Default charset | `utf8mb4` |
| Default collation | `utf8mb4_unicode_ci` |
| Engine | `InnoDB` |

Verify on any environment:

```sql
SELECT default_character_set_name, default_collation_name
FROM information_schema.schemata
WHERE schema_name = 'zerofir';
```

Local dev MySQL may differ (defaults to `utf8mb4_0900_ai_ci` for
fresh databases). Migrations must be explicit — never rely on env
defaults.

---

## 2. ID column convention

Same as CyberFraud + eParole:

| Table category | ID type | Rationale |
|---|---|---|
| Parent records (`zero_firs`, transfers, audit events, orders) | `VARCHAR(36)` UUIDv4 | Enumeration / IDOR protection (VAPT best practice) |
| Lookup tables (`units`, `police_stations`) | `INT AUTO_INCREMENT` | Stable, small, not exposed as URL param |
| Auth (`users`) | `INT AUTO_INCREMENT` | Not exposed to client; JWT carries `user_id` |
| Reference fields to lookups (`unit_id`, `ps_id`, `user_id`) | `INT` | Match the lookup PK |

Source of truth = the SQLAlchemy models in `backend/models/*.py`.

---

## 3. Rules for writing schema migrations

### 3.1 New tables — always declare both charset and collation

```sql
CREATE TABLE foo (
    id VARCHAR(36) NOT NULL,
    ...
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 3.2 New columns on existing tables — let the table default win

`ALTER TABLE ... ADD COLUMN` inherits the table's CHARSET/COLLATE;
do NOT specify them explicitly on the column. The column will match
its siblings (and any FK source).

### 3.3 New foreign keys — sanity check before writing the SQL

Before you write `FOREIGN KEY (x) REFERENCES y(z)`, run:

```sql
SELECT column_name, column_type, character_set_name, collation_name
FROM information_schema.columns
WHERE table_schema = 'zerofir'
  AND table_name = '<target_table>'
  AND column_name = '<target_column>';
```

Copy `column_type` + charset + collation onto the referencing
column. The combination must match.

### 3.4 Reorder DROP INDEX / CREATE INDEX around FKs

Lesson from CyberFraud migration 008 (2026-07-08): MySQL uses a
unique index as the FK backing index if it starts with the FK
column. **Create the replacement index BEFORE dropping the old
one** — else MySQL refuses with error 1553 ("Cannot drop index X:
needed in a foreign key constraint").

### 3.5 Migrations must be idempotent

Every migration checks `INFORMATION_SCHEMA` for tables / columns /
indexes / constraints before creating them. Use the same helper
functions (`_column_exists`, `_index_exists`, `_fk_exists`) that
CyberFraud + eParole use.

### 3.6 Never UPDATE or DELETE from append-only tables

`zero_fir_events` (Phase 1+) is append-only. All "changes" become
new rows. No migration should introduce an update route or a delete
cascade on this table.

---

## 4. Migration registry

_(populated as migrations land — Phase 1+)_

---

## 5. Common operations cheat-sheet

### Add a new child table referencing `zero_firs`

```sql
CREATE TABLE my_new_child (
    id            VARCHAR(36) NOT NULL,
    zero_fir_id   VARCHAR(36) NOT NULL,
    -- ... columns ...
    PRIMARY KEY (id),
    CONSTRAINT fk_my_new_child_zero_fir_id
        FOREIGN KEY (zero_fir_id) REFERENCES zero_firs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Check FK compatibility before writing one

```sql
SELECT
    cs.character_set_name AS charset,
    cl.collation_name     AS collation
FROM information_schema.columns c
JOIN information_schema.character_sets cs USING (character_set_name)
JOIN information_schema.collations cl USING (collation_name)
WHERE c.table_schema = 'zerofir'
  AND c.table_name = 'zero_firs'
  AND c.column_name = 'id';
```

---

## 6. When in doubt

1. Read the actual prod schema — `SHOW CREATE TABLE x\G`.
2. Match the referenced column's full definition when writing FKs.
3. Test the migration on a copy of prod data before pushing.
4. Run migrations through `deploy/update.sh`, never by hand on prod.
