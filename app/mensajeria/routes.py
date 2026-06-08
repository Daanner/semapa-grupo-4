from flask import Blueprint, render_template, request, jsonify
import datetime, random
from app.mock_data import (
    MEDIDORES, LECTURAS, get_consumo, calcular_importe, TARIFAS,
    get_usuario_by_ci,
)
from app.mensajeria.email_service import enviar_email

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

    # ── Buscar al usuario por CI y enviar la notificación real ──────────
    usuario = get_usuario_by_ci(preaviso["ci"])
    if not usuario:
        return jsonify({"ok": False,
                        "error": f"No hay datos de contacto para el CI {preaviso['ci']}"}), 404

    envio = {"modo": "no-enviado", "detalle": f"Canal '{canal}' no soportado para envío real"}
    if canal == "email":
        html = f"""
            <div style="font-family:Arial,sans-serif;max-width:600px">
              <h2 style="color:#0277bd">SEMAPA · Preaviso de consumo</h2>
              <p>{preaviso['mensaje']}</p>
              <table style="border-collapse:collapse;margin-top:12px">
                <tr><td><b>Contrato</b></td><td>{preaviso['contrato']}</td></tr>
                <tr><td><b>Período</b></td><td>{preaviso['periodo']}</td></tr>
                <tr><td><b>Consumo</b></td><td>{preaviso['consumo_m3']} m³</td></tr>
                <tr><td><b>Importe</b></td><td>Bs {preaviso['importe']:.2f}</td></tr>
              </table>
              <p style="color:#888;font-size:12px;margin-top:16px">
                Mensaje automático de la plataforma SEMAPA IoT.</p>
            </div>"""
        envio = enviar_email(
            destinatario=usuario["email"],
            asunto=f"SEMAPA · Preaviso {preaviso['periodo']} — Contrato {preaviso['contrato']}",
            html=html,
            nombre_dest=usuario["nombre"],
        )

    return jsonify({"ok": envio.get("ok", True), "canal": canal, "preaviso": preaviso,
                    "usuario": usuario, "envio": envio,
                    "cola": "semapa.preavisos", "estado": "encolado"})

@mensajeria_bp.route("/api/estado-cola")
def api_estado_cola():
    return jsonify({
        "cola": "semapa.preavisos", "broker": "RabbitMQ", "estado": "activo",
        "enviados_hoy": random.randint(800, 1200),
        "mensajes_pendientes": random.randint(0, 12),
        "errores": random.randint(0, 3),
    })
