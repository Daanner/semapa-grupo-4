import os
import sqlite3
from pathlib import Path
from flask import Blueprint, render_template, request, jsonify
import datetime, random, string
from app.mock_data import MEDIDORES, LECTURAS, get_consumo, calcular_importe

lector_bp = Blueprint("lector", __name__)

lecturas_registradas = []

def get_db_connection():
    BASE_DIR = Path(__file__).resolve().parents[2]
    DB_PATH = Path(os.getenv("SEMAPA_DB_PATH", BASE_DIR / "semapa.db"))
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # para acceder por nombre de columna
    return conn


@lector_bp.route("/")
def index():
    return render_template("lector/index.html")

@lector_bp.route("/api/buscar-medidor", methods=["POST"])
#def api_buscar_medidor():
#    data = request.get_json()
#    mac = data.get("medidor_id", "").strip().upper()
#    info = MEDIDORES.get(mac)
#    if not info:
#        return jsonify({"ok": False, "error": "Medidor no encontrado. Verifique la MAC address."}), 404
#    # última lectura del mock
#    lects = [l for l in LECTURAS if l["medidor_iot"] == mac]
#    ultima = lects[-1] if lects else {}
#    return jsonify({
#        "ok": True,
#        "medidor": mac,
#        "info": {
#            **info,
#            "ultima_lectura": ultima.get("LecturaActual", "—"),
#            "lecturaAnterior": ultima.get("lecturaAnterior", "—"),
#            "fecha_ultima": ultima.get("fechaHoraLectura", "—"),
#            "radiobase": ultima.get("radiobase", info["radiobase"]),
#        }
#    })
def api_buscar_medidor():
    data = request.get_json()
    mac = data.get("medidor_id", "").strip().upper()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Obtener datos del medidor y toda la información relacionada
        cursor.execute("""
            SELECT 
                m.mac,
                m.modelo,
                m.estado AS medidor_estado,
                m.fecha_instalacion,
                c.id AS contrato_id,
                c.numero_contrato,
                c.estado AS contrato_estado,
                cat.nombre AS categoria_tarifaria,
                cat.tarifa_base,
                cli.ci_nit,
                cli.nombres,
                cli.apellidos,
                cli.telefono,
                cli.correo,
                infra.direccion,
                infra.tipo AS infraestructura_tipo,
                z.nombre AS zona_nombre,
                z.codigo AS zona_codigo,
                d.nombre AS distrito_nombre,
                s.nombre AS subalcaldia_nombre
            FROM medidores m
            JOIN contratos c ON m.contrato_id = c.id
            JOIN categorias_tarifarias cat ON c.categoria_id = cat.id
            JOIN clientes cli ON c.cliente_id = cli.id
            JOIN infraestructuras infra ON c.infraestructura_id = infra.id
            JOIN zonas z ON infra.zona_id = z.id
            JOIN distritos d ON z.distrito_id = d.id
            JOIN subalcaldias s ON d.subalcaldia_id = s.id
            WHERE m.mac = ?
        """, (mac,))
        
        medidor_row = cursor.fetchone()
        if not medidor_row:
            conn.close()
            return jsonify({"ok": False, "error": "Medidor no encontrado. Verifique la MAC address."}), 404
        
        # 2. Obtener la última lectura IoT (con nombre de radiobase)
        cursor.execute("""
            SELECT 
                li.lectura_actual,
                li.lectura_anterior,
                li.fecha_hora,
                li.consumo_m3,
                rb.nombre AS radiobase_nombre
            FROM lecturas_iot li
            JOIN radiobases rb ON li.radiobase_id = rb.id
            WHERE li.medidor_id = (SELECT id FROM medidores WHERE mac = ?)
            ORDER BY li.fecha_hora DESC
            LIMIT 1
        """, (mac,))
        
        ultima = cursor.fetchone()
        conn.close()
        
    except Exception as e:
        return jsonify({"ok": False, "error": f"Error interno: {str(e)}"}), 500
    
    # Construir la respuesta en el formato esperado
    info = {
        "mac": medidor_row["mac"],
        "modelo": medidor_row["modelo"],
        "estado": medidor_row["medidor_estado"],
        "nombre": f"{medidor_row['nombres']} {medidor_row['apellidos'] or ''}".strip(),
        "ci_nit": medidor_row["ci_nit"],
        "telefono": medidor_row["telefono"],
        "correo": medidor_row["correo"],
        "direccion": medidor_row["direccion"],
        "zona": medidor_row["zona_nombre"],
        "distrito": medidor_row["distrito_nombre"],
        "subalcaldia": medidor_row["subalcaldia_nombre"],
        "categoria": medidor_row["categoria_tarifaria"],
        "contrato": medidor_row["numero_contrato"],
        "radiobase": ultima["radiobase_nombre"] if ultima else "No asignada"
    }
    
    if ultima:
        info["ultima_lectura"] = ultima["lectura_actual"]
        info["lecturaAnterior"] = ultima["lectura_anterior"]
        info["fecha_ultima"] = ultima["fecha_hora"]
        info["consumo_m3"] = ultima["consumo_m3"]
    else:
        info["ultima_lectura"] = "—"
        info["lecturaAnterior"] = "—"
        info["fecha_ultima"] = "—"
    
    return jsonify({
        "ok": True,
        "medidor": mac,
        "info": info
    })

@lector_bp.route("/api/registrar-lectura", methods=["POST"])
#def api_registrar_lectura():
#    data = request.get_json()
#    medidor_id  = data.get("medidor_id", "").strip().upper()
#    lectura     = data.get("lectura")
#    observacion = data.get("observacion", "")
#    usuario     = data.get("usuario", "campo_01")
#
#    if not medidor_id or lectura is None:
#        return jsonify({"ok": False, "error": "Datos incompletos"}), 400
#
#    # Tolerancia a filas incompletas como el CSV
#    if not MEDIDORES.get(medidor_id):
#        return jsonify({"ok": False, "error": "MAC no registrada en el sistema"}), 404
#
#    ref = "LEC-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
#    registro = {
#        "referencia":       ref,
#        "medidor_iot":      medidor_id,         # nombre exacto del CSV
#        "lecturaAnterior":  data.get("lectura_anterior", 0),
#        "LecturaActual":    float(lectura),
#        "fechaHoraLectura": datetime.datetime.now().strftime("%m/%d/%y %H:%M"),
#        "radiobase":        MEDIDORES[medidor_id]["radiobase"],
#        "observacion":      observacion,
#        "usuario":          usuario,
#        "estado":           "pendiente_sync",
#    }
#    lecturas_registradas.append(registro)
#    return jsonify({"ok": True, "referencia": ref, "registro": registro})
def api_registrar_lectura():
    data = request.get_json()
    medidor_id = data.get("medidor_id", "").strip().upper()
    lectura = data.get("lectura")
    observacion = data.get("observacion", "")
    # Las coordenadas vienen del dispositivo (frontend)
    latitud = data.get("latitud")
    longitud = data.get("longitud")
    
    # Validaciones básicas
    if not medidor_id or lectura is None:
        return jsonify({"ok": False, "error": "Datos incompletos: se requiere medidor_id y lectura"}), 400
    
    try:
        lectura_float = float(lectura)
    except ValueError:
        return jsonify({"ok": False, "error": "La lectura debe ser un número válido"}), 400
    
    # Conectar a la BD
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Verificar que el medidor existe y obtener su ID, además del correo del cliente asociado
        cursor.execute("""
            SELECT 
                m.id AS medidor_id,
                cli.correo AS cliente_correo
            FROM medidores m
            JOIN contratos ct ON m.contrato_id = ct.id
            JOIN clientes cli ON ct.cliente_id = cli.id
            WHERE m.mac = ?
        """, (medidor_id,))
        
        medidor = cursor.fetchone()
        if not medidor:
            conn.close()
            return jsonify({"ok": False, "error": "MAC no registrada en el sistema"}), 404
        
        # Usamos el correo del cliente como usuario_campo (según requerimiento)
        usuario_campo = medidor["cliente_correo"]
        medidor_db_id = medidor["medidor_id"]
        
        # 2. Insertar la lectura manual
        fecha_registro = datetime.datetime.now().isoformat()
        # Generamos una referencia única (por ejemplo, un hash corto)
        import hashlib
        ref_raw = f"{medidor_id}{lectura}{fecha_registro}{usuario_campo}"
        referencia = hashlib.md5(ref_raw.encode()).hexdigest()[:8].upper()
        
        cursor.execute("""
            INSERT INTO lecturas_manuales (
                medidor_id,
                usuario_campo,
                lectura_actual,
                latitud,
                longitud,
                observacion,
                fecha_registro,
                estado_sync
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            medidor_db_id,
            usuario_campo,
            lectura_float,
            latitud,
            longitud,
            observacion,
            fecha_registro,
            'PENDIENTE'
        ))
        
        conn.commit()
        nuevo_id = cursor.lastrowid
        
        # Construir respuesta similar al mock original
        registro = {
            "referencia": referencia,
            "medidor_iot": medidor_id,
            "lecturaAnterior": data.get("lectura_anterior", 0),  # si se envía, de lo contrario 0
            "LecturaActual": lectura_float,
            "fechaHoraLectura": datetime.datetime.now().strftime("%m/%d/%y %H:%M"),
            "observacion": observacion,
            "usuario": usuario_campo,
            "estado": "pendiente_sync",
            "latitud": latitud,
            "longitud": longitud
        }
        lecturas_registradas.append(registro)
        
        conn.close()
        return jsonify({"ok": True, "referencia": referencia, "registro": registro})
        
    except sqlite3.Error as e:
        conn.close()
        return jsonify({"ok": False, "error": f"Error de base de datos: {str(e)}"}), 500
    except Exception as e:
        conn.close()
        return jsonify({"ok": False, "error": f"Error interno: {str(e)}"}), 500

@lector_bp.route("/api/lecturas-pendientes")
def api_lecturas_pendientes():
    return jsonify({"ok": True, "total": len(lecturas_registradas), "lecturas": lecturas_registradas[-10:]})

@lector_bp.route("/movil")
def movil():
    """Vista móvil standalone — sin layout, PWA-ready"""
    return render_template("mobile/lector_movil.html")
