-- ==============================================================================================
-- PROYECTO FINAL: MODELO DIMENSIONAL (STAR SCHEMA / SNOWFLAKE)
-- SCRIPT DE CREACIÓN DE TABLAS (POSTGRESQL)
-- ==============================================================================================

-- ----------------------------------------------------------------------------------------------
-- 0. LIMPIEZA PREVIA (DROP TABLES)
-- Se eliminan en orden inverso a sus dependencias para evitar errores de llaves foráneas.
-- ----------------------------------------------------------------------------------------------
DROP TABLE IF EXISTS F_HechoMatricula;
DROP TABLE IF EXISTS D_Alumno;
DROP TABLE IF EXISTS D_Semestre;
DROP TABLE IF EXISTS D_Carrera;
DROP TABLE IF EXISTS D_Motivo;
DROP TABLE IF EXISTS D_Jornada;
DROP TABLE IF EXISTS D_Fecha;
DROP TABLE IF EXISTS D_Financiamiento;
DROP TABLE IF EXISTS D_Ocupacion;
DROP TABLE IF EXISTS D_Ciudad;
DROP TABLE IF EXISTS D_Estrato;
DROP TABLE IF EXISTS D_Genero;


-- ----------------------------------------------------------------------------------------------
-- 1. CREACIÓN DE DIMENSIONES SIMPLES
-- Tablas catálogo que almacenan atributos descriptivos
-- ----------------------------------------------------------------------------------------------

-- Dimensión Género
CREATE TABLE D_Genero (
    id_genero INTEGER PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL 
);

-- Dimensión Estrato
CREATE TABLE D_Estrato (
    id_estrato INTEGER PRIMARY KEY,
    descripcion VARCHAR(50) NOT NULL 
);

-- Dimensión Ciudad
CREATE TABLE D_Ciudad (
    id_ciudad INTEGER PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL 
);

-- Dimensión Ocupación
CREATE TABLE D_Ocupacion (
    id_ocupacion INTEGER PRIMARY KEY,
    descripcion VARCHAR(100) NOT NULL 
);

-- Dimensión Financiamiento
CREATE TABLE D_Financiamiento (
    id_financiamiento INTEGER PRIMARY KEY,
    nombre_financiamiento VARCHAR(100) NOT NULL 
);

-- Dimensión Jornada
CREATE TABLE D_Jornada (
    id_jornada INTEGER PRIMARY KEY,
    tipo VARCHAR(50) NOT NULL 
);

-- Dimensión Motivo / Estado del semestre
CREATE TABLE D_Motivo (
    id_motivo INTEGER PRIMARY KEY,
    tipo VARCHAR(100) NOT NULL 
);

-- Dimensión Carrera
CREATE TABLE D_Carrera (
    id_carrera INTEGER PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL 
);


-- ----------------------------------------------------------------------------------------------
-- 2. CREACIÓN DE DIMENSIONES COMPLEJAS Y FECHA
-- ----------------------------------------------------------------------------------------------

-- Dimensión Fecha (Id numérico formato YYYYMMDD)
CREATE TABLE D_Fecha (
    id_fecha INTEGER PRIMARY KEY,
    anio INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    dia INTEGER NOT NULL
);

-- Dimensión Semestre (Incluye valor financiero e histórico)
CREATE TABLE D_Semestre (
    id_semestre INTEGER PRIMARY KEY,
    semestre INTEGER NOT NULL,
    valor NUMERIC(12,2) NOT NULL, 
    activo BOOLEAN NOT NULL,
    id_fecha_creacion INTEGER NOT NULL,
    id_fecha_actualizacion INTEGER NOT NULL
);


-- ----------------------------------------------------------------------------------------------
-- 3. CREACIÓN DE LA DIMENSIÓN ALUMNO (SCD TIPO 2)
-- Contiene el historial completo de cambios sociodemográficos del estudiante.
-- ----------------------------------------------------------------------------------------------
CREATE TABLE D_Alumno (
    id_alumno INTEGER PRIMARY KEY,
    tipo_identificacion VARCHAR(50),
    numero_identificacion VARCHAR(100) NOT NULL, 
    nombre VARCHAR(150),
    telefono VARCHAR(50),
    direccion VARCHAR(200),
    edad INTEGER,
    
    -- Llaves Foráneas hacia las dimensiones simples
    id_genero INTEGER REFERENCES D_Genero(id_genero),
    id_estrato INTEGER REFERENCES D_Estrato(id_estrato),
    id_ciudad INTEGER REFERENCES D_Ciudad(id_ciudad),
    id_ocupacion INTEGER REFERENCES D_Ocupacion(id_ocupacion),
    id_financiamiento INTEGER REFERENCES D_Financiamiento(id_financiamiento),
    id_fecha_nacimiento INTEGER REFERENCES D_Fecha(id_fecha),
    
    -- Campos de Auditoría SCD Tipo 2
    id_fecha_creacion INTEGER NOT NULL,
    id_fecha_actualizacion INTEGER NOT NULL,
    activo BOOLEAN NOT NULL -- True si es el perfil actual, False si es histórico
);


-- ----------------------------------------------------------------------------------------------
-- 4. CREACIÓN DE LA TABLA DE HECHOS (FACT TABLE)
-- Tabla central que almacena las métricas cuantitativas (KPIs) y cruza todas las dimensiones.
-- ----------------------------------------------------------------------------------------------
CREATE TABLE F_HechoMatricula (
    -- Llave primaria autoincremental propia de la tabla de hechos
    id_hecho SERIAL PRIMARY KEY, 
    
    -- Llaves Foráneas hacia todas las dimensiones
    id_alumno INTEGER REFERENCES D_Alumno(id_alumno),
    id_carrera INTEGER REFERENCES D_Carrera(id_carrera),
    id_semestre INTEGER REFERENCES D_Semestre(id_semestre),
    id_motivo INTEGER REFERENCES D_Motivo(id_motivo),
    id_jornada INTEGER REFERENCES D_Jornada(id_jornada),
    
    -- Llaves foráneas hacia la Dimensión Fecha
    id_fecha_inicio_estudios INTEGER REFERENCES D_Fecha(id_fecha),
    id_fecha_desercion INTEGER REFERENCES D_Fecha(id_fecha),
    id_fecha_inicio_semestre INTEGER REFERENCES D_Fecha(id_fecha),
    id_fecha_final_semestre INTEGER REFERENCES D_Fecha(id_fecha),
    
    -- Métricas / Medidas (Measures)
    promedio_semestral NUMERIC(3,1), -- Decimal pequeño (Ej: 4.5)
    cantidad_materias_perdidas VARCHAR(50), -- Es texto porque los datos vienen como "1 a 2"
    valor_perdida_por_desercion NUMERIC(12,2) DEFAULT 0.0,
    valor_deuda NUMERIC(12,2) DEFAULT 0.0,
    
    -- Campos de auditoría
    id_fecha_creacion INTEGER NOT NULL,
    id_fecha_actualizacion INTEGER NOT NULL,
    activo BOOLEAN NOT NULL
);