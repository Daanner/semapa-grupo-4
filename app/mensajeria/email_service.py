"""
Servicio de envío de correo para mensajería.

Usa Gmail SMTP con smtplib (incluido en Python, sin dependencias ni servicios
externos ni pagos). Envía a CUALQUIER dirección de correo, gratis.

Requisito (1 sola vez): una "contraseña de aplicación" de Google.
  1. Activa la verificación en 2 pasos en tu cuenta Google.
  2. Genera una App Password en https://myaccount.google.com/apppasswords
  3. Pégala en .env como SMTP_PASSWORD (16 caracteres, sin espacios).

Si no hay SMTP_USER/SMTP_PASSWORD, funciona en modo "dry-run":
escribe el correo en consola en lugar de enviarlo (para no romper la demo).
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from flask import current_app


def enviar_email(destinatario: str, asunto: str, html: str, nombre_dest: str = "") -> dict:
    """
    Envía un correo. Devuelve un dict con el resultado:
      {"ok": bool, "modo": "real"|"simulado", "destino": str, "detalle": str}
    """
    host      = current_app.config.get("SMTP_HOST", "smtp.gmail.com")
    port      = current_app.config.get("SMTP_PORT", 587)
    user      = current_app.config.get("SMTP_USER", "")
    password  = current_app.config.get("SMTP_PASSWORD", "")
    from_name = current_app.config.get("MAIL_FROM_NAME", "SEMAPA")

    destino = destinatario

    # Sin credenciales → modo simulado (no rompe nada, útil para desarrollo)
    if not user or not password:
        print("\n" + "=" * 60)
        print("[EMAIL SIMULADO - sin SMTP_USER/SMTP_PASSWORD]")
        print(f"   Para:    {destino}")
        print(f"   Asunto:  {asunto}")
        print(f"   Cuerpo:  {html[:200]}...")
        print("=" * 60 + "\n")
        return {"ok": True, "modo": "simulado", "destino": destino,
                "detalle": "Sin credenciales SMTP: correo escrito en consola, no enviado."}

    # Construir el mensaje (HTML)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"] = formataddr((from_name, user))
    msg["To"] = formataddr((nombre_dest or destino, destino))
    msg.attach(MIMEText(html, "html", "utf-8"))

    # Envío real por SMTP (STARTTLS)
    try:
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(user, [destino], msg.as_string())
        return {"ok": True, "modo": "real", "destino": destino,
                "detalle": f"Enviado por SMTP ({host}) a {destino}"}
    except Exception as e:
        return {"ok": False, "modo": "real", "destino": destino,
                "detalle": f"Error al enviar por SMTP: {e}"}
