from flask import Blueprint, render_template, request, jsonify
from app.mock_data import MEDIDORES, LECTURAS, get_consumo, calcular_importe

totem_bp = Blueprint("totem", __name__)

@totem_bp.route("/")
def index():
    return render_template("totem/index.html")

@totem_bp.route("/standalone")
def standalone():
    """Vista independiente sin layout para kiosco físico"""
    return render_template("totem_standalone/kiosko.html")

@totem_bp.route("/api/consultar", methods=["POST"])
def api_consultar():
    data   = request.get_json()
    buscar = (data.get("ci") or data.get("medidor_iot") or data.get("contrato", "")).strip().upper()

    mac = None
    for m, info in MEDIDORES.items():
        if (info["ci"].upper() == buscar or
            info["contrato"].upper() == buscar or
            m == buscar):
            mac = m; break

    if not mac:
        return jsonify({"ok": False, "error": "No se encontró el registro"}), 404

    info  = MEDIDORES[mac]
    lects = [l for l in LECTURAS if l["medidor_iot"] == mac]
    ultima = lects[-1] if lects else {}
    consumo = get_consumo(ultima)
    importe = calcular_importe(consumo, info["categoria"])

    return jsonify({"ok": True, "datos": {
        "nombre":     info["nombre"],
        "contrato":   info["contrato"],
        "medidor_iot": mac,
        "radiobase":  info["radiobase"],
        "tarifa":     info["tarifa"],
        "consumo_m3": consumo,
        "lecturaAnterior": ultima.get("lecturaAnterior", "—"),
        "LecturaActual":   ultima.get("LecturaActual", "—"),
        "fechaHoraLectura": ultima.get("fechaHoraLectura", "—"),
        "deuda_total": importe,
        "cuotas": [
            {"periodo": "2026-03", "importe": round(importe * 0.95, 2), "estado": "vencida"},
            {"periodo": "2026-04", "importe": round(importe, 2),        "estado": "vencida"},
            {"periodo": "2026-05", "importe": round(importe * 1.07, 2), "estado": "pendiente"},
        ] if importe > 0 else [],
    }})
