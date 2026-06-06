from flask import Blueprint, render_template, request, jsonify
from app.mock_data import MEDIDORES, LECTURAS, get_consumo, calcular_importe

pdf_bp = Blueprint("pdf", __name__)

@pdf_bp.route("/")
def index():
    return render_template("pdf/index.html")

@pdf_bp.route("/api/preview", methods=["POST"])
def api_preview():
    data       = request.get_json()
    mac        = (data.get("medidor_iot") or data.get("contrato", "7D:16:0E:17:7E:AA")).strip().upper()
    formato    = data.get("formato", "media_carta")
    periodo    = data.get("periodo", "2026-05")

    # buscar por contrato también
    if not mac.count(":") == 5:
        for m, info in MEDIDORES.items():
            if info["contrato"] == mac or info["ci"] == mac:
                mac = m; break

    info = MEDIDORES.get(mac)
    if not info:
        return jsonify({"ok": False, "error": "Medidor no encontrado"}), 404

    lects  = [l for l in LECTURAS if l["medidor_iot"] == mac]
    ultima = lects[-1] if lects else {}
    consumo = get_consumo(ultima)
    importe = calcular_importe(consumo, info["categoria"])

    historial = [
        {"periodo": "2026-02", "lecturaAnterior": ultima.get("lecturaAnterior",0)-60, "LecturaActual": ultima.get("lecturaAnterior",0), "consumo": consumo-3, "importe": calcular_importe(consumo-3, info["categoria"])},
        {"periodo": "2026-03", "lecturaAnterior": ultima.get("lecturaAnterior",0)-30, "LecturaActual": ultima.get("lecturaAnterior",0)+consumo-3, "consumo": consumo-1, "importe": calcular_importe(consumo-1, info["categoria"])},
        {"periodo": "2026-04", "lecturaAnterior": ultima.get("lecturaAnterior",0),    "LecturaActual": ultima.get("LecturaActual",0),  "consumo": consumo,   "importe": importe},
    ]

    return jsonify({
        "ok": True, "formato": formato, "periodo": periodo,
        "datos": {**info, "medidor_iot": mac, "consumo_m3": consumo, "importe": importe,
                  "lecturaAnterior": ultima.get("lecturaAnterior","—"),
                  "LecturaActual":   ultima.get("LecturaActual","—"),
                  "fechaHoraLectura": ultima.get("fechaHoraLectura","—"),
                  "radiobase": ultima.get("radiobase", info["radiobase"])},
        "historial": historial,
        "vencimiento": "2026-06-30",
        "codigo_pago": f"SEMP{info['contrato'].replace('-','')}{periodo.replace('-','')}",
        "qr_url": f"/pdf/api/qr/{mac}/{periodo}",
    })

@pdf_bp.route("/api/qr/<path:mac>/<periodo>")
def api_qr(mac, periodo):
    return jsonify({"medidor_iot": mac, "periodo": periodo,
                    "url_validacion": f"https://semapa.gob.bo/validar/{mac}/{periodo}"})
