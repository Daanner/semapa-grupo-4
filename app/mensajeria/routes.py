from flask import Blueprint, render_template, request, jsonify
import datetime, random
from app.mock_data import MEDIDORES, LECTURAS, get_consumo, calcular_importe, TARIFAS

mensajeria_bp = Blueprint("mensajeria", __name__)

def _build_preaviso(mac, periodo):
    info = MEDIDORES.get(mac)
    if not info:
        return None
    lects = [l for l in LECTURAS if l["medidor_iot"] == mac]
    ultima = lects[-1] if lects else {}
    consumo = get_consumo(ultima) if ultima else 18
    importe = calcular_importe(consumo, info["categoria"])
    nombre_corto = info["nombre"].split()[0]
    return {
        "contrato":   info["contrato"],
        "medidor_iot": mac,
        "periodo":    periodo,
        "nombre":     info["nombre"],
        "ci":         info["ci"],
        "radiobase":  info["radiobase"],
        "consumo_m3": consumo,
        "tarifa":     info["tarifa"],
        "importe":    importe,
        "mensaje": (
            f"Estimado/a {nombre_corto}, SEMAPA le recuerda que su preaviso de consumo "
            f"de agua correspondiente al período {periodo} es de Bs {importe:.2f}, "
            f"con un consumo registrado de {consumo} m³."
        ),
        "enviado_en": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

@mensajeria_bp.route("/")
def index():
    return render_template("mensajeria/index.html")

@mensajeria_bp.route("/api/enviar", methods=["POST"])
def api_enviar():
    data = request.get_json()
    periodo = data.get("periodo", "2026-05")
    canal   = data.get("canal", "email")
    # buscar por MAC, CI o contrato
    mac = data.get("medidor_iot") or data.get("medidor") or ""
    mac = mac.strip().upper()
    if not mac:
        ci_o_contrato = data.get("contrato") or data.get("ci", "")
        for m, info in MEDIDORES.items():
            if info["ci"] == ci_o_contrato or info["contrato"] == ci_o_contrato:
                mac = m; break
    preaviso = _build_preaviso(mac, periodo)
    if not preaviso:
        return jsonify({"ok": False, "error": "Medidor / contrato no encontrado"}), 404
    return jsonify({"ok": True, "canal": canal, "preaviso": preaviso,
                    "cola": "semapa.preavisos", "estado": "encolado"})

@mensajeria_bp.route("/api/estado-cola")
def api_estado_cola():
    return jsonify({
        "cola": "semapa.preavisos", "broker": "RabbitMQ", "estado": "activo",
        "enviados_hoy": random.randint(800, 1200),
        "mensajes_pendientes": random.randint(0, 12),
        "errores": random.randint(0, 3),
    })
