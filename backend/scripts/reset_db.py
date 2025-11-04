import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

# !! ВСТАВЬ свой DSN:
DATABASE_URL = "postgresql+asyncpg://flooruser:17HjvfPfryjv@89.208.14.204:5432/floordb"

DROP_STATEMENTS = [
    # триггеры → функция
    "DROP TRIGGER IF EXISTS trg_employee_updated_at ON employee",
    "DROP TRIGGER IF EXISTS trg_org_unit_updated_at ON org_unit",
    "DROP FUNCTION IF EXISTS set_updated_at() CASCADE",

    # таблицы (с зависимостями)
    "DROP TABLE IF EXISTS audit_log                 CASCADE",
    "DROP TABLE IF EXISTS sync_record               CASCADE",
    "DROP TABLE IF EXISTS photo_moderation          CASCADE",
    "DROP TABLE IF EXISTS employee                  CASCADE",
    "DROP TABLE IF EXISTS media                     CASCADE",
    "DROP TABLE IF EXISTS org_unit                  CASCADE",
    "DROP TABLE IF EXISTS external_entity_snapshot  CASCADE",
    "DROP TABLE IF EXISTS sync_job                  CASCADE",
]

CREATE_STATEMENTS = [
    # 0) расширения (могут уже быть)
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
    "CREATE INDEX idx_sync_job_started_at  ON sync_job (started_at)",
    "CREATE INDEX idx_sync_job_finished_at ON sync_job (finished_at)",
    "CREATE INDEX idx_sync_job_status      ON sync_job (status)",

    # 2) external_entity_snapshot (теперь только сотрудники; без entity_type/local_id)
    """
    CREATE TABLE external_entity_snapshot (
        id            BIGSERIAL PRIMARY KEY,
        external_ref  TEXT NOT NULL,
        job_id        BIGINT NOT NULL REFERENCES sync_job(id) ON DELETE CASCADE,
        payload       JSONB NOT NULL,
        normalized    JSONB NOT NULL,
        received_at   TIMESTAMPTZ NOT NULL
    )
    """,
    "CREATE UNIQUE INDEX uq_ees_job_external_ref ON external_entity_snapshot (job_id, external_ref)",
    "CREATE INDEX idx_ees_external_ref_received  ON external_entity_snapshot (external_ref, received_at)",

    # 3) org_unit (manager_id колонка есть, FK добавим позже, когда employee уже создан)
    """
    CREATE TABLE org_unit (
        id            BIGSERIAL PRIMARY KEY,

        parent_id     BIGINT NULL REFERENCES org_unit(id) ON DELETE SET NULL,

        unit_type     TEXT NOT NULL
            CHECK (unit_type IN ('group','domain','legal_entity','department','direction')),

        name          TEXT NOT NULL,

        is_archived   BOOLEAN NOT NULL DEFAULT FALSE,

        manager_id    BIGINT NULL,

        created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX idx_org_unit_parent_id ON org_unit (parent_id)",
    "CREATE INDEX idx_org_unit_manager_id ON org_unit (manager_id)",
    # уникальность названия в рамках типа (кейс-индефференто)
    "CREATE UNIQUE INDEX uq_org_unit_type_name_lower ON org_unit (lower(name), unit_type)",
    # триграммный индекс по названию
    "CREATE INDEX idx_org_unit_name_trgm ON org_unit USING GIN (lower(name) gin_trgm_ops)",

    # 4) media
    """
    CREATE TABLE media (
        id           BIGSERIAL PRIMARY KEY,
        storage_key  TEXT NOT NULL,
        created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    "CREATE UNIQUE INDEX uq_media_storage_key ON media (storage_key)",

    # 5) employee
    """
    CREATE TABLE employee (
        id                     BIGSERIAL PRIMARY KEY,

        external_ref           TEXT NULL,

        email                  TEXT NOT NULL UNIQUE,

        first_name             TEXT NOT NULL,
        middle_name            TEXT NULL,
        last_name              TEXT NOT NULL,

        title                  TEXT NOT NULL,

        status                 TEXT NOT NULL
            CHECK (status IN ('active','dismissed'))
            DEFAULT 'active',

        manager_id             BIGINT NULL REFERENCES employee(id) ON DELETE SET NULL,

        lowest_org_unit_id     BIGINT NULL REFERENCES org_unit(id) ON DELETE SET NULL,

        bio                    TEXT NULL,
        skill_ratings          JSONB NULL,

        work_city              TEXT NULL,
        work_format            TEXT NULL
            CHECK (work_format IN ('office','hybrid','remote')),
        time_zone              TEXT NULL,

        work_phone             TEXT NULL,
        mattermost_handle      TEXT NULL,

        birth_date             DATE NULL,
        hire_date              DATE NULL CHECK (hire_date <= CURRENT_DATE),

        photo_id               BIGINT NULL REFERENCES media(id) ON DELETE SET NULL,

        last_applied_snapshot_id BIGINT NULL
            REFERENCES external_entity_snapshot(id) ON DELETE SET NULL,

        password_hash          TEXT NULL,
        is_blocked             BOOLEAN NOT NULL DEFAULT FALSE,
        last_login_at          TIMESTAMPTZ NULL,
        is_admin               BOOLEAN NOT NULL DEFAULT FALSE,

        search_tsv tsvector GENERATED ALWAYS AS (
            setweight(to_tsvector('russian', coalesce(first_name,'')),  'A') ||
            setweight(to_tsvector('russian', coalesce(middle_name,'')), 'A') ||
            setweight(to_tsvector('russian', coalesce(last_name,'')),   'A') ||
            setweight(to_tsvector('russian', coalesce(title,'')),       'B') ||
            setweight(to_tsvector('russian', coalesce(bio,'')),         'D')
        ) STORED,

        created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at             TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX idx_employee_last_name_trgm  ON employee USING GIN (lower(last_name) gin_trgm_ops)",
    "CREATE INDEX idx_employee_title_trgm      ON employee USING GIN (lower(title) gin_trgm_ops)",
    "CREATE INDEX idx_employee_manager_id      ON employee (manager_id)",
    "CREATE INDEX idx_employee_status          ON employee (status)",
    "CREATE INDEX idx_employee_search_tsv      ON employee USING GIN (search_tsv)",
    "CREATE INDEX idx_employee_skill_ratings   ON employee USING GIN ((skill_ratings))",

    # 6) photo_moderation (с частичным уник. индексом на pending)
    """
    CREATE TABLE photo_moderation (
        id                    BIGSERIAL PRIMARY KEY,
        employee_id           BIGINT NOT NULL REFERENCES employee(id) ON DELETE CASCADE,
        media_id              BIGINT NOT NULL REFERENCES media(id) ON DELETE CASCADE,
        status                TEXT NOT NULL
            CHECK (status IN ('pending','approved','rejected'))
            DEFAULT 'pending',
        reviewer_employee_id  BIGINT NULL REFERENCES employee(id) ON DELETE SET NULL,
        reviewed_at           TIMESTAMPTZ NULL,
        reject_reason         TEXT NULL,
        created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX idx_photo_moderation_status        ON photo_moderation (status)",
    "CREATE INDEX idx_photo_moderation_employee      ON photo_moderation (employee_id)",
    "CREATE INDEX idx_photo_moderation_reviewer      ON photo_moderation (reviewer_employee_id)",
    "CREATE INDEX idx_photo_moderation_created_at    ON photo_moderation (created_at)",
    "CREATE UNIQUE INDEX uq_photo_mod_one_pending_per_employee ON photo_moderation (employee_id) WHERE status = 'pending'",
    "CREATE INDEX idx_photo_mod_pending_emp ON photo_moderation (employee_id) WHERE status = 'pending'",

    # 7) sync_record (без entity_type/local_id)
    """
    CREATE TABLE sync_record (
        id           BIGSERIAL PRIMARY KEY,
        job_id       BIGINT NOT NULL REFERENCES sync_job(id) ON DELETE CASCADE,
        external_ref TEXT NOT NULL,
        action       TEXT NOT NULL CHECK (action IN ('create','update','archive')),
        status       TEXT NOT NULL CHECK (status IN ('applied','orphaned','error')),
        decision     TEXT NULL CHECK (decision IN ('archive','keep')),
        decided_by_employee_id BIGINT NULL REFERENCES employee(id) ON DELETE SET NULL,
        decided_at  TIMESTAMPTZ NULL,
        message     TEXT NULL,
        created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX idx_sync_record_job_external ON sync_record (job_id, external_ref)",
    "CREATE INDEX idx_sync_record_job_id      ON sync_record (job_id)",

    # 8) audit_log
    """
    CREATE TABLE audit_log (
        id                  BIGSERIAL PRIMARY KEY,
        actor_employee_id   BIGINT NULL REFERENCES employee(id) ON DELETE SET NULL,
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

    # 9) теперь навешиваем FK для org_unit.manager_id (после создания employee)
    """
    ALTER TABLE org_unit
    ADD CONSTRAINT org_unit_manager_fk
    FOREIGN KEY (manager_id)
    REFERENCES employee(id)
    ON DELETE SET NULL
    """,
]

TRIGGER_BLOCKS = [
    # Функция
    """
    CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at := now();
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """,
    # Триггеры
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
            head = stmt.strip().splitlines()[0] if stmt.strip() else stmt
            print(f" + {head[:80]} ...")
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
