from flask import Blueprint, render_template, request, jsonify
import datetime
from app.db.repository import get_preaviso, get_connection
from app.mensajeria.email_service import enviar_email

mensajeria_bp = Blueprint("mensajeria", __name__)


def _mensaje_preaviso(p: dict) -> str:
    nombre_corto = (p.get("nombre") or "Cliente").split()[0]
    return (
        f"Estimado/a {nombre_corto}, SEMAPA le recuerda que su preaviso de consumo "
        f"de agua correspondiente al período {p['periodo']} es de Bs {p['importe']:.2f}, "
        f"con un consumo registrado de {p['consumo_m3']} m³."
    )


def _registrar_mensaje(contrato_id, periodo, canal, destinatario, mensaje, estado):
    """Guarda el envío en la tabla mensajes_preaviso (si existe el preaviso en la BD)."""
    try:
        ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id FROM preavisos WHERE contrato_id=? AND periodo=? ORDER BY id DESC LIMIT 1",
                (contrato_id, periodo),
            )
            row = cur.fetchone()
            if not row:
                return None
            cur.execute(
                """INSERT INTO mensajes_preaviso
                   (preaviso_id, canal, destinatario, mensaje, estado, fecha_creacion, fecha_envio)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (row["id"], canal, destinatario, mensaje, estado, ahora,
                 ahora if estado == "ENVIADO" else None),
            )
            conn.commit()
            return cur.lastrowid
    except Exception as e:
        print("No se pudo registrar el mensaje en la BD:", e)
        return None


@mensajeria_bp.route("/")
def index():
    return render_template("mensajeria/index.html")


@mensajeria_bp.route("/api/enviar", methods=["POST"])
def api_enviar():
    data = request.get_json() or {}
    periodo = data.get("periodo", "2026-04")
    canal = data.get("canal", "email")
    buscar = (data.get("contrato") or data.get("ci")
              or data.get("medidor") or data.get("medidor_iot") or "").strip()

    if not buscar:
        return jsonify({"ok": False, "error": "Indica un contrato, CI o medidor"}), 400

    # ── Datos reales desde la base de datos ─────────────────────────────
    base = get_preaviso(buscar, periodo)
    if not base:
        return jsonify({"ok": False,
                        "error": "No se encontró contrato, CI o medidor en la base de datos"}), 404

    mensaje = _mensaje_preaviso(base)
    preaviso = {
        "contrato": base.get("contrato"),
        "contrato_id": base.get("contrato_id"),
        "periodo": periodo,
        "nombre": base.get("nombre"),
        "ci": base.get("ci"),
        "consumo_m3": base.get("consumo_m3"),
        "importe": base.get("importe"),
        "codigo_pago": base.get("codigo_pago"),
        "mensaje": mensaje,
        "enviado_en": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    correo = base.get("correo")
    if not correo:
        return jsonify({"ok": False,
                        "error": f"El cliente (CI {base.get('ci')}) no tiene correo registrado"}), 404

    # ── Envío real del correo ───────────────────────────────────────────
    envio = {"modo": "no-enviado", "detalle": f"Canal '{canal}' no soportado para envío real"}
    if canal == "email":
        html = f"""
            <div style="font-family:Arial,sans-serif;max-width:600px">
              <h2 style="color:#0277bd">SEMAPA · Preaviso de consumo</h2>
              <p>{mensaje}</p>
              <table style="border-collapse:collapse;margin-top:12px">
                <tr><td><b>Contrato</b></td><td>{preaviso['contrato']}</td></tr>
                <tr><td><b>Período</b></td><td>{preaviso['periodo']}</td></tr>
                <tr><td><b>Consumo</b></td><td>{preaviso['consumo_m3']} m³</td></tr>
                <tr><td><b>Importe</b></td><td>Bs {preaviso['importe']:.2f}</td></tr>
                <tr><td><b>Código de pago</b></td><td>{preaviso['codigo_pago']}</td></tr>
              </table>
              <p style="color:#888;font-size:12px;margin-top:16px">
                Mensaje automático de la plataforma SEMAPA IoT.</p>
            </div>"""
        envio = enviar_email(
            destinatario=correo,
            asunto=f"SEMAPA · Preaviso {preaviso['periodo']} — Contrato {preaviso['contrato']}",
            html=html,
            nombre_dest=base.get("nombre") or correo,
        )

    # ── Registrar el envío en la BD (tabla mensajes_preaviso) ────────────
    estado = "ENVIADO" if (envio.get("ok") and envio.get("modo") == "real") else "ENCOLADO"
    _registrar_mensaje(preaviso["contrato_id"], periodo, canal, correo, mensaje, estado)

    return jsonify({
        "ok": envio.get("ok", True),
        "canal": canal,
        "preaviso": preaviso,
        "usuario": {"nombre": base.get("nombre"), "correo": correo, "telefono": base.get("telefono")},
        "envio": envio,
        "cola": "semapa.preavisos",
        "estado": "encolado",
    })
