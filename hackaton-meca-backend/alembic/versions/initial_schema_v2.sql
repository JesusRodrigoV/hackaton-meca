-- =====================================================================
-- HACKATON2 · Sistema Web de Control Presupuestario y Ejecución Financiera
-- Esquema v2 (PostgreSQL 13+)
--
-- CAMBIOS RESPECTO A LA v1
--  1. tipos_cambio con fecha y tipo; movimientos conserva la tasa usada (snapshot).
--  2. presupuestos.month opcional (NULL = anual), moneda original y línea para
--     distinguir filas repetidas.
--  3. FK compuesta (cuenta_id, rubro_id) -> cuentas: rubro y cuenta consistentes.
--  4. Importación idempotente: file_hash, row_hash, staging (importacion_filas),
--     conciliación de totales y reversión lógica (sin borrar en cascada).
--  5. month como smallint (1-12); cuenta contable renombrada para no confundirla
--     con la línea presupuestaria (cuentas).
--  6. Presupuesto vigente: presupuesto_modificaciones (ledger) + vistas.
--  7. modificaciones (reasignación de gasto entre financiadores) con estado,
--     aprobación y efecto calculado en vista, sin tocar movimientos.
--  8. Gestión cerrada: trigger que bloquea cambios.
--  9. financiadores: moneda, vigencia y grupo (para comparar CEL 2026 vs CEL 2027).
-- 10. Auditoría append-only con hash encadenado; reportes programados/generados.
-- 11. Higiene: NOT NULL, timestamptz, CHECKs, updated_at automático.
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- 0. Funciones utilitarias
-- ---------------------------------------------------------------------
CREATE FUNCTION fn_set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------
-- 1. Seguridad: usuarios, roles, permisos
-- ---------------------------------------------------------------------
CREATE TABLE users (
    id              serial        PRIMARY KEY,
    email           varchar(150)  NOT NULL,
    full_name       varchar(150)  NOT NULL,
    password_hash   varchar(255)  NOT NULL,           -- argon2id / bcrypt
    is_active       boolean       NOT NULL DEFAULT true,
    last_login_at   timestamptz   NULL,
    failed_attempts smallint      NOT NULL DEFAULT 0,
    locked_until    timestamptz   NULL,
    created_at      timestamptz   NOT NULL DEFAULT now(),
    updated_at      timestamptz   NOT NULL DEFAULT now()
);
-- Los usuarios se DESACTIVAN (is_active = false), no se borran: la auditoría
-- los referencia con RESTRICT.
CREATE UNIQUE INDEX uq_users_email ON users (lower(email));
CREATE TRIGGER trg_users_updated BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

CREATE TABLE roles (
    id          serial       PRIMARY KEY,
    name        varchar(50)  NOT NULL UNIQUE,
    description text         NULL,
    is_system   boolean      NOT NULL DEFAULT false,
    created_at  timestamptz  NOT NULL DEFAULT now(),
    updated_at  timestamptz  NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_roles_updated BEFORE UPDATE ON roles
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

CREATE TABLE permissions (
    id          serial        PRIMARY KEY,
    code        varchar(100)  NOT NULL UNIQUE,
    module      varchar(50)   NOT NULL,
    description text          NULL,
    created_at  timestamptz   NOT NULL DEFAULT now()
);

CREATE TABLE role_permissions (
    role_id       integer NOT NULL REFERENCES roles (id)       ON DELETE CASCADE,
    permission_id integer NOT NULL REFERENCES permissions (id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE user_roles (
    user_id integer NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    role_id integer NOT NULL REFERENCES roles (id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- Alcance de datos por usuario (seguridad a nivel de fila, aplicada en la API).
-- Regla sugerida: OR entre valores de una misma dimensión, AND entre dimensiones.
-- Sin filas para una dimensión = sin restricción en esa dimensión.
CREATE TABLE user_data_scopes (
    id             serial       PRIMARY KEY,
    user_id        integer      NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    dimension_type varchar(30)  NOT NULL
                   CHECK (dimension_type IN ('region', 'area', 'financiador')),
    dimension_id   integer      NOT NULL,
    created_at     timestamptz  NOT NULL DEFAULT now(),
    CONSTRAINT uq_user_scope UNIQUE (user_id, dimension_type, dimension_id)
);
CREATE INDEX idx_user_data_scopes ON user_data_scopes (user_id, dimension_type);

-- dimension_id es polimórfico: se valida con trigger porque no admite FK.
CREATE FUNCTION fn_validar_scope() RETURNS trigger AS $$
BEGIN
    IF NEW.dimension_type = 'region'
       AND NOT EXISTS (SELECT 1 FROM regiones WHERE id = NEW.dimension_id) THEN
        RAISE EXCEPTION 'regiones.id % no existe', NEW.dimension_id;
    ELSIF NEW.dimension_type = 'area'
       AND NOT EXISTS (SELECT 1 FROM areas WHERE id = NEW.dimension_id) THEN
        RAISE EXCEPTION 'areas.id % no existe', NEW.dimension_id;
    ELSIF NEW.dimension_type = 'financiador'
       AND NOT EXISTS (SELECT 1 FROM financiadores WHERE id = NEW.dimension_id) THEN
        RAISE EXCEPTION 'financiadores.id % no existe', NEW.dimension_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
-- (el trigger se crea más abajo, cuando existan las tablas de catálogo)

-- ---------------------------------------------------------------------
-- 2. Catálogos
-- ---------------------------------------------------------------------
CREATE TABLE regiones (
    id         serial       PRIMARY KEY,
    code       varchar(10)  NOT NULL UNIQUE,
    name       varchar(100) NOT NULL,
    created_at timestamptz  NOT NULL DEFAULT now()
);

CREATE TABLE areas (
    id          serial       PRIMARY KEY,
    name        varchar(120) NOT NULL UNIQUE,
    description text         NULL,
    created_at  timestamptz  NOT NULL DEFAULT now()
);

CREATE TABLE rubros (
    id         serial       PRIMARY KEY,
    code       varchar(20)  NOT NULL UNIQUE,      -- '4', '5', '6'...
    name       varchar(150) NOT NULL,              -- 'Consultoria' (sin el código)
    created_at timestamptz  NOT NULL DEFAULT now()
);

-- Línea presupuestaria dentro de un rubro ('4.1' Videos, '5.3' Viajes...).
-- No confundir con la cuenta CONTABLE (movimientos.cuenta_contable_*).
CREATE TABLE cuentas (
    id         serial       PRIMARY KEY,
    rubro_id   integer      NOT NULL REFERENCES rubros (id) ON DELETE RESTRICT,
    code       varchar(50)  NOT NULL,              -- '4.1'
    name       varchar(150) NOT NULL,              -- 'Videos'
    created_at timestamptz  NOT NULL DEFAULT now(),
    CONSTRAINT uq_cuenta_rubro_code UNIQUE (rubro_id, code),
    CONSTRAINT uq_cuenta_id_rubro   UNIQUE (id, rubro_id)   -- destino de la FK compuesta
);
COMMENT ON TABLE cuentas IS
    'Línea presupuestaria (4.1, 5.3...). La cuenta contable vive en movimientos.cuenta_contable_*.';

-- Grupo estable de fondos: permite comparar "CEL 2026" con "CEL 2027" entre gestiones.
CREATE TABLE financiador_grupos (
    id         serial       PRIMARY KEY,
    code       varchar(50)  NOT NULL UNIQUE,       -- 'CEL', 'INVE', 'CATALYST'
    name       varchar(120) NOT NULL,
    created_at timestamptz  NOT NULL DEFAULT now()
);

CREATE TABLE financiadores (
    id              serial       PRIMARY KEY,
    grupo_id        integer      NULL REFERENCES financiador_grupos (id) ON DELETE SET NULL,
    code            varchar(50)  NULL,
    name            varchar(120) NOT NULL UNIQUE,  -- 'CEL 2026', 'KJCF LACT'
    description     text         NULL,
    moneda          char(3)      NOT NULL DEFAULT 'BOB' CHECK (moneda IN ('BOB', 'USD')),
    vigencia_inicio date         NULL,
    vigencia_fin    date         NULL,
    created_at      timestamptz  NOT NULL DEFAULT now(),
    CONSTRAINT ck_financiador_vigencia
        CHECK (vigencia_fin IS NULL OR vigencia_inicio IS NULL OR vigencia_fin >= vigencia_inicio)
);

CREATE TRIGGER trg_scope_validar BEFORE INSERT OR UPDATE ON user_data_scopes
    FOR EACH ROW EXECUTE FUNCTION fn_validar_scope();

CREATE TABLE gestiones (
    id          serial       PRIMARY KEY,
    year        integer      NOT NULL UNIQUE CHECK (year BETWEEN 2000 AND 2100),
    is_closed   boolean      NOT NULL DEFAULT false,
    closed_at   timestamptz  NULL,
    closed_by   integer      NULL REFERENCES users (id) ON DELETE SET NULL,
    description varchar(100) NULL,
    created_at  timestamptz  NOT NULL DEFAULT now()
);

-- Tipos de cambio por fecha. Una fila por (fecha, tipo).
CREATE TABLE tipos_cambio (
    id     serial        PRIMARY KEY,
    fecha  date          NOT NULL,
    tipo   varchar(15)   NOT NULL DEFAULT 'oficial',   -- oficial, referencial, etc.
    rate   numeric(12,4) NOT NULL CHECK (rate > 0),    -- Bs por 1 USD
    CONSTRAINT uq_tipo_cambio UNIQUE (fecha, tipo)
);

-- ---------------------------------------------------------------------
-- 3. Importaciones (con staging, conciliación y reversión lógica)
-- ---------------------------------------------------------------------
CREATE TABLE importaciones (
    id                    serial        PRIMARY KEY,
    user_id               integer       NULL REFERENCES users (id) ON DELETE SET NULL,
    gestion_id            integer       NOT NULL REFERENCES gestiones (id) ON DELETE RESTRICT,
    file_name             varchar(255)  NOT NULL,
    file_hash             char(64)      NOT NULL,                 -- sha256 del archivo
    modo                  varchar(20)   NOT NULL DEFAULT 'incremental'
                          CHECK (modo IN ('incremental', 'reemplazo_periodo')),
    status                varchar(20)   NOT NULL DEFAULT 'pendiente'
                          CHECK (status IN ('pendiente', 'validado', 'completado', 'revertido', 'fallido')),
    fecha_corte           date          NULL,                     -- max(fecha de comprobante) del archivo
    total_rows            integer       NOT NULL DEFAULT 0,
    processed_rows        integer       NOT NULL DEFAULT 0,
    duplicate_rows        integer       NOT NULL DEFAULT 0,
    error_rows            integer       NOT NULL DEFAULT 0,
    -- Conciliación: lo que dice el archivo vs lo que realmente se cargó
    archivo_debe_bob      numeric(15,2) NULL,
    archivo_haber_bob     numeric(15,2) NULL,
    cargado_debe_bob      numeric(15,2) NULL,
    cargado_haber_bob     numeric(15,2) NULL,
    log_errors            jsonb         NULL,                     -- resumen; el detalle está en importacion_filas
    created_at            timestamptz   NOT NULL DEFAULT now(),
    confirmed_at          timestamptz   NULL,
    reverted_at           timestamptz   NULL
);
-- Impide subir dos veces el mismo archivo (salvo que la carga previa se revirtió o falló)
CREATE UNIQUE INDEX uq_importaciones_hash
    ON importaciones (gestion_id, file_hash)
    WHERE status NOT IN ('revertido', 'fallido');

-- Staging: una fila por fila del Excel. Habilita vista previa y descarga de errores.
CREATE TABLE importacion_filas (
    id             bigserial    PRIMARY KEY,
    importacion_id integer      NOT NULL REFERENCES importaciones (id) ON DELETE CASCADE,
    fila_excel     integer      NOT NULL,
    tipo_fila      varchar(15)  NOT NULL CHECK (tipo_fila IN ('movimiento', 'presupuesto')),
    estado         varchar(15)  NOT NULL CHECK (estado IN ('ok', 'duplicado', 'error', 'omitido')),
    codigo_error   varchar(40)  NULL,
    mensaje_error  text         NULL,
    row_hash       char(64)     NULL,
    raw_json       jsonb        NOT NULL,
    CONSTRAINT uq_importacion_fila UNIQUE (importacion_id, fila_excel)
);
CREATE INDEX idx_importacion_filas_estado ON importacion_filas (importacion_id, estado);

-- ---------------------------------------------------------------------
-- 4. Movimientos (ejecución) – libro inmutable
-- ---------------------------------------------------------------------
CREATE TABLE movimientos (
    id                     bigserial     PRIMARY KEY,
    importacion_id         integer       NULL REFERENCES importaciones (id) ON DELETE RESTRICT,
    gestion_id             integer       NOT NULL REFERENCES gestiones (id)    ON DELETE RESTRICT,
    region_id              integer       NOT NULL REFERENCES regiones (id)     ON DELETE RESTRICT,
    area_id                integer       NOT NULL REFERENCES areas (id)        ON DELETE RESTRICT,
    financiador_id         integer       NOT NULL REFERENCES financiadores (id) ON DELETE RESTRICT,
    rubro_id               integer       NOT NULL REFERENCES rubros (id)       ON DELETE RESTRICT,
    cuenta_id              integer       NULL,
    month                  smallint      NOT NULL CHECK (month BETWEEN 1 AND 12),
    voucher_date           date          NULL,
    voucher_type           integer       NULL,
    voucher_number         integer       NULL,
    check_number           integer       NULL DEFAULT 0,
    cuenta_contable_codigo varchar(50)   NULL,          -- siempre texto (ej. 5102040050)
    cuenta_contable_nombre varchar(150)  NULL,
    reference              text          NULL,
    beneficiario           varchar(200)  NULL,          -- extraído de reference (mejor esfuerzo)
    documento_ref          varchar(60)   NULL,          -- ej. 'R-697'
    debit_bob              numeric(15,2) NOT NULL DEFAULT 0.00 CHECK (debit_bob  >= 0),
    credit_bob             numeric(15,2) NOT NULL DEFAULT 0.00 CHECK (credit_bob >= 0),
    debit_usd              numeric(15,2) NOT NULL DEFAULT 0.00 CHECK (debit_usd  >= 0),
    credit_usd             numeric(15,2) NOT NULL DEFAULT 0.00 CHECK (credit_usd >= 0),
    exchange_rate          numeric(12,4) NOT NULL DEFAULT 6.96 CHECK (exchange_rate > 0),
    tipos_cambio_id        integer       NULL REFERENCES tipos_cambio (id),
    neto_bob               numeric(15,2) GENERATED ALWAYS AS (debit_bob - credit_bob) STORED,
    neto_usd               numeric(15,2) GENERATED ALWAYS AS (debit_usd - credit_usd) STORED,
    row_hash               char(64)      NOT NULL,
    anulado                boolean       NOT NULL DEFAULT false,
    anulado_at             timestamptz   NULL,
    anulado_motivo         text          NULL,
    created_at             timestamptz   NOT NULL DEFAULT now(),
    CONSTRAINT uq_mov_id_gestion UNIQUE (id, gestion_id),
    -- Rubro y cuenta siempre consistentes entre sí
    CONSTRAINT fk_mov_cuenta_rubro FOREIGN KEY (cuenta_id, rubro_id)
        REFERENCES cuentas (id, rubro_id) ON DELETE RESTRICT
);
COMMENT ON COLUMN movimientos.row_hash IS
    'sha256 de los campos normalizados de la fila + n° de ocurrencia dentro del archivo (líneas idénticas legítimas). Evita duplicar al re-importar.';
COMMENT ON COLUMN movimientos.month IS
    'Mes contable del archivo. La API debería advertir (no bloquear) si difiere del mes de voucher_date.';
COMMENT ON COLUMN movimientos.neto_bob IS
    'Ejecución neta = debe - haber.';

-- Un mismo movimiento no puede cargarse dos veces (los anulados no cuentan)
CREATE UNIQUE INDEX uq_movimientos_row_hash ON movimientos (row_hash) WHERE NOT anulado;
CREATE INDEX idx_movimientos_query
    ON movimientos (gestion_id, region_id, area_id, financiador_id, rubro_id, cuenta_id);
CREATE INDEX idx_movimientos_month ON movimientos (gestion_id, month);
CREATE INDEX idx_movimientos_fecha ON movimientos (gestion_id, voucher_date);
CREATE INDEX idx_movimientos_importacion ON movimientos (importacion_id);

-- ---------------------------------------------------------------------
-- 5. Presupuestos y modificaciones
-- ---------------------------------------------------------------------
CREATE TABLE presupuestos (
    id              bigserial     PRIMARY KEY,
    gestion_id      integer       NOT NULL REFERENCES gestiones (id)     ON DELETE RESTRICT,
    region_id       integer       NOT NULL REFERENCES regiones (id)      ON DELETE RESTRICT,
    area_id         integer       NOT NULL REFERENCES areas (id)         ON DELETE RESTRICT,
    financiador_id  integer       NOT NULL REFERENCES financiadores (id) ON DELETE RESTRICT,
    rubro_id        integer       NOT NULL REFERENCES rubros (id)        ON DELETE RESTRICT,
    cuenta_id       integer       NULL,
    month           smallint      NULL CHECK (month IS NULL OR month BETWEEN 1 AND 12), -- NULL = anual
    linea           varchar(150)  NULL,      -- distingue filas con la misma combinación de dimensiones
    moneda          char(3)       NOT NULL DEFAULT 'BOB' CHECK (moneda IN ('BOB', 'USD')),
    monto_original  numeric(15,2) NOT NULL,  -- tal como viene en el archivo, en `moneda`
    amount_bob      numeric(15,2) NOT NULL DEFAULT 0.00,  -- base de reporte
    amount_usd      numeric(15,2) NULL DEFAULT 0.00,
    tipos_cambio_id integer       NULL REFERENCES tipos_cambio (id),  -- tasa usada si hubo conversión
    importacion_id  integer       NULL REFERENCES importaciones (id) ON DELETE RESTRICT,
    created_at      timestamptz   NOT NULL DEFAULT now(),
    updated_at      timestamptz   NOT NULL DEFAULT now(),
    CONSTRAINT ck_pres_monto_bob CHECK (moneda <> 'BOB' OR monto_original = amount_bob),
    CONSTRAINT uq_pres_id_gestion UNIQUE (id, gestion_id),
    CONSTRAINT fk_pres_cuenta_rubro FOREIGN KEY (cuenta_id, rubro_id)
        REFERENCES cuentas (id, rubro_id) ON DELETE RESTRICT
);
COMMENT ON TABLE presupuestos IS
    'Presupuesto inicial. Si el Excel trae filas repetidas para la misma combinación, el importador las suma o usa "linea" para distinguirlas.';
CREATE UNIQUE INDEX uq_presupuestos_linea ON presupuestos (
    gestion_id, region_id, area_id, financiador_id, rubro_id,
    COALESCE(cuenta_id, 0), COALESCE(month, 0), COALESCE(linea, '')
);
CREATE INDEX idx_presupuestos_query
    ON presupuestos (gestion_id, region_id, area_id, financiador_id, rubro_id, cuenta_id);
CREATE TRIGGER trg_presupuestos_updated BEFORE UPDATE ON presupuestos
    FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- Reformulaciones de presupuesto (ledger de solo inserciones; el estado es lo único que cambia)
CREATE TABLE presupuesto_modificaciones (
    id                     bigserial     PRIMARY KEY,
    gestion_id             integer       NOT NULL REFERENCES gestiones (id) ON DELETE RESTRICT,
    tipo                   varchar(20)   NOT NULL CHECK (tipo IN ('ampliacion', 'reduccion', 'traspaso')),
    origen_presupuesto_id  bigint        NULL REFERENCES presupuestos (id) ON DELETE RESTRICT,
    destino_presupuesto_id bigint        NULL REFERENCES presupuestos (id) ON DELETE RESTRICT,
    amount_bob             numeric(15,2) NOT NULL CHECK (amount_bob > 0),
    reason                 text          NOT NULL,
    estado                 varchar(15)   NOT NULL DEFAULT 'borrador'
                           CHECK (estado IN ('borrador', 'aprobado', 'rechazado')),
    solicitado_por         integer       NULL REFERENCES users (id) ON DELETE SET NULL,
    aprobado_por           integer       NULL REFERENCES users (id) ON DELETE SET NULL,
    aprobado_at            timestamptz   NULL,
    created_at             timestamptz   NOT NULL DEFAULT now(),
    CONSTRAINT ck_pm_direccion CHECK (
           (tipo = 'ampliacion' AND destino_presupuesto_id IS NOT NULL AND origen_presupuesto_id IS NULL)
        OR (tipo = 'reduccion'  AND origen_presupuesto_id  IS NOT NULL AND destino_presupuesto_id IS NULL)
        OR (tipo = 'traspaso'   AND origen_presupuesto_id  IS NOT NULL AND destino_presupuesto_id IS NOT NULL
                                AND origen_presupuesto_id <> destino_presupuesto_id)),
    CONSTRAINT ck_pm_aprobacion CHECK (estado <> 'aprobado' OR (aprobado_por IS NOT NULL AND aprobado_at IS NOT NULL))
    -- Opcional (segregación de funciones): CHECK (aprobado_por IS NULL OR aprobado_por <> solicitado_por)
);
CREATE INDEX idx_pm_gestion_estado ON presupuesto_modificaciones (gestion_id, estado);

-- Reasignación de GASTO entre financiadores (el movimiento original no se toca;
-- su efecto se aplica en la vista v_ejecucion_efectiva).
CREATE TABLE modificaciones (
    id                     bigserial     PRIMARY KEY,
    gestion_id             integer       NOT NULL,
    movimiento_id          bigint        NOT NULL,
    financiador_origen_id  integer       NOT NULL REFERENCES financiadores (id) ON DELETE RESTRICT,
    financiador_destino_id integer       NOT NULL REFERENCES financiadores (id) ON DELETE RESTRICT,
    amount_bob             numeric(15,2) NOT NULL CHECK (amount_bob > 0),
    reason                 text          NOT NULL,
    estado                 varchar(15)   NOT NULL DEFAULT 'borrador'
                           CHECK (estado IN ('borrador', 'aprobado', 'rechazado')),
    solicitado_por         integer       NULL REFERENCES users (id) ON DELETE SET NULL,
    aprobado_por           integer       NULL REFERENCES users (id) ON DELETE SET NULL,
    aprobado_at            timestamptz   NULL,
    created_at             timestamptz   NOT NULL DEFAULT now(),
    CONSTRAINT ck_mod_financiadores CHECK (financiador_origen_id <> financiador_destino_id),
    CONSTRAINT ck_mod_aprobacion CHECK (estado <> 'aprobado' OR (aprobado_por IS NOT NULL AND aprobado_at IS NOT NULL)),
    -- el movimiento debe pertenecer a la misma gestión
    CONSTRAINT fk_mod_movimiento FOREIGN KEY (movimiento_id, gestion_id)
        REFERENCES movimientos (id, gestion_id) ON DELETE RESTRICT
);
CREATE INDEX idx_modificaciones_mov ON modificaciones (movimiento_id, estado);

-- ---------------------------------------------------------------------
-- 6. Gestión cerrada: nadie escribe en una gestión cerrada
-- ---------------------------------------------------------------------
CREATE FUNCTION fn_bloquear_gestion_cerrada() RETURNS trigger AS $$
DECLARE
    v_gid    integer;
    v_closed boolean;
BEGIN
    FOR v_gid IN
        SELECT DISTINCT g FROM unnest(ARRAY[
            CASE WHEN TG_OP <> 'INSERT' THEN OLD.gestion_id END,
            CASE WHEN TG_OP <> 'DELETE' THEN NEW.gestion_id END
        ]) AS g WHERE g IS NOT NULL
    LOOP
        SELECT is_closed INTO v_closed FROM gestiones WHERE id = v_gid;
        IF v_closed THEN
            RAISE EXCEPTION 'La gestión (id=%) está cerrada: no se permiten cambios en %.', v_gid, TG_TABLE_NAME
                USING ERRCODE = 'check_violation';
        END IF;
    END LOOP;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_mov_gestion_cerrada BEFORE INSERT OR UPDATE OR DELETE ON movimientos
    FOR EACH ROW EXECUTE FUNCTION fn_bloquear_gestion_cerrada();
CREATE TRIGGER trg_pres_gestion_cerrada BEFORE INSERT OR UPDATE OR DELETE ON presupuestos
    FOR EACH ROW EXECUTE FUNCTION fn_bloquear_gestion_cerrada();
CREATE TRIGGER trg_pm_gestion_cerrada BEFORE INSERT OR UPDATE OR DELETE ON presupuesto_modificaciones
    FOR EACH ROW EXECUTE FUNCTION fn_bloquear_gestion_cerrada();
CREATE TRIGGER trg_mod_gestion_cerrada BEFORE INSERT OR UPDATE OR DELETE ON modificaciones
    FOR EACH ROW EXECUTE FUNCTION fn_bloquear_gestion_cerrada();

-- ---------------------------------------------------------------------
-- 7. Auditoría: append-only con hash encadenado (evidencia de manipulación)
-- ---------------------------------------------------------------------
CREATE TABLE audit_chain_head (
    id        smallint PRIMARY KEY CHECK (id = 1),
    last_hash char(64) NULL
);
INSERT INTO audit_chain_head (id, last_hash) VALUES (1, NULL);

CREATE TABLE audit_logs (
    id           bigserial    PRIMARY KEY,
    user_id      integer      NULL REFERENCES users (id) ON DELETE RESTRICT,
    action       varchar(80)  NOT NULL,        -- login, import.create, report.export, budget.modify...
    entity       varchar(80)  NOT NULL,
    entity_id    varchar(50)  NULL,
    details_json jsonb        NULL,            -- filtros usados, antes/después, etc.
    ip_address   varchar(45)  NULL,
    user_agent   varchar(300) NULL,
    request_id   varchar(64)  NULL,
    created_at   timestamptz  NOT NULL DEFAULT now(),
    prev_hash    char(64)     NULL,
    row_hash     char(64)     NULL
);
CREATE INDEX idx_audit_logs_user   ON audit_logs (user_id, created_at);
CREATE INDEX idx_audit_logs_entity ON audit_logs (entity, entity_id);

CREATE FUNCTION fn_audit_chain() RETURNS trigger AS $$
BEGIN
    -- El bloqueo de fila sobre la cabecera serializa los inserts y evita bifurcar la cadena
    SELECT last_hash INTO NEW.prev_hash FROM audit_chain_head WHERE id = 1 FOR UPDATE;
    NEW.row_hash := encode(sha256(convert_to(concat_ws('|',
        NEW.id, NEW.user_id, NEW.action, NEW.entity, NEW.entity_id,
        NEW.details_json::text, NEW.ip_address,
        extract(epoch FROM NEW.created_at)::text, NEW.prev_hash), 'UTF8')), 'hex');
    UPDATE audit_chain_head SET last_hash = NEW.row_hash WHERE id = 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_chain BEFORE INSERT ON audit_logs
    FOR EACH ROW EXECUTE FUNCTION fn_audit_chain();

CREATE FUNCTION fn_audit_inmutable() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'audit_logs es de solo inserción (% bloqueado)', TG_OP;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_no_mod BEFORE UPDATE OR DELETE ON audit_logs
    FOR EACH ROW EXECUTE FUNCTION fn_audit_inmutable();
CREATE TRIGGER trg_audit_no_truncate BEFORE TRUNCATE ON audit_logs
    FOR EACH STATEMENT EXECUTE FUNCTION fn_audit_inmutable();
-- Refuerzo recomendado en producción: REVOKE UPDATE, DELETE, TRUNCATE ON audit_logs FROM <rol_de_la_app>;
-- Verificación de la cadena: recorrer por prev_hash y recomputar row_hash.

-- ---------------------------------------------------------------------
-- 8. Reportes: definiciones, programación y archivos generados
-- ---------------------------------------------------------------------
CREATE TABLE reportes_definiciones (
    id          serial       PRIMARY KEY,
    code        varchar(40)  NOT NULL UNIQUE,
    name        varchar(120) NOT NULL,
    descripcion text         NULL,
    tipo        varchar(15)  NOT NULL CHECK (tipo IN ('agregado', 'detalle', 'resumen')),
    dimensiones jsonb        NOT NULL DEFAULT '[]',   -- niveles desplegables, en orden
    orden       smallint     NOT NULL DEFAULT 0
);

CREATE TABLE reportes_programados (
    id               serial       PRIMARY KEY,
    reporte_id       integer      NULL REFERENCES reportes_definiciones (id) ON DELETE CASCADE, -- NULL = paquete de los 7
    name             varchar(120) NOT NULL,
    cron_expr        varchar(50)  NOT NULL,           -- ej. '0 7 * * 1'
    formato          varchar(10)  NOT NULL DEFAULT 'xlsx' CHECK (formato IN ('xlsx', 'pdf', 'ambos')),
    parametros_json  jsonb        NOT NULL DEFAULT '{}',
    destinatarios    jsonb        NOT NULL DEFAULT '[]',
    activo           boolean      NOT NULL DEFAULT true,
    creado_por       integer      NULL REFERENCES users (id) ON DELETE SET NULL,
    ultima_ejecucion timestamptz  NULL,
    created_at       timestamptz  NOT NULL DEFAULT now()
);

CREATE TABLE reportes_generados (
    id              bigserial    PRIMARY KEY,
    reporte_id      integer      NULL REFERENCES reportes_definiciones (id) ON DELETE SET NULL,
    programacion_id integer      NULL REFERENCES reportes_programados (id) ON DELETE SET NULL,
    gestion_id      integer      NOT NULL REFERENCES gestiones (id) ON DELETE RESTRICT,
    importacion_id  integer      NULL REFERENCES importaciones (id) ON DELETE SET NULL, -- última carga incluida
    fecha_corte     date         NOT NULL,
    formato         varchar(10)  NOT NULL CHECK (formato IN ('xlsx', 'pdf')),
    origen          varchar(20)  NOT NULL DEFAULT 'manual'
                    CHECK (origen IN ('manual', 'programado', 'post_importacion')),
    parametros_json jsonb        NOT NULL DEFAULT '{}',   -- filtros aplicados
    file_path       text         NOT NULL,
    file_sha256     char(64)     NOT NULL,
    file_size       bigint       NULL,
    generado_por    integer      NULL REFERENCES users (id) ON DELETE SET NULL,
    generado_at     timestamptz  NOT NULL DEFAULT now()
);
CREATE INDEX idx_reportes_generados ON reportes_generados (gestion_id, reporte_id, generado_at DESC);

-- ---------------------------------------------------------------------
-- 9. Vistas: un solo origen de verdad para los 7 reportes
-- ---------------------------------------------------------------------

-- Ejecución con las reasignaciones aprobadas aplicadas (movimientos sigue intacto).
-- Cada reasignación resta del financiador origen y suma al destino; soporta parciales y cadenas.
CREATE VIEW v_ejecucion_efectiva AS
SELECT m.id AS movimiento_id, NULL::bigint AS modificacion_id,
       m.gestion_id, m.region_id, m.area_id, m.financiador_id, m.rubro_id, m.cuenta_id,
       m.month, m.voucher_date, m.neto_bob, m.neto_usd
FROM movimientos m
WHERE NOT m.anulado
UNION ALL
SELECT m.id, mo.id,
       m.gestion_id, m.region_id, m.area_id, mo.financiador_origen_id, m.rubro_id, m.cuenta_id,
       m.month, m.voucher_date,
       -mo.amount_bob,
       -round(mo.amount_bob / m.exchange_rate, 2)
FROM modificaciones mo
JOIN movimientos m ON m.id = mo.movimiento_id
WHERE mo.estado = 'aprobado' AND NOT m.anulado
UNION ALL
SELECT m.id, mo.id,
       m.gestion_id, m.region_id, m.area_id, mo.financiador_destino_id, m.rubro_id, m.cuenta_id,
       m.month, m.voucher_date,
       mo.amount_bob,
       round(mo.amount_bob / m.exchange_rate, 2)
FROM modificaciones mo
JOIN movimientos m ON m.id = mo.movimiento_id
WHERE mo.estado = 'aprobado' AND NOT m.anulado;

-- Presupuesto inicial + modificaciones aprobadas = vigente (anual, por combinación de dimensiones)
CREATE VIEW v_presupuesto_vigente AS
WITH deltas AS (
    SELECT destino_presupuesto_id AS presupuesto_id, amount_bob AS delta
    FROM presupuesto_modificaciones
    WHERE estado = 'aprobado' AND destino_presupuesto_id IS NOT NULL
    UNION ALL
    SELECT origen_presupuesto_id, -amount_bob
    FROM presupuesto_modificaciones
    WHERE estado = 'aprobado' AND origen_presupuesto_id IS NOT NULL
), por_linea AS (
    SELECT presupuesto_id, SUM(delta) AS delta FROM deltas GROUP BY presupuesto_id
)
SELECT p.gestion_id, p.region_id, p.area_id, p.financiador_id, p.rubro_id,
       COALESCE(p.cuenta_id, 0)                           AS cuenta_key,   -- 0 = sin cuenta
       SUM(p.amount_bob)                                  AS inicial_bob,
       COALESCE(SUM(l.delta), 0)                          AS modificaciones_bob,
       SUM(p.amount_bob) + COALESCE(SUM(l.delta), 0)      AS vigente_bob
FROM presupuestos p
LEFT JOIN por_linea l ON l.presupuesto_id = p.id
GROUP BY p.gestion_id, p.region_id, p.area_id, p.financiador_id, p.rubro_id, COALESCE(p.cuenta_id, 0);

-- Presupuesto vs ejecución con FULL OUTER JOIN: nada queda oculto
-- (ejecución sin presupuesto, presupuesto sin ejecución, sobre-ejecución).
CREATE VIEW v_ejecucion_vs_presupuesto AS
WITH ejec AS (
    SELECT gestion_id, region_id, area_id, financiador_id, rubro_id,
           COALESCE(cuenta_id, 0) AS cuenta_key,
           SUM(neto_bob)          AS ejecutado_bob
    FROM v_ejecucion_efectiva
    GROUP BY gestion_id, region_id, area_id, financiador_id, rubro_id, COALESCE(cuenta_id, 0)
)
SELECT COALESCE(p.gestion_id, e.gestion_id)       AS gestion_id,
       COALESCE(p.region_id, e.region_id)         AS region_id,
       COALESCE(p.area_id, e.area_id)             AS area_id,
       COALESCE(p.financiador_id, e.financiador_id) AS financiador_id,
       COALESCE(p.rubro_id, e.rubro_id)           AS rubro_id,
       NULLIF(COALESCE(p.cuenta_key, e.cuenta_key), 0) AS cuenta_id,
       COALESCE(p.inicial_bob, 0)                 AS presupuesto_inicial_bob,
       COALESCE(p.modificaciones_bob, 0)          AS modificaciones_bob,
       COALESCE(p.vigente_bob, 0)                 AS presupuesto_vigente_bob,
       COALESCE(e.ejecutado_bob, 0)               AS ejecutado_bob,
       COALESCE(p.vigente_bob, 0) - COALESCE(e.ejecutado_bob, 0) AS saldo_bob,
       CASE WHEN COALESCE(p.vigente_bob, 0) > 0
            THEN round(COALESCE(e.ejecutado_bob, 0) / p.vigente_bob * 100, 2) END AS pct_ejecucion,
       CASE WHEN p.gestion_id IS NULL THEN 'EJECUCION_SIN_PRESUPUESTO'
            WHEN e.gestion_id IS NULL THEN 'SIN_EJECUCION'
            WHEN e.ejecutado_bob > p.vigente_bob THEN 'SOBREEJECUCION'
            ELSE 'OK' END                         AS alerta
FROM v_presupuesto_vigente p
FULL OUTER JOIN ejec e
  ON  p.gestion_id     = e.gestion_id
  AND p.region_id      = e.region_id
  AND p.area_id        = e.area_id
  AND p.financiador_id = e.financiador_id
  AND p.rubro_id       = e.rubro_id
  AND p.cuenta_key     = e.cuenta_key;

-- ---------------------------------------------------------------------
-- 10. Datos iniciales
-- ---------------------------------------------------------------------
INSERT INTO permissions (code, module, description) VALUES
 ('dashboard.ver',          'dashboard',     'Ver el dashboard'),
 ('reportes.ver',           'reportes',      'Consultar reportes'),
 ('reportes.exportar',      'reportes',      'Exportar reportes a Excel/PDF'),
 ('reportes.programar',     'reportes',      'Programar reportes automáticos'),
 ('importaciones.ver',      'importaciones', 'Ver historial de importaciones'),
 ('importaciones.crear',    'importaciones', 'Subir y validar archivos'),
 ('importaciones.confirmar','importaciones', 'Confirmar una carga validada'),
 ('importaciones.revertir', 'importaciones', 'Revertir una carga'),
 ('presupuestos.ver',       'presupuestos',  'Ver presupuestos'),
 ('presupuestos.editar',    'presupuestos',  'Crear/editar presupuestos'),
 ('modificaciones.solicitar','modificaciones','Solicitar modificaciones'),
 ('modificaciones.aprobar', 'modificaciones','Aprobar o rechazar modificaciones'),
 ('catalogos.editar',       'catalogos',     'Editar financiadores, áreas, rubros, cuentas, regiones'),
 ('gestiones.cerrar',       'gestiones',     'Cerrar o reabrir una gestión'),
 ('usuarios.admin',         'seguridad',     'Administrar usuarios y alcances de datos'),
 ('roles.admin',            'seguridad',     'Administrar roles y permisos'),
 ('auditoria.ver',          'seguridad',     'Consultar el registro de auditoría');

INSERT INTO roles (name, description, is_system) VALUES
 ('Administrador', 'Acceso total',                                         true),
 ('Directivo',     'Consulta global, exporta y aprueba modificaciones',    true),
 ('Contador',      'Importa archivos, administra catálogos y presupuestos', true),
 ('Tecnico',       'Consulta y exporta dentro de su alcance de datos',     true),
 ('Auditor',       'Solo lectura, incluida la auditoría',                  true);

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON
     r.name = 'Administrador'
  OR (r.name = 'Directivo' AND p.code IN
        ('dashboard.ver','reportes.ver','reportes.exportar','reportes.programar',
         'presupuestos.ver','importaciones.ver','modificaciones.aprobar','gestiones.cerrar'))
  OR (r.name = 'Contador' AND p.code IN
        ('dashboard.ver','reportes.ver','reportes.exportar','importaciones.ver',
         'importaciones.crear','importaciones.confirmar','importaciones.revertir',
         'presupuestos.ver','presupuestos.editar','modificaciones.solicitar','catalogos.editar'))
  OR (r.name = 'Tecnico' AND p.code IN
        ('dashboard.ver','reportes.ver','reportes.exportar','presupuestos.ver','modificaciones.solicitar'))
  OR (r.name = 'Auditor' AND p.code IN
        ('dashboard.ver','reportes.ver','reportes.exportar','importaciones.ver',
         'presupuestos.ver','auditoria.ver'));

INSERT INTO reportes_definiciones (code, name, descripcion, tipo, dimensiones, orden) VALUES
 ('ejec_rubro_cuenta',  'Ejecución por rubro y cuenta',     'Rubro desplegable a cuenta',          'agregado', '["rubro","cuenta"]',     1),
 ('ejec_financiador',   'Ejecución por financiador',        'Totales por financiador',             'agregado', '["financiador"]',        2),
 ('ejec_area_financ',   'Ejecución por área y financiador', 'Área desplegable a financiador',      'agregado', '["area","financiador"]', 3),
 ('ejec_region',        'Ejecución por región',             'Totales por región',                  'agregado', '["region"]',             4),
 ('ejec_mes',           'Ejecución por mes',                'Evolución mensual',                   'agregado', '["mes"]',                5),
 ('detalle_movimientos','Detalle de movimientos',           'Comprobantes línea por línea',        'detalle',  '[]',                     6),
 ('resumen_general',    'Resumen general consolidado',      'Presupuesto vs ejecución consolidado','resumen',  '[]',                     7);

COMMIT;
-- End of file.
