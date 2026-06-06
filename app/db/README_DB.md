# Módulo DBB / DBA - SEMAPA Grupo 4

Este módulo reemplaza el mockup visual con una base de datos real en SQLite para la demo académica.

## Qué contiene

- `schema.sql`: estructura local SQLite.
- `schema_postgresql.sql`: diseño equivalente para PostgreSQL.
- `repository.py`: capa de acceso a datos y consultas reutilizables.
- `routes.py`: endpoints `/db` para que los otros módulos consuman información.

## Ejecución rápida

Desde la raíz del proyecto:

```bash
python init_db.py
python run.py
```

Abrir:

```text
http://127.0.0.1:5000/db/status
```

## Endpoints principales

```text
/db/status
/db/seed
/db/reset-seed
/db/api/resumen
/db/api/distritos
/db/api/consumo-diario
/db/api/sensores
/db/api/clima
/db/api/preaviso?buscar=C-000001&periodo=2026-04
```

## Tablas creadas

- `subalcaldias`
- `distritos`
- `zonas`
- `categorias_tarifarias`
- `clientes`
- `infraestructuras`
- `contratos`
- `radiobases`
- `medidores`
- `lecturas_iot`
- `lecturas_manuales`
- `preavisos`
- `mensajes_preaviso`
- `carga_logs`

## Nota técnica

La práctica solicita 120.000 medidores y lecturas masivas. Para que corra en una laptop se genera una muestra controlada:

- 1.000 infraestructuras
- 1.000 contratos
- 1.200 medidores
- 100.000 lecturas IoT
- 14 radiobases
- 56 zonas
- 14 distritos
- 6 subalcaldías

La estructura permite escalar a los volúmenes reales usando PostgreSQL o Cassandra/ScyllaDB.
