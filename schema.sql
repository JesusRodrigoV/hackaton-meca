-- ==============================================================================
-- SISTEMA DE CONTROL PRESUPUESTARIO Y EJECUCIÓN FINANCIERA (ENSEÑA POR BOLIVIA)
-- Esquema relacional PostgreSQL (DDL) con RBAC granular, auditoría y catálogos
-- ==============================================================================

-- Extensiones útiles
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==============================================================================
-- 1. BLOQUE DE SEGURIDAD, RBAC DINÁMICO Y AUDITORÍA
-- ==============================================================================

CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    code VARCHAR(100) UNIQUE NOT NULL,       -- ej: 'reports:view', 'budget:edit', 'users:manage'
    module VARCHAR(50) NOT NULL,             -- ej: 'REPORTES', 'PRESUPUESTO', 'USUARIOS'
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,        -- ej: 'SUPER_ADMIN', 'FINANZAS', 'COORDINADOR', 'AUDITOR'
    description TEXT,
    is_system BOOLEAN DEFAULT FALSE,         -- Roles protegidos del sistema
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE role_permissions (
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(150) UNIQUE NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_roles (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- Granularidad de datos por usuario (Data Scoping):
-- Permite que un usuario solo tenga acceso a ciertas Regiones, Áreas o Financiadores
CREATE TABLE user_data_scopes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    dimension_type VARCHAR(30) NOT NULL,      -- 'REGION', 'AREA', 'FINANCIADOR'
    dimension_id INTEGER NOT NULL,            -- id referenciado en la tabla correspondiente
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_scope UNIQUE (user_id, dimension_type, dimension_id)
);

-- Registro de Auditoría obligatorio según requerimiento
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(80) NOT NULL,             -- 'LOGIN', 'IMPORT_EXCEL', 'EDIT_BUDGET', etc.
    entity VARCHAR(80) NOT NULL,             -- 'presupuestos', 'movimientos', 'roles'
    entity_id VARCHAR(50),
    details_json JSONB,                      -- Valores previos vs nuevos
    ip_address VARCHAR(45),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- 2. BLOQUE DE CATÁLOGOS MAESTROS Y GESTIONES
-- ==============================================================================

CREATE TABLE gestiones (
    id SERIAL PRIMARY KEY,
    year INTEGER UNIQUE NOT NULL,             -- ej: 2026, 2025
    is_closed BOOLEAN DEFAULT FALSE,
    description VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE regiones (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,         -- ej: 'LP', 'SC'
    name VARCHAR(100) NOT NULL,                -- ej: 'La Paz', 'Santa Cruz'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE areas (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) UNIQUE NOT NULL,        -- ej: 'ALUMNI', 'CAMBIO SISTEMICO', 'PROGRAMA'
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE financiadores (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50),
    name VARCHAR(120) UNIQUE NOT NULL,        -- ej: 'CATALYST 18', 'CEL 2026', 'KJCF LACT'
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE rubros (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,         -- ej: '4', '5', '6', '7', '8', '9'
    name VARCHAR(150) NOT NULL,                -- ej: '4. Consultoria', '5. Viajes'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cuentas (
    id SERIAL PRIMARY KEY,
    rubro_id INTEGER NOT NULL REFERENCES rubros(id) ON DELETE RESTRICT,
    code VARCHAR(50) NOT NULL,                -- ej: '4.1', '5.2', '5102080010'
    name VARCHAR(150) NOT NULL,                -- ej: '4.1 Videos', 'ALQUILER OFICINA'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_cuenta_rubro_code UNIQUE (rubro_id, code)
);

CREATE TABLE tipos_cambio (
    id SERIAL PRIMARY KEY,
    gestion_id INTEGER NOT NULL REFERENCES gestiones(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    rate NUMERIC(12, 4) NOT NULL,             -- ej: 6.9600 o tasas de mercado
    currency_from VARCHAR(5) DEFAULT 'USD',
    currency_to VARCHAR(5) DEFAULT 'BOB',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_fecha_tipo_cambio UNIQUE (gestion_id, date, currency_from, currency_to)
);

-- ==============================================================================
-- 3. BLOQUE TRANSACCIONAL: IMPORTACIONES, PRESUPUESTOS, MOVIMIENTOS Y MODIFICACIONES
-- ==============================================================================

CREATE TABLE importaciones (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    gestion_id INTEGER NOT NULL REFERENCES gestiones(id) ON DELETE RESTRICT,
    file_name VARCHAR(255) NOT NULL,
    status VARCHAR(30) DEFAULT 'COMPLETADO',  -- 'PROCESANDO', 'COMPLETADO', 'ERROR'
    total_rows INTEGER DEFAULT 0,
    processed_rows INTEGER DEFAULT 0,
    error_rows INTEGER DEFAULT 0,
    log_errors JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Planificación / Líneas Presupuestarias
CREATE TABLE presupuestos (
    id BIGSERIAL PRIMARY KEY,
    gestion_id INTEGER NOT NULL REFERENCES gestiones(id) ON DELETE RESTRICT,
    region_id INTEGER NOT NULL REFERENCES regiones(id) ON DELETE RESTRICT,
    area_id INTEGER NOT NULL REFERENCES areas(id) ON DELETE RESTRICT,
    financiador_id INTEGER NOT NULL REFERENCES financiadores(id) ON DELETE RESTRICT,
    rubro_id INTEGER NOT NULL REFERENCES rubros(id) ON DELETE RESTRICT,
    cuenta_id INTEGER REFERENCES cuentas(id) ON DELETE SET NULL,
    month VARCHAR(20) NOT NULL,               -- 'ENERO'..'SEPTIEMBRE', 'PTTO' (anual / sin mes asignado)
    amount_bob NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    amount_usd NUMERIC(15, 2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Ejecución Real / Asientos Contables
CREATE TABLE movimientos (
    id BIGSERIAL PRIMARY KEY,
    importacion_id INTEGER REFERENCES importaciones(id) ON DELETE CASCADE,
    gestion_id INTEGER NOT NULL REFERENCES gestiones(id) ON DELETE RESTRICT,
    
    -- Dimensiones contables
    region_id INTEGER NOT NULL REFERENCES regiones(id) ON DELETE RESTRICT,
    area_id INTEGER NOT NULL REFERENCES areas(id) ON DELETE RESTRICT,
    financiador_id INTEGER NOT NULL REFERENCES financiadores(id) ON DELETE RESTRICT,
    rubro_id INTEGER NOT NULL REFERENCES rubros(id) ON DELETE RESTRICT,
    cuenta_id INTEGER REFERENCES cuentas(id) ON DELETE SET NULL,
    
    -- Datos del comprobante
    month VARCHAR(20) NOT NULL,               -- 'ENERO', 'FEBRERO', etc.
    voucher_date DATE,                        -- cfecha
    voucher_type INTEGER,                     -- tipo (1: Ingreso, 2: Egreso, 3: Traspaso)
    voucher_number INTEGER,                   -- numero
    check_number INTEGER DEFAULT 0,           -- no_cheque
    account_code VARCHAR(50),                 -- codigo contable (ej: '5102080013')
    account_name VARCHAR(150),                -- nombre contable (ej: 'LIMPIEZA DE OFICINA')
    reference TEXT,                           -- ref / glosa descriptiva
    
    -- Importes en Bolivianos
    debit_bob NUMERIC(15, 2) NOT NULL DEFAULT 0.00,  -- Ejecución real en Bs
    credit_bob NUMERIC(15, 2) NOT NULL DEFAULT 0.00, -- haber
    
    -- Importes en Dólares
    debit_usd NUMERIC(15, 2) NOT NULL DEFAULT 0.00,  -- dsus
    credit_usd NUMERIC(15, 2) NOT NULL DEFAULT 0.00, -- hsus
    exchange_rate NUMERIC(12, 4) NOT NULL DEFAULT 6.96,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Modificaciones / Reclasificaciones presupuestarias o de fondos
CREATE TABLE modificaciones (
    id BIGSERIAL PRIMARY KEY,
    movimiento_id BIGINT REFERENCES movimientos(id) ON DELETE CASCADE,
    financiador_origen_id INTEGER NOT NULL REFERENCES financiadores(id) ON DELETE RESTRICT,
    financiador_destino_id INTEGER NOT NULL REFERENCES financiadores(id) ON DELETE RESTRICT,
    amount_bob NUMERIC(15, 2) NOT NULL,
    reason TEXT NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- 4. ÍNDICES DE RENDIMIENTO (Clave para reportes dinámicos inmediatos)
-- ==============================================================================

CREATE INDEX idx_presupuestos_query ON presupuestos (gestion_id, region_id, area_id, financiador_id, rubro_id, cuenta_id);
CREATE INDEX idx_movimientos_query ON movimientos (gestion_id, region_id, area_id, financiador_id, rubro_id, cuenta_id);
CREATE INDEX idx_movimientos_month ON movimientos (gestion_id, month);
CREATE INDEX idx_audit_logs_user ON audit_logs (user_id, created_at);
CREATE INDEX idx_user_data_scopes ON user_data_scopes (user_id, dimension_type);
