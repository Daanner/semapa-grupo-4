"""
Capa de datos SEMAPA Grupo 4.

Este módulo es la entrega del equipo DBB/DBA:
- crea la base SQLite local para la demo académica;
- puebla datos simulados consistentes;
- expone consultas reutilizables para Dashboard, PDF, Mensajería, Tótem y Lector Manual.

No requiere servicios externos para correr en clase. En producción, el diseño se puede migrar a PostgreSQL.
"""

from __future__ import annotations

import hashlib
import os
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = Path(os.getenv("SEMAPA_DB_PATH", BASE_DIR / "semapa.db"))
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

MODELOS_MEDIDOR = [
    "Itron OpenWay Riva",
    "Landis+Gyr E360",
    "Honeywell Elster",
    "Kamstrup MULTICAL",
    "Sensus iPERL",
]

TARIFAS = {
    1: {"nombre": "Doméstica", "precio_m3": 4.02},
    2: {"nombre": "Social", "precio_m3": 2.50},
    3: {"nombre": "Comercial", "precio_m3": 6.80},
    4: {"nombre": "Industrial A", "precio_m3": 9.50},
    5: {"nombre": "Estatal", "precio_m3": 3.20},
    6: {"nombre": "Industrial B", "precio_m3": 12.00},
    7: {"nombre": "Especial", "precio_m3": 5.10},
    8: {"nombre": "Uso múltiple", "precio_m3": 7.30},
    9: {"nombre": "Mixta", "precio_m3": 5.80},
}


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Crea todas las tablas si no existen."""
    with get_connection() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.commit()


def reset_db() -> None:
    """Elimina la base y la vuelve a crear."""
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row is not None else None


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(r) for r in rows]


def calcular_importe(consumo_m3: float, categoria_id: int) -> float:
    tarifa = TARIFAS.get(int(categoria_id), TARIFAS[1])
    return round(float(consumo_m3) * float(tarifa["precio_m3"]), 2)


def _random_mac(rng: random.Random) -> str:
    return ":".join(f"{rng.randint(0, 255):02X}" for _ in range(6))


def _hash_evento(medidor_id: int, fecha_hora: str, lectura_actual: float, radiobase_id: int) -> str:
    raw = f"{medidor_id}|{fecha_hora}|{lectura_actual:.2f}|{radiobase_id}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def seed_db(
    force: bool = False,
    total_infraestructuras: int = 1000,
    total_contratos: int = 1000,
    total_medidores: int = 1200,
    total_lecturas: int = 100000,
) -> dict[str, Any]:
    """
    Puebla la BD con datos simulados.

    La tarea real habla de 80k/100k infraestructuras, 100k contratos y 120k medidores.
    Para que corra en una laptop de clase se genera una muestra controlada, manteniendo la estructura.
    El volumen de lecturas por defecto sí llega a 100.000 eventos para probar dashboard y consultas.
    """
    init_db()
    rng = random.Random(2026)

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS total FROM medidores")
        if cur.fetchone()["total"] > 0 and not force:
            return {"ok": True, "message": "La base ya tenía datos. Use force=True para reiniciar.", "db_path": str(DB_PATH)}

    if force:
        reset_db()

    subalcaldias = [
        "Adela Zamudio",
        "Tunari",
        "Molle",
        "Valle Hermoso",
        "Alejo Calatayud",
        "Itocta",
    ]

    zonas_nombres = [
        "Cala Cala", "Queru Queru", "Muyurina", "Sarco", "Temporal", "Mayorazgo", "Tupuraya",
        "Recoleta", "Centro", "San Pedro", "Las Cuadras", "Alalay", "Villa Pagador", "Valle Hermoso",
        "La Maica", "Kara Kara", "Ticti Norte", "Ticti Sud", "Pacata", "Chimba", "Coña Coña",
        "Colquiri", "Quintanilla", "Sivingani", "Sebastian Pagador", "Pucara", "Jayhuayco", "Santa Vera Cruz",
    ]
    tipos_infra = ["Vivienda", "Comercio", "Industria", "Institución", "Mixta"]
    nombres = ["Juan", "María", "Luis", "Ana", "Pedro", "Rosa", "Carlos", "Elena", "Miguel", "Carmen", "José", "Lucía"]
    apellidos = ["Mendoza", "Quispe", "Rojas", "Mamani", "Vargas", "Flores", "Camacho", "Torrico", "García", "Zeballos"]

    inserted = {}
    start = datetime(2026, 2, 1, 0, 0)

    with get_connection() as conn:
        cur = conn.cursor()

        # Tarifas
        cur.executemany(
            "INSERT OR IGNORE INTO categorias_tarifarias (id, nombre, tarifa_base, descripcion) VALUES (?, ?, ?, ?)",
            [(i, v["nombre"], v["precio_m3"], f"Categoría tarifaria {v['nombre']}") for i, v in TARIFAS.items()],
        )

        # Subalcaldías
        for nombre in subalcaldias:
            cur.execute("INSERT OR IGNORE INTO subalcaldias (nombre) VALUES (?)", (nombre,))

        # Distritos: 14
        cur.execute("SELECT id FROM subalcaldias ORDER BY id")
        sub_ids = [r["id"] for r in cur.fetchall()]
        for i in range(1, 15):
            sub_id = sub_ids[(i - 1) % len(sub_ids)]
            cur.execute(
                "INSERT OR IGNORE INTO distritos (subalcaldia_id, codigo, nombre, poblacion) VALUES (?, ?, ?, ?)",
                (sub_id, f"D-{i:02d}", f"Distrito {i}", rng.randint(25000, 75000)),
            )

        # Zonas: 56
        cur.execute("SELECT id FROM distritos ORDER BY id")
        distrito_ids = [r["id"] for r in cur.fetchall()]
        riesgos = ["NORMAL", "ALERTA", "CRITICO"]
        for i in range(1, 57):
            distrito_id = distrito_ids[(i - 1) % len(distrito_ids)]
            base_nombre = zonas_nombres[(i - 1) % len(zonas_nombres)]
            cur.execute(
                """
                INSERT OR IGNORE INTO zonas (distrito_id, codigo, nombre, latitud, longitud, riesgo_hidrico)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    distrito_id,
                    f"Z-{i:03d}",
                    f"{base_nombre} {i}",
                    round(-17.3895 + rng.uniform(-0.12, 0.12), 7),
                    round(-66.1568 + rng.uniform(-0.16, 0.16), 7),
                    rng.choices(riesgos, weights=[75, 18, 7])[0],
                ),
            )

        # Radiobases: 14
        cur.execute("SELECT id, latitud, longitud FROM zonas ORDER BY id")
        zonas_rows = cur.fetchall()
        for i in range(1, 15):
            z = zonas_rows[(i - 1) % len(zonas_rows)]
            cur.execute(
                """
                INSERT OR IGNORE INTO radiobases (id, nombre, codigo, zona_id, latitud, longitud, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (i, f"Radiobase LoRaWAN {i}", f"RB-{i:02d}", z["id"], z["latitud"], z["longitud"], "ACTIVA"),
            )

        # Clientes
        clientes = []
        for i in range(1, max(total_contratos, total_infraestructuras) + 1):
            nom = rng.choice(nombres)
            ape = f"{rng.choice(apellidos)} {rng.choice(apellidos)}"
            ci = f"{rng.randint(3000000, 9999999)}"
            clientes.append((ci, nom, ape, f"7{rng.randint(1000000,9999999)}", f"{nom.lower()}.{i}@correo.com", f"Calle {rng.randint(1,999)} Zona {rng.randint(1,56)}"))
        cur.executemany(
            "INSERT OR IGNORE INTO clientes (ci_nit, nombres, apellidos, telefono, correo, direccion) VALUES (?, ?, ?, ?, ?, ?)",
            clientes,
        )

        # Infraestructuras
        cur.execute("SELECT id FROM zonas ORDER BY id")
        zona_ids = [r["id"] for r in cur.fetchall()]
        infra = []
        for i in range(1, total_infraestructuras + 1):
            zona_id = zona_ids[(i - 1) % len(zona_ids)]
            infra.append((
                f"INF-{i:06d}", zona_id, f"Av. SEMAPA #{i}, Zona {zona_id}", rng.choice(tipos_infra),
                "ACTIVA", round(-17.3895 + rng.uniform(-0.12, 0.12), 7), round(-66.1568 + rng.uniform(-0.16, 0.16), 7)
            ))
        cur.executemany(
            """
            INSERT OR IGNORE INTO infraestructuras (codigo, zona_id, direccion, tipo, estado, latitud, longitud)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            infra,
        )

        # Contratos
        cur.execute("SELECT id FROM clientes ORDER BY id")
        cliente_ids = [r["id"] for r in cur.fetchall()]
        cur.execute("SELECT id FROM infraestructuras ORDER BY id")
        infra_ids = [r["id"] for r in cur.fetchall()]
        contratos = []
        for i in range(1, total_contratos + 1):
            contratos.append((
                f"C-{i:06d}", cliente_ids[(i - 1) % len(cliente_ids)], infra_ids[(i - 1) % len(infra_ids)], rng.randint(1, 9),
                (datetime(2020, 1, 1) + timedelta(days=rng.randint(0, 2200))).strftime("%Y-%m-%d"), "ACTIVO"
            ))
        cur.executemany(
            """
            INSERT OR IGNORE INTO contratos (numero_contrato, cliente_id, infraestructura_id, categoria_id, fecha_inicio, estado)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            contratos,
        )

        # Medidores
        cur.execute("SELECT id FROM contratos ORDER BY id")
        contrato_ids = [r["id"] for r in cur.fetchall()]
        medidores = []
        macs = set()
        for i in range(1, total_medidores + 1):
            mac = _random_mac(rng)
            while mac in macs:
                mac = _random_mac(rng)
            macs.add(mac)
            contrato_id = contrato_ids[(i - 1) % len(contrato_ids)]
            rb = rng.randint(1, 14)
            estado = rng.choices(["ACTIVO", "FALLA", "SIN_SEÑAL"], weights=[96, 2, 2])[0]
            medidores.append((
                mac, rng.choice(MODELOS_MEDIDOR), contrato_id, rb, estado,
                (datetime(2023, 1, 1) + timedelta(days=rng.randint(0, 1000))).strftime("%Y-%m-%d"),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S") if estado == "ACTIVO" else None
            ))
        cur.executemany(
            """
            INSERT OR IGNORE INTO medidores (mac, modelo, contrato_id, radiobase_id, estado, fecha_instalacion, ultima_senal)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            medidores,
        )

        conn.commit()

        # Lecturas IoT: 100.000 eventos + 0.07% duplicados simulados.
        cur.execute("SELECT id, radiobase_id FROM medidores ORDER BY id")
        medidor_rows = cur.fetchall()
        lecturas = []
        last_reading = {m["id"]: rng.uniform(100, 4000) for m in medidor_rows}
        for i in range(total_lecturas):
            m = medidor_rows[i % len(medidor_rows)]
            medidor_id = m["id"]
            fecha = start + timedelta(hours=i % (24 * 89), minutes=rng.randint(0, 59))
            consumo = max(0.05, rng.gauss(0.65, 0.32))
            anterior = last_reading[medidor_id]
            actual = anterior + consumo
            last_reading[medidor_id] = actual
            temperatura = round(17 + 8 * rng.random() + (3 if fecha.month == 4 else 0), 2)
            fh = fecha.strftime("%Y-%m-%d %H:%M:%S")
            hash_evento = _hash_evento(medidor_id, fh, actual, m["radiobase_id"])
            lecturas.append((medidor_id, m["radiobase_id"], fh, round(anterior, 2), round(actual, 2), round(consumo, 2), temperatura, "IOT", hash_evento, (fecha + timedelta(days=rng.randint(5, 30))).strftime("%Y-%m-%d %H:%M:%S")))

        duplicados = int(total_lecturas * 0.0007)
        lecturas_con_dup = list(lecturas)
        lecturas_con_dup.extend(rng.sample(lecturas, k=max(1, duplicados)))
        rng.shuffle(lecturas_con_dup)

        before = conn.total_changes
        cur.executemany(
            """
            INSERT OR IGNORE INTO lecturas_iot (
                medidor_id, radiobase_id, fecha_hora, lectura_anterior, lectura_actual,
                consumo_m3, temperatura_c, origen, hash_evento, fecha_pago
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            lecturas_con_dup,
        )
        conn.commit()
        inserted_lecturas = conn.total_changes - before
        dup_omitidos = len(lecturas_con_dup) - inserted_lecturas

        cur.execute(
            "INSERT INTO carga_logs (proceso, total_recibidos, insertados, duplicados_omitidos, fecha) VALUES (?, ?, ?, ?, ?)",
            ("seed_lecturas_iot", len(lecturas_con_dup), inserted_lecturas, dup_omitidos, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )

        # Preavisos para una muestra de contratos
        cur.execute("SELECT id, categoria_id FROM contratos ORDER BY id LIMIT 300")
        contratos_rows = cur.fetchall()
        for c in contratos_rows:
            consumo = round(rng.uniform(8, 45), 2)
            monto = calcular_importe(consumo, c["categoria_id"])
            codigo = f"SEMAPA-{c['id']:06d}-202604"
            cur.execute(
                """
                INSERT OR IGNORE INTO preavisos (contrato_id, periodo, consumo_total_m3, monto_estimado, fecha_generacion, codigo_pago, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (c["id"], "2026-04", consumo, monto, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), codigo, "GENERADO"),
            )

        conn.commit()

        for table in ["subalcaldias", "distritos", "zonas", "categorias_tarifarias", "clientes", "infraestructuras", "contratos", "radiobases", "medidores", "lecturas_iot", "preavisos"]:
            cur.execute(f"SELECT COUNT(*) AS total FROM {table}")
            inserted[table] = cur.fetchone()["total"]
        cur.execute("SELECT duplicados_omitidos FROM carga_logs ORDER BY id DESC LIMIT 1")
        inserted["duplicados_omitidos"] = cur.fetchone()["duplicados_omitidos"]

    return {"ok": True, "db_path": str(DB_PATH), "resumen": inserted}


def database_status() -> dict[str, Any]:
    init_db()
    with get_connection() as conn:
        cur = conn.cursor()
        tables = ["subalcaldias", "distritos", "zonas", "clientes", "infraestructuras", "contratos", "radiobases", "medidores", "lecturas_iot", "preavisos", "carga_logs"]
        counts = {}
        for t in tables:
            cur.execute(f"SELECT COUNT(*) AS total FROM {t}")
            counts[t] = cur.fetchone()["total"]
        cur.execute("SELECT * FROM carga_logs ORDER BY id DESC LIMIT 3")
        logs = rows_to_dicts(cur.fetchall())
    return {"ok": True, "db_path": str(DB_PATH), "counts": counts, "logs": logs}


def get_resumen() -> dict[str, Any]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) total FROM clientes")
        clientes = cur.fetchone()["total"]
        cur.execute("SELECT COUNT(*) total FROM contratos")
        contratos = cur.fetchone()["total"]
        cur.execute("SELECT COUNT(*) total FROM infraestructuras")
        infra = cur.fetchone()["total"]
        cur.execute("SELECT COUNT(*) total FROM medidores")
        medidores = cur.fetchone()["total"]
        cur.execute("SELECT COUNT(*) total FROM medidores WHERE estado='ACTIVO'")
        activos = cur.fetchone()["total"]
        cur.execute("SELECT COALESCE(SUM(consumo_m3),0) consumo FROM lecturas_iot WHERE date(fecha_hora) = (SELECT MAX(date(fecha_hora)) FROM lecturas_iot)")
        consumo_total = round(cur.fetchone()["consumo"], 2)
        cur.execute("SELECT COALESCE(SUM(poblacion),0) poblacion FROM distritos")
        poblacion = cur.fetchone()["poblacion"] or 1
        cur.execute("SELECT COUNT(*) total FROM zonas WHERE riesgo_hidrico='CRITICO'")
        zonas_criticas = cur.fetchone()["total"]
    return {
        "poblacion": poblacion,
        "consumo_total_m3": consumo_total,
        "consumo_per_capita_L": round(consumo_total * 1000 / poblacion, 2),
        "meta_onu_L": 300,
        "medidores_activos": activos,
        "medidores_total": medidores,
        "contratos": contratos,
        "clientes": clientes,
        "infraestructuras": infra,
        "alertas_sobreconsumo": zonas_criticas,
        "zonas_estres_hidrico": zonas_criticas,
    }


def get_distritos_consumo() -> list[dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT d.nombre, ROUND(SUM(l.consumo_m3), 2) AS consumo_m3, d.poblacion
            FROM lecturas_iot l
            JOIN medidores m ON m.id = l.medidor_id
            JOIN contratos c ON c.id = m.contrato_id
            JOIN infraestructuras i ON i.id = c.infraestructura_id
            JOIN zonas z ON z.id = i.zona_id
            JOIN distritos d ON d.id = z.distrito_id
            GROUP BY d.id, d.nombre, d.poblacion
            ORDER BY consumo_m3 DESC
            """
        )
        return rows_to_dicts(cur.fetchall())


def get_consumo_diario(limit: int = 90) -> list[dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT date(fecha_hora) AS fecha,
                   CASE strftime('%m', fecha_hora)
                       WHEN '02' THEN 'Feb'
                       WHEN '03' THEN 'Mar'
                       WHEN '04' THEN 'Abr'
                       ELSE strftime('%m', fecha_hora)
                   END AS mes,
                   ROUND(SUM(consumo_m3), 2) AS consumo_m3
            FROM lecturas_iot
            GROUP BY date(fecha_hora)
            ORDER BY fecha
            LIMIT ?
            """,
            (limit,),
        )
        return rows_to_dicts(cur.fetchall())


def get_sensores() -> dict[str, Any]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) total FROM medidores")
        total = cur.fetchone()["total"]
        cur.execute("SELECT COUNT(*) activos FROM medidores WHERE estado='ACTIVO'")
        activos = cur.fetchone()["activos"]
        fallas = total - activos
        cur.execute("SELECT modelo, COUNT(*) cantidad FROM medidores GROUP BY modelo ORDER BY cantidad DESC")
        modelos = rows_to_dicts(cur.fetchall())
        cur.execute("SELECT COUNT(*) radiobases FROM radiobases")
        radiobases = cur.fetchone()["radiobases"]
    return {"total": total, "activos": activos, "fallas": fallas, "pct_fallas": round(fallas / total * 100, 2) if total else 0, "radiobases": radiobases, "modelos": modelos}


def get_clima_consumo() -> list[dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT CASE strftime('%m', fecha_hora)
                       WHEN '02' THEN 'Feb'
                       WHEN '03' THEN 'Mar'
                       WHEN '04' THEN 'Abr'
                       ELSE strftime('%m', fecha_hora)
                   END AS mes,
                   CAST(strftime('%W', fecha_hora) AS INTEGER) AS semana,
                   ROUND(AVG(temperatura_c), 2) AS temp_c,
                   ROUND(SUM(consumo_m3), 2) AS consumo_m3
            FROM lecturas_iot
            GROUP BY mes, semana
            ORDER BY MIN(fecha_hora)
            LIMIT 15
            """
        )
        return rows_to_dicts(cur.fetchall())


def buscar_medidor(query: str) -> dict[str, Any] | None:
    q = (query or "").strip().upper()
    if not q:
        return None
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT m.id AS medidor_id, m.mac AS medidor_iot, m.modelo, m.estado AS estado_medidor,
                   rb.id AS radiobase, rb.nombre AS radiobase_nombre,
                   c.id AS contrato_id, c.numero_contrato AS contrato, c.categoria_id,
                   cli.ci_nit AS ci, cli.nombres || ' ' || COALESCE(cli.apellidos,'') AS nombre,
                   cli.telefono, cli.correo, cli.direccion,
                   ct.nombre AS tarifa
            FROM medidores m
            JOIN contratos c ON c.id = m.contrato_id
            JOIN clientes cli ON cli.id = c.cliente_id
            JOIN categorias_tarifarias ct ON ct.id = c.categoria_id
            JOIN radiobases rb ON rb.id = m.radiobase_id
            WHERE UPPER(m.mac) = ? OR UPPER(c.numero_contrato) = ? OR UPPER(cli.ci_nit) = ?
            LIMIT 1
            """,
            (q, q, q),
        )
        row = row_to_dict(cur.fetchone())
        if not row:
            return None
        cur.execute(
            """
            SELECT lectura_anterior, lectura_actual, consumo_m3, fecha_hora, radiobase_id
            FROM lecturas_iot
            WHERE medidor_id = ?
            ORDER BY fecha_hora DESC
            LIMIT 1
            """,
            (row["medidor_id"],),
        )
        ultima = row_to_dict(cur.fetchone()) or {}
        row["ultima_lectura"] = ultima.get("lectura_actual", "—")
        row["lecturaAnterior"] = ultima.get("lectura_anterior", "—")
        row["LecturaActual"] = ultima.get("lectura_actual", "—")
        row["fechaHoraLectura"] = ultima.get("fecha_hora", "—")
        row["consumo_m3"] = ultima.get("consumo_m3", 0)
        row["importe"] = calcular_importe(row["consumo_m3"], row["categoria_id"])
        return row


def get_preaviso(query: str, periodo: str = "2026-04") -> dict[str, Any] | None:
    base = buscar_medidor(query)
    if not base:
        return None
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM preavisos
            WHERE contrato_id = ? AND periodo = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (base["contrato_id"], periodo),
        )
        pre = row_to_dict(cur.fetchone())
    consumo = pre["consumo_total_m3"] if pre else base["consumo_m3"]
    importe = pre["monto_estimado"] if pre else base["importe"]
    return {**base, "periodo": periodo, "consumo_m3": consumo, "importe": importe, "codigo_pago": pre["codigo_pago"] if pre else f"SEMAPA-{base['contrato']}-{periodo}"}


def registrar_lectura_manual(data: dict[str, Any]) -> dict[str, Any]:
    medidor = buscar_medidor(data.get("medidor_iot") or data.get("medidor_id") or "")
    if not medidor:
        return {"ok": False, "error": "Medidor no encontrado"}
    lectura = float(data.get("lectura") or data.get("lectura_actual") or 0)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO lecturas_manuales (medidor_id, usuario_campo, lectura_actual, fotografia_url, latitud, longitud, observacion, fecha_registro, estado_sync)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                medidor["medidor_id"],
                data.get("usuario", "campo_01"),
                lectura,
                data.get("fotografia_url"),
                data.get("latitud"),
                data.get("longitud"),
                data.get("observacion", ""),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "PENDIENTE",
            ),
        )
        conn.commit()
        ref = cur.lastrowid
    return {"ok": True, "referencia": f"LEC-{ref:08d}", "medidor": medidor["medidor_iot"], "lectura": lectura}


def get_mock_compatible_data(limit: int = 20) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Devuelve MEDIDORES y LECTURAS con la misma estructura del mock original."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT m.id, m.mac, c.numero_contrato, cli.nombres || ' ' || COALESCE(cli.apellidos,'') AS nombre,
                   cli.ci_nit, cli.direccion, rb.id AS radiobase, ct.nombre AS tarifa, c.categoria_id
            FROM medidores m
            JOIN contratos c ON c.id = m.contrato_id
            JOIN clientes cli ON cli.id = c.cliente_id
            JOIN radiobases rb ON rb.id = m.radiobase_id
            JOIN categorias_tarifarias ct ON ct.id = c.categoria_id
            ORDER BY m.id
            LIMIT ?
            """,
            (limit,),
        )
        rows = cur.fetchall()
        medidores = {}
        lecturas = []
        for r in rows:
            medidores[r["mac"]] = {
                "contrato": r["numero_contrato"],
                "nombre": r["nombre"],
                "ci": r["ci_nit"],
                "direccion": r["direccion"],
                "radiobase": r["radiobase"],
                "tarifa": r["tarifa"],
                "categoria": r["categoria_id"],
            }
            cur.execute(
                """
                SELECT lectura_anterior, lectura_actual, fecha_hora, radiobase_id, fecha_pago
                FROM lecturas_iot
                WHERE medidor_id = ?
                ORDER BY fecha_hora DESC
                LIMIT 1
                """,
                (r["id"],),
            )
            l = cur.fetchone()
            if l:
                lecturas.append({
                    "medidor_iot": r["mac"],
                    "lecturaAnterior": l["lectura_anterior"],
                    "LecturaActual": l["lectura_actual"],
                    "fechaHoraLectura": l["fecha_hora"],
                    "radiobase": l["radiobase_id"],
                    "fecha_pago": l["fecha_pago"],
                })
        return medidores, lecturas
