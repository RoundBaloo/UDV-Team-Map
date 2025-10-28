import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

# тот же URL, который у тебя работает
DATABASE_URL = "postgresql+asyncpg://flooruser:17HjvfPfryjv@89.208.14.204:5432/floordb"


DROP_STATEMENTS = [
    # сначала триггеры, потом функция
    "DROP TRIGGER IF EXISTS trg_team_updated_at ON team",
    "DROP TRIGGER IF EXISTS trg_employee_updated_at ON employee",
    "DROP TRIGGER IF EXISTS trg_org_unit_updated_at ON org_unit",
    "DROP FUNCTION IF EXISTS set_updated_at() CASCADE",

    # потом таблицы с зависимостями
    "DROP TABLE IF EXISTS audit_log               CASCADE",
    "DROP TABLE IF EXISTS sync_record             CASCADE",
    "DROP TABLE IF EXISTS photo_moderation        CASCADE",
    "DROP TABLE IF EXISTS employee_team           CASCADE",
    "DROP TABLE IF EXISTS team                    CASCADE",
    "DROP TABLE IF EXISTS employee                CASCADE",
    "DROP TABLE IF EXISTS media                   CASCADE",
    "DROP TABLE IF EXISTS org_unit                CASCADE",
    "DROP TABLE IF EXISTS external_entity_snapshot CASCADE",
    "DROP TABLE IF EXISTS sync_job                CASCADE",
]


CREATE_STATEMENTS = [
    # 0) расширения
    "CREATE EXTENSION IF NOT EXISTS pg_trgm",

    # 1) sync_job
    """
    CREATE TABLE sync_job (
        id           BIGSERIAL PRIMARY KEY,
        trigger      TEXT NOT NULL CHECK (trigger IN ('scheduled','manual')),
        status       TEXT NOT NULL CHECK (status IN ('running','success','error','partial')),
        started_at   TIMESTAMPTZ NOT NULL,
        finished_at  TIMESTAMPTZ NULL,
        summary      JSONB NULL
    )
    """,
    "CREATE INDEX idx_sync_job_started_at ON sync_job (started_at)",
    "CREATE INDEX idx_sync_job_status     ON sync_job (status)",

    # 2) external_entity_snapshot
    """
    CREATE TABLE external_entity_snapshot (
        id            BIGSERIAL PRIMARY KEY,
        entity_type   TEXT NOT NULL CHECK (entity_type IN ('employee','team','org_unit')),
        external_ref  TEXT NOT NULL,
        job_id        BIGINT NOT NULL REFERENCES sync_job(id) ON DELETE CASCADE,
        payload       JSONB NOT NULL,
        normalized    JSONB NOT NULL,
        received_at   TIMESTAMPTZ NOT NULL,
        local_id      BIGINT NULL
    )
    """,
    "CREATE INDEX idx_ees_entity_ext ON external_entity_snapshot (entity_type, external_ref)",
    """CREATE INDEX idx_ees_entity_local_received
       ON external_entity_snapshot (entity_type, local_id, received_at DESC)
    """,

    # 3) org_unit (без manager_id FK пока что — потому что employee ещё не существует)
    # мы добавим FK и индексы на manager_id после создания employee
    """
    CREATE TABLE org_unit (
        id            BIGSERIAL PRIMARY KEY,

        parent_id     BIGINT NULL
            REFERENCES org_unit(id) ON DELETE SET NULL,

        external_ref  TEXT UNIQUE NULL,

        unit_type     TEXT NOT NULL
            CHECK (unit_type IN ('block','department','direction')),

        name          TEXT NOT NULL,

        is_archived   BOOLEAN NOT NULL DEFAULT FALSE,

        manager_id    BIGINT NULL, -- FK добавим позже ALTER'ом

        last_applied_snapshot_id BIGINT NULL
            REFERENCES external_entity_snapshot(id) ON DELETE SET NULL,

        created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX idx_org_unit_parent_id ON org_unit (parent_id)",
    """CREATE INDEX idx_org_unit_name_trgm
       ON org_unit
       USING GIN (lower(name) gin_trgm_ops)
    """,

    # 4) media
    """
    CREATE TABLE media (
        id           BIGSERIAL PRIMARY KEY,
        storage_key  TEXT NOT NULL,
        created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,

    # 5) employee
    """
    CREATE TABLE employee (
        id                   BIGSERIAL PRIMARY KEY,

        external_ref         TEXT NULL,
        email                TEXT NOT NULL UNIQUE,

        first_name           TEXT NOT NULL,
        last_name            TEXT NOT NULL,
        title                TEXT NOT NULL,

        status               TEXT NOT NULL
            CHECK (status IN ('active','dismissed'))
            DEFAULT 'active',

        manager_id           BIGINT NULL,
        primary_org_unit_id  BIGINT NULL,

        grade                TEXT NULL,
        bio                  TEXT NULL,
        skills               JSONB NULL,
        work_city            TEXT NULL,
        work_format          TEXT NULL
            CHECK (work_format IN ('office','hybrid','remote')),
        time_zone            TEXT NULL,

        work_phone           TEXT NULL,
        personal_phone       TEXT NULL,
        messengers           JSONB NULL,

        birth_day            SMALLINT NULL CHECK (birth_day BETWEEN 1 AND 31),
        birth_month          SMALLINT NULL CHECK (birth_month BETWEEN 1 AND 12),
        experience_months    INT NULL CHECK (experience_months >= 0),

        photo_id             BIGINT NULL
            REFERENCES media(id) ON DELETE SET NULL,

        last_applied_snapshot_id BIGINT NULL
            REFERENCES external_entity_snapshot(id) ON DELETE SET NULL,

        password_hash        TEXT NULL,
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
    )
    """,

    "CREATE INDEX idx_employee_last_name_trgm ON employee USING GIN (lower(last_name) gin_trgm_ops)",
    "CREATE INDEX idx_employee_title_trgm     ON employee USING GIN (lower(title) gin_trgm_ops)",
    "CREATE INDEX idx_employee_manager_id     ON employee (manager_id)",
    "CREATE INDEX idx_employee_status         ON employee (status)",
    "CREATE INDEX idx_employee_search_tsv     ON employee USING GIN (search_tsv)",

    # 6) team (lead_id ссылается на employee)
    """
    CREATE TABLE team (
        id            BIGSERIAL PRIMARY KEY,

        external_ref  TEXT UNIQUE NULL,
        name          TEXT NOT NULL,
        description   TEXT NULL,

        org_unit_id BIGINT NULL 
            REFERENCES org_unit(id) ON DELETE SET NULL,

        lead_id       BIGINT NULL
            REFERENCES employee(id) ON DELETE SET NULL,

        is_archived   BOOLEAN NOT NULL DEFAULT FALSE,

        last_applied_snapshot_id BIGINT NULL
            REFERENCES external_entity_snapshot(id) ON DELETE SET NULL,

        created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX idx_team_org_unit_id ON team (org_unit_id)",
    "CREATE INDEX idx_team_lead_id     ON team (lead_id)",
    "CREATE INDEX idx_team_name_trgm   ON team USING GIN (lower(name) gin_trgm_ops)",

    # 7) employee_team
    """
    CREATE TABLE employee_team (
        employee_id       BIGINT NOT NULL
            REFERENCES employee(id) ON DELETE CASCADE,
        team_id           BIGINT NOT NULL
            REFERENCES team(id) ON DELETE CASCADE,
        position_in_team  TEXT NULL,
        is_primary        BOOLEAN NOT NULL DEFAULT FALSE,
        PRIMARY KEY (employee_id, team_id)
    )
    """,
    "CREATE INDEX idx_employee_team_team_id ON employee_team (team_id)",
    "CREATE INDEX idx_employee_team_employee_id ON employee_team (employee_id)",
    """
    CREATE UNIQUE INDEX uq_employee_one_primary_team
        ON employee_team (employee_id)
        WHERE is_primary IS TRUE
    """,

    # 8) photo_moderation
    """
    CREATE TABLE photo_moderation (
        id                    BIGSERIAL PRIMARY KEY,
        employee_id           BIGINT NOT NULL
            REFERENCES employee(id) ON DELETE CASCADE,
        media_id              BIGINT NOT NULL
            REFERENCES media(id) ON DELETE CASCADE,
        status                TEXT NOT NULL
            CHECK (status IN ('pending','approved','rejected'))
            DEFAULT 'pending',
        reviewer_employee_id  BIGINT NULL
            REFERENCES employee(id) ON DELETE SET NULL,
        reviewed_at           TIMESTAMPTZ NULL,
        reject_reason         TEXT NULL,
        created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """CREATE INDEX idx_photo_moderation_pending
       ON photo_moderation (status)
       WHERE status = 'pending'
    """,

    # 9) sync_record
    """
    CREATE TABLE sync_record (
        id           BIGSERIAL PRIMARY KEY,
        job_id       BIGINT NOT NULL
            REFERENCES sync_job(id) ON DELETE CASCADE,
        entity_type  TEXT NOT NULL
            CHECK (entity_type IN ('employee','team','org_unit')),
        external_ref TEXT NOT NULL,
        local_id     BIGINT NULL,
        action       TEXT NOT NULL
            CHECK (action IN ('create','update','archive')),
        status       TEXT NOT NULL
            CHECK (status IN ('applied','orphaned','error')),
        decision                 TEXT NULL
            CHECK (decision IN ('archive','keep')),
        decided_by_employee_id   BIGINT NULL
            REFERENCES employee(id) ON DELETE SET NULL,
        decided_at               TIMESTAMPTZ NULL,
        message      TEXT NULL,
        created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX idx_sync_record_entity_local ON sync_record (entity_type, local_id)",
    "CREATE INDEX idx_sync_record_job_id       ON sync_record (job_id)",

    # 10) audit_log
    """
    CREATE TABLE audit_log (
        id                  BIGSERIAL PRIMARY KEY,
        actor_employee_id   BIGINT NULL
            REFERENCES employee(id) ON DELETE SET NULL,
        action              TEXT NOT NULL,
        entity_type         TEXT NOT NULL,
        entity_id           BIGINT NOT NULL,
        before              JSONB NULL,
        after               JSONB NULL,
        ip                  TEXT NULL,
        user_agent          TEXT NULL,
        created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX idx_audit_log_created_at ON audit_log (created_at)",
    "CREATE INDEX idx_audit_log_actor      ON audit_log (actor_employee_id)",
    "CREATE INDEX idx_audit_log_entity     ON audit_log (entity_type, entity_id)",

    # теперь, когда employee уже создан, можем навесить FK для org_unit.manager_id
    """
    ALTER TABLE org_unit
    ADD CONSTRAINT org_unit_manager_fk
    FOREIGN KEY (manager_id)
    REFERENCES employee(id)
    ON DELETE SET NULL
    """,

    "CREATE INDEX idx_org_unit_manager_id ON org_unit (manager_id)",
]


# триггерная функция set_updated_at() и триггеры надо создавать отдельно,
# потому что тело функции содержит `;` внутри $$...$$
TRIGGER_BLOCKS = [
    # функция
    """
    CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at := now();
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """,

    # триггеры
    """
    CREATE TRIGGER trg_org_unit_updated_at
    BEFORE UPDATE ON org_unit
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """,
    """
    CREATE TRIGGER trg_employee_updated_at
    BEFORE UPDATE ON employee
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """,
    """
    CREATE TRIGGER trg_team_updated_at
    BEFORE UPDATE ON team
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """,
]


async def main():
    engine = create_async_engine(
        DATABASE_URL,
        isolation_level="AUTOCOMMIT",
    )

    async with engine.begin() as conn:
        print("⚠ DROPPING all known tables/triggers/functions…")
        for stmt in DROP_STATEMENTS:
            print(f" - {stmt}")
            await conn.exec_driver_sql(stmt)
        print("✅ DROP done\n")

        print("🛠 CREATING fresh schema…")
        for stmt in CREATE_STATEMENTS:
            print(f" + {stmt.splitlines()[0][:80]}...")
            await conn.exec_driver_sql(stmt)
        print("✅ CREATE tables/indexes done\n")

        print("🔁 Creating trigger functions…")
        for stmt in TRIGGER_BLOCKS:
            first_line = stmt.strip().splitlines()[0]
            print(f" * {first_line} ...")
            await conn.exec_driver_sql(stmt)
        print("✅ Triggers done\n")

    await engine.dispose()
    print("🎉 DB reset complete")


if __name__ == "__main__":
    asyncio.run(main())
