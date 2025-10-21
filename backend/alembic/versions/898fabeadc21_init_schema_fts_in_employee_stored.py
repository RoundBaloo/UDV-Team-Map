"""init schema + FTS in employee (stored)

Revision ID: 898fabeadc21
Revises: d2fd3faf0dee
Create Date: 2025-10-21 17:32:09.711120

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '898fabeadc21'
down_revision: Union[str, Sequence[str], None] = 'd2fd3faf0dee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 0) extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    # 1) sync_job
    op.execute("""
    CREATE TABLE IF NOT EXISTS sync_job (
      id BIGSERIAL PRIMARY KEY,
      trigger     TEXT NOT NULL CHECK (trigger IN ('scheduled','manual')),
      status      TEXT NOT NULL CHECK (status IN ('running','success','error','partial')),
      started_at  TIMESTAMPTZ NOT NULL,
      finished_at TIMESTAMPTZ NULL,
      summary     JSONB NULL
    );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_sync_job_started_at ON sync_job (started_at);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_sync_job_status ON sync_job (status);")

    # 2) external_entity_snapshot
    op.execute("""
    CREATE TABLE IF NOT EXISTS external_entity_snapshot (
      id           BIGSERIAL PRIMARY KEY,
      entity_type  TEXT NOT NULL CHECK (entity_type IN ('employee','team','org_unit')),
      external_ref TEXT NOT NULL,
      job_id       BIGINT NOT NULL REFERENCES sync_job(id) ON DELETE CASCADE,
      payload      JSONB NOT NULL,
      normalized   JSONB NOT NULL,
      received_at  TIMESTAMPTZ NOT NULL,
      local_id     BIGINT NULL
    );
    """)
    op.execute("""
    CREATE INDEX IF NOT EXISTS idx_ees_entity_ext
      ON external_entity_snapshot (entity_type, external_ref);
    """)
    op.execute("""
    CREATE INDEX IF NOT EXISTS idx_ees_entity_local_received
      ON external_entity_snapshot (entity_type, local_id, received_at DESC);
    """)

    # 3) org_unit
    op.execute("""
    CREATE TABLE IF NOT EXISTS org_unit (
      id BIGSERIAL PRIMARY KEY,
      parent_id BIGINT NULL REFERENCES org_unit(id) ON DELETE SET NULL,
      unit_type TEXT NOT NULL CHECK (unit_type IN ('block','department','direction')),
      name      TEXT NOT NULL,
      code      TEXT UNIQUE NULL,
      is_archived BOOLEAN NOT NULL DEFAULT FALSE,
      last_applied_snapshot_id BIGINT NULL REFERENCES external_entity_snapshot(id) ON DELETE SET NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_org_unit_parent_id ON org_unit (parent_id);")
    op.execute("""
    CREATE INDEX IF NOT EXISTS idx_org_unit_name_trgm
      ON org_unit USING GIN (lower(name) gin_trgm_ops);
    """)

    # 4) media
    op.execute("""
    CREATE TABLE IF NOT EXISTS media (
      id BIGSERIAL PRIMARY KEY,
      storage_key TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """)

    # 5) employee (+ STORED FTS)
    op.execute("""
    CREATE TABLE IF NOT EXISTS employee (
      id                   BIGSERIAL PRIMARY KEY,

      external_ref         TEXT NULL,
      email                TEXT NOT NULL UNIQUE,

      first_name           TEXT NOT NULL,
      last_name            TEXT NOT NULL,
      title                TEXT NOT NULL,
      status               TEXT NOT NULL CHECK (status IN ('active','dismissed')) DEFAULT 'active',
      manager_id           BIGINT NULL REFERENCES employee(id) ON DELETE SET NULL,
      primary_org_unit_id  BIGINT NULL REFERENCES org_unit(id) ON DELETE SET NULL,

      grade                TEXT NULL,
      bio                  TEXT NULL,
      skills               JSONB NULL,
      work_city            TEXT NULL,
      work_format          TEXT NULL CHECK (work_format IN ('office','hybrid','remote')),
      time_zone            TEXT NULL,

      work_phone           TEXT NULL,
      personal_phone       TEXT NULL,
      messengers           JSONB NULL,

      birth_day            SMALLINT NULL CHECK (birth_day BETWEEN 1 AND 31),
      birth_month          SMALLINT NULL CHECK (birth_month BETWEEN 1 AND 12),
      experience_months    INT NULL CHECK (experience_months >= 0),

      photo_id             BIGINT NULL REFERENCES media(id) ON DELETE SET NULL,

      last_applied_snapshot_id BIGINT NULL REFERENCES external_entity_snapshot(id) ON DELETE SET NULL,

      password_hash        TEXT NOT NULL,
      is_blocked           BOOLEAN NOT NULL DEFAULT FALSE,
      last_login_at        TIMESTAMPTZ NULL,
      is_admin             BOOLEAN NOT NULL DEFAULT FALSE,

      search_tsv tsvector GENERATED ALWAYS AS (
        setweight(to_tsvector('russian', coalesce(first_name,'')), 'A') ||
        setweight(to_tsvector('russian', coalesce(last_name,'')),  'A') ||
        setweight(to_tsvector('russian', coalesce(title,'')),      'B') ||
        setweight(to_tsvector('russian', coalesce(grade,'')),      'C') ||
        setweight(to_tsvector('russian', coalesce(bio,'')),        'D') ||
        setweight(to_tsvector('russian', coalesce(skills::text,'')),'C')
      ) STORED,

      created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """)
    op.execute("""
    CREATE INDEX IF NOT EXISTS idx_employee_last_name_trgm
      ON employee USING GIN (lower(last_name) gin_trgm_ops);
    """)
    op.execute("""
    CREATE INDEX IF NOT EXISTS idx_employee_title_trgm
      ON employee USING GIN (lower(title) gin_trgm_ops);
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_employee_manager_id ON employee (manager_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_employee_primary_org_unit_id ON employee (primary_org_unit_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_employee_status ON employee (status);")
    op.execute("""
    CREATE INDEX IF NOT EXISTS idx_employee_search_tsv
      ON employee USING GIN (search_tsv);
    """)

    # 6) team
    op.execute("""
    CREATE TABLE IF NOT EXISTS team (
      id BIGSERIAL PRIMARY KEY,
      org_unit_id BIGINT NOT NULL REFERENCES org_unit(id) ON DELETE CASCADE,
      name        TEXT NOT NULL,
      code        TEXT UNIQUE NULL,
      description TEXT NULL,
      lead_id     BIGINT NULL REFERENCES employee(id) ON DELETE SET NULL,
      is_archived BOOLEAN NOT NULL DEFAULT FALSE,
      last_applied_snapshot_id BIGINT NULL REFERENCES external_entity_snapshot(id) ON DELETE SET NULL,
      created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_team_org_unit_id ON team (org_unit_id);")
    op.execute("""
    CREATE INDEX IF NOT EXISTS idx_team_name_trgm
      ON team USING GIN (lower(name) gin_trgm_ops);
    """)

    # 7) employee_team
    op.execute("""
    CREATE TABLE IF NOT EXISTS employee_team (
      employee_id       BIGINT NOT NULL REFERENCES employee(id) ON DELETE CASCADE,
      team_id           BIGINT NOT NULL REFERENCES team(id) ON DELETE CASCADE,
      position_in_team  TEXT NULL,
      is_primary        BOOLEAN NOT NULL DEFAULT FALSE,
      PRIMARY KEY (employee_id, team_id)
    );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_employee_team_team_id ON employee_team (team_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_employee_team_employee_id ON employee_team (employee_id);")
    op.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS uq_employee_one_primary_team
      ON employee_team (employee_id)
      WHERE is_primary IS TRUE;
    """)

    # 8) photo_moderation
    op.execute("""
    CREATE TABLE IF NOT EXISTS photo_moderation (
      id BIGSERIAL PRIMARY KEY,
      employee_id BIGINT NOT NULL REFERENCES employee(id) ON DELETE CASCADE,
      media_id    BIGINT NOT NULL REFERENCES media(id) ON DELETE CASCADE,
      status      TEXT NOT NULL CHECK (status IN ('pending','approved','rejected')) DEFAULT 'pending',
      reviewer_employee_id BIGINT NULL REFERENCES employee(id) ON DELETE SET NULL,
      reviewed_at TIMESTAMPTZ NULL,
      reject_reason TEXT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """)
    op.execute("""
    CREATE INDEX IF NOT EXISTS idx_photo_moderation_pending
      ON photo_moderation (status) WHERE status='pending';
    """)

    # 9) sync_record
    op.execute("""
    CREATE TABLE IF NOT EXISTS sync_record (
      id           BIGSERIAL PRIMARY KEY,
      job_id       BIGINT NOT NULL REFERENCES sync_job(id) ON DELETE CASCADE,
      entity_type  TEXT NOT NULL CHECK (entity_type IN ('employee','team','org_unit')),
      external_ref TEXT NOT NULL,
      local_id     BIGINT NULL,
      action       TEXT NOT NULL CHECK (action IN ('create','update','verify','archive')),
      status       TEXT NOT NULL CHECK (status IN ('applied','orphaned','error')),
      decision     TEXT NULL CHECK (decision IN ('archive','keep') OR decision IS NULL),
      decided_by_employee_id BIGINT NULL REFERENCES employee(id) ON DELETE SET NULL,
      decided_at   TIMESTAMPTZ NULL,
      message      TEXT NULL,
      created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """)
    op.execute("""
    CREATE INDEX IF NOT EXISTS idx_sync_record_entity_local
      ON sync_record (entity_type, local_id);
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_sync_record_job_id ON sync_record (job_id);")

    # 10) audit_log
    op.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
      id BIGSERIAL PRIMARY KEY,
      actor_employee_id BIGINT NULL REFERENCES employee(id) ON DELETE SET NULL,
      action      TEXT NOT NULL,
      entity_type TEXT NOT NULL,
      entity_id   BIGINT NOT NULL,
      before      JSONB NULL,
      after       JSONB NULL,
      ip          TEXT NULL,
      user_agent  TEXT NULL,
      created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log (created_at);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_actor ON audit_log (actor_employee_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log (entity_type, entity_id);")

    # 11) updated_at trigger function
    op.execute("""
    CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
    BEGIN
      NEW.updated_at := now();
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    # 12) triggers on tables
    op.execute("DROP TRIGGER IF EXISTS trg_org_unit_updated_at ON org_unit;")
    op.execute("""
    CREATE TRIGGER trg_org_unit_updated_at
      BEFORE UPDATE ON org_unit
      FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """)
    op.execute("DROP TRIGGER IF EXISTS trg_employee_updated_at ON employee;")
    op.execute("""
    CREATE TRIGGER trg_employee_updated_at
      BEFORE UPDATE ON employee
      FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """)
    op.execute("DROP TRIGGER IF EXISTS trg_team_updated_at ON team;")
    op.execute("""
    CREATE TRIGGER trg_team_updated_at
      BEFORE UPDATE ON team
      FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """)
    
    pass


def downgrade():
    # 1) триггеры updated_at
    op.execute("DROP TRIGGER IF EXISTS trg_team_updated_at ON team;")
    op.execute("DROP TRIGGER IF EXISTS trg_employee_updated_at ON employee;")
    op.execute("DROP TRIGGER IF EXISTS trg_org_unit_updated_at ON org_unit;")

    # 2) функция updated_at
    op.execute("DROP FUNCTION IF EXISTS set_updated_at;")

    # 3) audit_log (индексы → таблица)
    op.execute("DROP INDEX IF EXISTS idx_audit_log_entity;")
    op.execute("DROP INDEX IF EXISTS idx_audit_log_actor;")
    op.execute("DROP INDEX IF EXISTS idx_audit_log_created_at;")
    op.execute("DROP TABLE IF EXISTS audit_log;")

    # 4) sync_record
    op.execute("DROP INDEX IF EXISTS idx_sync_record_job_id;")
    op.execute("DROP INDEX IF EXISTS idx_sync_record_entity_local;")
    op.execute("DROP TABLE IF EXISTS sync_record;")

    # 5) photo_moderation
    op.execute("DROP INDEX IF EXISTS idx_photo_moderation_pending;")
    op.execute("DROP TABLE IF EXISTS photo_moderation;")

    # 6) employee_team
    op.execute("DROP INDEX IF EXISTS uq_employee_one_primary_team;")
    op.execute("DROP INDEX IF EXISTS idx_employee_team_employee_id;")
    op.execute("DROP INDEX IF EXISTS idx_employee_team_team_id;")
    op.execute("DROP TABLE IF EXISTS employee_team;")

    # 7) team
    op.execute("DROP INDEX IF EXISTS idx_team_name_trgm;")
    op.execute("DROP INDEX IF EXISTS idx_team_org_unit_id;")
    op.execute("DROP TABLE IF EXISTS team;")

    # 8) employee (индексы → таблица)
    op.execute("DROP INDEX IF EXISTS idx_employee_search_tsv;")
    op.execute("DROP INDEX IF EXISTS idx_employee_status;")
    op.execute("DROP INDEX IF EXISTS idx_employee_primary_org_unit_id;")
    op.execute("DROP INDEX IF EXISTS idx_employee_manager_id;")
    op.execute("DROP INDEX IF EXISTS idx_employee_title_trgm;")
    op.execute("DROP INDEX IF EXISTS idx_employee_last_name_trgm;")
    op.execute("DROP TABLE IF EXISTS employee;")

    # 9) media
    op.execute("DROP TABLE IF EXISTS media;")

    # 10) org_unit
    op.execute("DROP INDEX IF EXISTS idx_org_unit_name_trgm;")
    op.execute("DROP INDEX IF EXISTS idx_org_unit_parent_id;")
    op.execute("DROP TABLE IF EXISTS org_unit;")

    # 11) external_entity_snapshot
    op.execute("DROP INDEX IF EXISTS idx_ees_entity_local_received;")
    op.execute("DROP INDEX IF EXISTS idx_ees_entity_ext;")
    op.execute("DROP TABLE IF EXISTS external_entity_snapshot;")

    # 12) sync_job
    op.execute("DROP INDEX IF EXISTS idx_sync_job_status;")
    op.execute("DROP INDEX IF EXISTS idx_sync_job_started_at;")
    op.execute("DROP TABLE IF EXISTS sync_job;")

    pass
