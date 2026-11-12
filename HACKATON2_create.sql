-- Created by Redgate Data Modeler (https://datamodeler.redgate-platform.com)
-- Last modification date: 2026-11-12 14:39:29.03

-- tables
-- Table: areas
CREATE TABLE areas (
    id serial  NOT NULL,
    name varchar(120)  NOT NULL,
    description text  NULL,
    created_at timestamp  NULL DEFAULT current_timestamp,
    CONSTRAINT AK_5 UNIQUE (name) NOT DEFERRABLE  INITIALLY IMMEDIATE,
    CONSTRAINT areas_pk PRIMARY KEY (id)
);

-- Table: audit_logs
CREATE TABLE audit_logs (
    id bigserial  NOT NULL,
    user_id integer  NULL,
    action varchar(80)  NOT NULL,
    entity varchar(80)  NOT NULL,
    entity_id varchar(50)  NULL,
    details_json jsonb  NULL,
    ip_address varchar(45)  NULL,
    created_at timestamp  NULL DEFAULT current_timestamp,
    CONSTRAINT audit_logs_pk PRIMARY KEY (id)
);

CREATE INDEX idx_audit_logs_user on audit_logs (user_id ASC,created_at ASC);

-- Table: cuentas
CREATE TABLE cuentas (
    id serial  NOT NULL,
    rubro_id integer  NOT NULL,
    code varchar(50)  NOT NULL,
    name varchar(150)  NOT NULL,
    created_at timestamp  NULL DEFAULT current_timestamp,
    CONSTRAINT uq_cuenta_rubro_code UNIQUE (rubro_id, code) NOT DEFERRABLE  INITIALLY IMMEDIATE,
    CONSTRAINT cuentas_pk PRIMARY KEY (id)
);

-- Table: financiadores
CREATE TABLE financiadores (
    id serial  NOT NULL,
    code varchar(50)  NULL,
    name varchar(120)  NOT NULL,
    description text  NULL,
    created_at timestamp  NULL DEFAULT current_timestamp,
    CONSTRAINT AK_6 UNIQUE (name) NOT DEFERRABLE  INITIALLY IMMEDIATE,
    CONSTRAINT financiadores_pk PRIMARY KEY (id)
);

-- Table: gestiones
CREATE TABLE gestiones (
    id serial  NOT NULL,
    year integer  NOT NULL,
    is_closed boolean  NULL DEFAULT false,
    description varchar(100)  NULL,
    created_at timestamp  NULL DEFAULT current_timestamp,
    CONSTRAINT AK_3 UNIQUE (year) NOT DEFERRABLE  INITIALLY IMMEDIATE,
    CONSTRAINT gestiones_pk PRIMARY KEY (id)
);

-- Table: importaciones
CREATE TABLE importaciones (
    id serial  NOT NULL,
    user_id integer  NULL,
    gestion_id integer  NOT NULL,
    file_name varchar(255)  NOT NULL,
    status varchar(30)  NULL DEFAULT 'completado',
    total_rows integer  NULL DEFAULT 0,
    processed_rows integer  NULL DEFAULT 0,
    error_rows integer  NULL DEFAULT 0,
    log_errors jsonb  NULL,
    created_at timestamp  NULL DEFAULT current_timestamp,
    CONSTRAINT importaciones_pk PRIMARY KEY (id)
);

-- Table: modificaciones
CREATE TABLE modificaciones (
    id bigserial  NOT NULL,
    movimiento_id bigint  NULL,
    financiador_origen_id integer  NOT NULL,
    financiador_destino_id integer  NOT NULL,
    amount_bob numeric(15,2)  NOT NULL,
    reason text  NOT NULL,
    user_id integer  NULL,
    created_at timestamp  NULL DEFAULT current_timestamp,
    CONSTRAINT modificaciones_pk PRIMARY KEY (id)
);

-- Table: movimientos
CREATE TABLE movimientos (
    id bigserial  NOT NULL,
    importacion_id integer  NULL,
    gestion_id integer  NOT NULL,
    region_id integer  NOT NULL,
    area_id integer  NOT NULL,
    financiador_id integer  NOT NULL,
    rubro_id integer  NOT NULL,
    cuenta_id integer  NULL,
    month varchar(20)  NOT NULL,
    voucher_date date  NULL,
    voucher_type integer  NULL,
    voucher_number integer  NULL,
    check_number integer  NULL DEFAULT 0,
    account_code varchar(50)  NULL,
    account_name varchar(150)  NULL,
    reference text  NULL,
    debit_bob numeric(15,2)  NOT NULL DEFAULT 0.00,
    credit_bob numeric(15,2)  NOT NULL DEFAULT 0.00,
    debit_usd numeric(15,2)  NOT NULL DEFAULT 0.00,
    credit_usd numeric(15,2)  NOT NULL DEFAULT 0.00,
    exchange_rate numeric(12,4)  NOT NULL DEFAULT 6.96,
    created_at timestamp  NULL DEFAULT current_timestamp,
    tipos_cambio_id int  NOT NULL,
    CONSTRAINT movimientos_pk PRIMARY KEY (id)
);

CREATE INDEX idx_movimientos_query on movimientos (gestion_id ASC,region_id ASC,area_id ASC,financiador_id ASC,rubro_id ASC,cuenta_id ASC);

CREATE INDEX idx_movimientos_month on movimientos (gestion_id ASC,month ASC);

-- Table: permissions
CREATE TABLE permissions (
    id serial  NOT NULL,
    code varchar(100)  NOT NULL,
    module varchar(50)  NOT NULL,
    description text  NULL,
    created_at timestamp  NULL DEFAULT current_timestamp,
    CONSTRAINT AK_0 UNIQUE (code) NOT DEFERRABLE  INITIALLY IMMEDIATE,
    CONSTRAINT permissions_pk PRIMARY KEY (id)
);

-- Table: presupuestos
CREATE TABLE presupuestos (
    id bigserial  NOT NULL,
    gestion_id integer  NOT NULL,
    region_id integer  NOT NULL,
    area_id integer  NOT NULL,
    financiador_id integer  NOT NULL,
    rubro_id integer  NOT NULL,
    cuenta_id integer  NULL,
    month varchar(20)  NOT NULL,
    amount_bob numeric(15,2)  NOT NULL DEFAULT 0.00,
    amount_usd numeric(15,2)  NULL DEFAULT 0.00,
    created_at timestamp  NULL DEFAULT current_timestamp,
    updated_at timestamp  NULL DEFAULT current_timestamp,
    CONSTRAINT presupuestos_pk PRIMARY KEY (id)
);

CREATE INDEX idx_presupuestos_query on presupuestos (gestion_id ASC,region_id ASC,area_id ASC,financiador_id ASC,rubro_id ASC,cuenta_id ASC);

-- Table: regiones
CREATE TABLE regiones (
    id serial  NOT NULL,
    code varchar(10)  NOT NULL,
    name varchar(100)  NOT NULL,
    created_at timestamp  NULL DEFAULT current_timestamp,
    CONSTRAINT AK_4 UNIQUE (code) NOT DEFERRABLE  INITIALLY IMMEDIATE,
    CONSTRAINT regiones_pk PRIMARY KEY (id)
);

-- Table: role_permissions
CREATE TABLE role_permissions (
    role_id integer  NOT NULL,
    permission_id integer  NOT NULL,
    CONSTRAINT role_permissions_pk PRIMARY KEY (role_id,permission_id)
);

-- Table: roles
CREATE TABLE roles (
    id serial  NOT NULL,
    name varchar(50)  NOT NULL,
    description text  NULL,
    is_system boolean  NULL DEFAULT false,
    created_at timestamp  NULL DEFAULT current_timestamp,
    updated_at timestamp  NULL DEFAULT current_timestamp,
    CONSTRAINT AK_1 UNIQUE (name) NOT DEFERRABLE  INITIALLY IMMEDIATE,
    CONSTRAINT roles_pk PRIMARY KEY (id)
);

-- Table: rubros
CREATE TABLE rubros (
    id serial  NOT NULL,
    code varchar(20)  NOT NULL,
    name varchar(150)  NOT NULL,
    created_at timestamp  NULL DEFAULT current_timestamp,
    CONSTRAINT AK_7 UNIQUE (code) NOT DEFERRABLE  INITIALLY IMMEDIATE,
    CONSTRAINT rubros_pk PRIMARY KEY (id)
);

-- Table: tipos_cambio
CREATE TABLE tipos_cambio (
    id int  NOT NULL,
    rate decimal(6,3)  NOT NULL,
    fuente varchar(10)  NOT NULL,
    CONSTRAINT tipos_cambio_pk PRIMARY KEY (id)
);

-- Table: user_data_scopes
CREATE TABLE user_data_scopes (
    id serial  NOT NULL,
    user_id integer  NOT NULL,
    dimension_type varchar(30)  NOT NULL,
    dimension_id integer  NOT NULL,
    created_at timestamp  NULL DEFAULT current_timestamp,
    CONSTRAINT uq_user_scope UNIQUE (user_id, dimension_type, dimension_id) NOT DEFERRABLE  INITIALLY IMMEDIATE,
    CONSTRAINT user_data_scopes_pk PRIMARY KEY (id)
);

CREATE INDEX idx_user_data_scopes on user_data_scopes (user_id ASC,dimension_type ASC);

-- Table: user_roles
CREATE TABLE user_roles (
    user_id integer  NOT NULL,
    role_id integer  NOT NULL,
    CONSTRAINT user_roles_pk PRIMARY KEY (user_id,role_id)
);

-- Table: users
CREATE TABLE users (
    id serial  NOT NULL,
    email varchar(150)  NOT NULL,
    full_name varchar(150)  NOT NULL,
    password_hash varchar(255)  NOT NULL,
    is_active boolean  NULL DEFAULT true,
    created_at timestamp  NULL DEFAULT current_timestamp,
    updated_at timestamp  NULL DEFAULT current_timestamp,
    CONSTRAINT AK_2 UNIQUE (email) NOT DEFERRABLE  INITIALLY IMMEDIATE,
    CONSTRAINT users_pk PRIMARY KEY (id)
);

-- foreign keys
-- Reference: FK_0 (table: role_permissions)
ALTER TABLE role_permissions ADD CONSTRAINT FK_0
    FOREIGN KEY (role_id)
    REFERENCES roles (id)
    ON DELETE  CASCADE  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: FK_1 (table: role_permissions)
ALTER TABLE role_permissions ADD CONSTRAINT FK_1
    FOREIGN KEY (permission_id)
    REFERENCES permissions (id)
    ON DELETE  CASCADE  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: FK_10 (table: presupuestos)
ALTER TABLE presupuestos ADD CONSTRAINT FK_10
    FOREIGN KEY (gestion_id)
    REFERENCES gestiones (id)
    ON DELETE  RESTRICT  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: FK_11 (table: presupuestos)
ALTER TABLE presupuestos ADD CONSTRAINT FK_11
    FOREIGN KEY (region_id)
    REFERENCES regiones (id)
    ON DELETE  RESTRICT  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: FK_12 (table: presupuestos)
ALTER TABLE presupuestos ADD CONSTRAINT FK_12
    FOREIGN KEY (area_id)
    REFERENCES areas (id)
    ON DELETE  RESTRICT  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: FK_13 (table: presupuestos)
ALTER TABLE presupuestos ADD CONSTRAINT FK_13
    FOREIGN KEY (financiador_id)
    REFERENCES financiadores (id)
    ON DELETE  RESTRICT  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: FK_14 (table: presupuestos)
ALTER TABLE presupuestos ADD CONSTRAINT FK_14
    FOREIGN KEY (rubro_id)
    REFERENCES rubros (id)
    ON DELETE  RESTRICT  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: FK_15 (table: presupuestos)
ALTER TABLE presupuestos ADD CONSTRAINT FK_15
    FOREIGN KEY (cuenta_id)
    REFERENCES cuentas (id)
    ON DELETE  SET NULL  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: FK_16 (table: movimientos)
ALTER TABLE movimientos ADD CONSTRAINT FK_16
    FOREIGN KEY (importacion_id)
    REFERENCES importaciones (id)
    ON DELETE  CASCADE  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: FK_17 (table: movimientos)
ALTER TABLE movimientos ADD CONSTRAINT FK_17
    FOREIGN KEY (gestion_id)
    REFERENCES gestiones (id)
    ON DELETE  RESTRICT  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: FK_18 (table: movimientos)
ALTER TABLE movimientos ADD CONSTRAINT FK_18
    FOREIGN KEY (region_id)
    REFERENCES regiones (id)
    ON DELETE  RESTRICT  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: FK_19 (table: movimientos)
ALTER TABLE movimientos ADD CONSTRAINT FK_19
    FOREIGN KEY (area_id)
    REFERENCES areas (id)
    ON DELETE  RESTRICT  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: FK_2 (table: user_roles)
ALTER TABLE user_roles ADD CONSTRAINT FK_2
    FOREIGN KEY (user_id)
    REFERENCES users (id)
    ON DELETE  CASCADE  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: FK_20 (table: movimientos)
ALTER TABLE movimientos ADD CONSTRAINT FK_20
    FOREIGN KEY (financiador_id)
    REFERENCES financiadores (id)
    ON DELETE  RESTRICT  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: FK_21 (table: movimientos)
ALTER TABLE movimientos ADD CONSTRAINT FK_21
    FOREIGN KEY (rubro_id)
    REFERENCES rubros (id)
    ON DELETE  RESTRICT  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: FK_22 (table: movimientos)
ALTER TABLE movimientos ADD CONSTRAINT FK_22
    FOREIGN KEY (cuenta_id)
    REFERENCES cuentas (id)
    ON DELETE  SET NULL  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: FK_23 (table: modificaciones)
ALTER TABLE modificaciones ADD CONSTRAINT FK_23
    FOREIGN KEY (movimiento_id)
    REFERENCES movimientos (id)
    ON DELETE  CASCADE  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: FK_24 (table: modificaciones)
ALTER TABLE modificaciones ADD CONSTRAINT FK_24
    FOREIGN KEY (financiador_origen_id)
    REFERENCES financiadores (id)
    ON DELETE  RESTRICT  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: FK_25 (table: modificaciones)
ALTER TABLE modificaciones ADD CONSTRAINT FK_25
    FOREIGN KEY (financiador_destino_id)
    REFERENCES financiadores (id)
    ON DELETE  RESTRICT  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: FK_26 (table: modificaciones)
ALTER TABLE modificaciones ADD CONSTRAINT FK_26
    FOREIGN KEY (user_id)
    REFERENCES users (id)
    ON DELETE  SET NULL  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: FK_3 (table: user_roles)
ALTER TABLE user_roles ADD CONSTRAINT FK_3
    FOREIGN KEY (role_id)
    REFERENCES roles (id)
    ON DELETE  CASCADE  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: FK_4 (table: user_data_scopes)
ALTER TABLE user_data_scopes ADD CONSTRAINT FK_4
    FOREIGN KEY (user_id)
    REFERENCES users (id)
    ON DELETE  CASCADE  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: FK_5 (table: audit_logs)
ALTER TABLE audit_logs ADD CONSTRAINT FK_5
    FOREIGN KEY (user_id)
    REFERENCES users (id)
    ON DELETE  SET NULL  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: FK_6 (table: cuentas)
ALTER TABLE cuentas ADD CONSTRAINT FK_6
    FOREIGN KEY (rubro_id)
    REFERENCES rubros (id)
    ON DELETE  RESTRICT  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: FK_8 (table: importaciones)
ALTER TABLE importaciones ADD CONSTRAINT FK_8
    FOREIGN KEY (user_id)
    REFERENCES users (id)
    ON DELETE  SET NULL  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: FK_9 (table: importaciones)
ALTER TABLE importaciones ADD CONSTRAINT FK_9
    FOREIGN KEY (gestion_id)
    REFERENCES gestiones (id)
    ON DELETE  RESTRICT  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- Reference: movimientos_tipos_cambio (table: movimientos)
ALTER TABLE movimientos ADD CONSTRAINT movimientos_tipos_cambio
    FOREIGN KEY (tipos_cambio_id)
    REFERENCES tipos_cambio (id)  
    NOT DEFERRABLE 
    INITIALLY IMMEDIATE
;

-- End of file.

