from flask import Blueprint, render_template, request, jsonify
import datetime, random, string
from app.mock_data import MEDIDORES, LECTURAS, get_consumo, calcular_importe

lector_bp = Blueprint("lector", __name__)

lecturas_registradas = []

@lector_bp.route("/")
def index():
    return render_template("lector/index.html")

@lector_bp.route("/api/buscar-medidor", methods=["POST"])
def api_buscar_medidor():
    data = request.get_json()
    mac = data.get("medidor_id", "").strip().upper()
    info = MEDIDORES.get(mac)
    if not info:
        return jsonify({"ok": False, "error": "Medidor no encontrado. Verifique la MAC address."}), 404
    # última lectura del mock
    lects = [l for l in LECTURAS if l["medidor_iot"] == mac]
    ultima = lects[-1] if lects else {}
    return jsonify({
        "ok": True,
        "medidor": mac,
        "info": {
            **info,
            "ultima_lectura": ultima.get("LecturaActual", "—"),
            "lecturaAnterior": ultima.get("lecturaAnterior", "—"),
            "fecha_ultima": ultima.get("fechaHoraLectura", "—"),
            "radiobase": ultima.get("radiobase", info["radiobase"]),
        }
    })

@lector_bp.route("/api/registrar-lectura", methods=["POST"])
def api_registrar_lectura():
    data = request.get_json()
    medidor_id  = data.get("medidor_id", "").strip().upper()
    lectura     = data.get("lectura")
    observacion = data.get("observacion", "")
    usuario     = data.get("usuario", "campo_01")

    if not medidor_id or lectura is None:
        return jsonify({"ok": False, "error": "Datos incompletos"}), 400

    # Tolerancia a filas incompletas como el CSV
    if not MEDIDORES.get(medidor_id):
        return jsonify({"ok": False, "error": "MAC no registrada en el sistema"}), 404

    ref = "LEC-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    registro = {
        "referencia":       ref,
        "medidor_iot":      medidor_id,         # nombre exacto del CSV
        "lecturaAnterior":  data.get("lectura_anterior", 0),
        "LecturaActual":    float(lectura),
        "fechaHoraLectura": datetime.datetime.now().strftime("%m/%d/%y %H:%M"),
        "radiobase":        MEDIDORES[medidor_id]["radiobase"],
        "observacion":      observacion,
        "usuario":          usuario,
        "estado":           "pendiente_sync",
    }
    lecturas_registradas.append(registro)
    return jsonify({"ok": True, "referencia": ref, "registro": registro})

@lector_bp.route("/api/lecturas-pendientes")
def api_lecturas_pendientes():
    return jsonify({"ok": True, "total": len(lecturas_registradas), "lecturas": lecturas_registradas[-10:]})

@lector_bp.route("/movil")
def movil():
    """Vista móvil standalone — sin layout, PWA-ready"""
    return render_template("mobile/lector_movil.html")
