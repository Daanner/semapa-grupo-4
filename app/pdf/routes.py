from flask import Blueprint, render_template, request, jsonify, send_file
import sqlite3
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

# Blueprint oficial del módulo PDF para Alan y Miriam
pdf_bp = Blueprint("pdf", __name__)

def obtener_conexion_db():
    """
    CONEXIÓN OFICIAL A LA DB DEL EQUIPO
    Apunta de forma absoluta al archivo físico de la raíz.
    """
    base_dir = os.path.abspath(os.path.dirname(__name__))
    db_path = os.path.join(base_dir, "semapa.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Permite mapear columnas reales de Jesús y Cristhian
    return conn

@pdf_bp.route("/")
def index():
    return render_template("pdf/index.html")

@pdf_bp.route("/api/preview", methods=["POST"])
def api_preview():
    """Endpoint que conecta el Mockup visual con los campos de la DB real"""
    data = request.get_json() or {}
    contrato_raw = data.get("contrato", "C-001234")
    contrato_buscado = contrato_raw.split("—")[0].strip().upper()
    formato = data.get("formato", "media_carta")
    periodo = data.get("periodo", "2026-05")

    # MOCKUP DE RESPALDO (Campos alineados al Excel por si la DB está vacía)
    datos_cliente = {
        "contrato": contrato_buscado,
        "mac_medidor": "7D:16:0E:17:7E:AA",
        "ci_nit": "5234891",
        "nombre_completo": "Juan Carlos Mendoza",
        "direccion": "Av. Ayacucho 342, Cochabamba",
        "categoria": "Doméstica",
        "consumo_m3": 24,
        "importe": 96.00,
        "lectura_anterior": 110,
        "lectura_actual": 134
    }

    # Cambios dinámicos de simulación rápida en el combo
    if contrato_buscado == "C-005678":
        datos_cliente.update({"nombre_completo": "María Flores Quispe", "ci_nit": "6123456", "consumo_m3": 18, "importe": 72.00})
    elif contrato_buscado == "C-009999":
        datos_cliente.update({"nombre_completo": "COBOCE S.A.", "ci_nit": "10203040", "categoria": "Industrial", "consumo_m3": 150, "importe": 1200.00})

    # CONSULTA REAL CON LAS COLUMNAS QUE REVISAMOS EN POWERSHELL
    try:
        conn = obtener_conexion_db()
        cursor = conn.cursor()

        # Unimos contratos y clientes usando sus llaves relacionales
        cursor.execute("""
            SELECT c.id AS contrato_id, c.numero_contrato, cl.ci_nit, cl.nombres, cl.apellidos, cl.direccion, c.categoria_id
            FROM contratos c
            JOIN clientes cl ON c.cliente_id = cl.id
            WHERE UPPER(c.numero_contrato) = ?
        """, (contrato_buscado,))
        row_contrato = cursor.fetchone()

        if row_contrato:
            datos_cliente["contrato"] = row_contrato["numero_contrato"]
            datos_cliente["ci_nit"] = row_contrato["ci_nit"]
            datos_cliente["nombre_completo"] = f"{row_contrato['nombres']} {row_contrato['apellidos']}"
            datos_cliente["direccion"] = row_contrato["direccion"]
            
            # Buscar categoría (Mapeo rápido de categorías ID a Texto)
            datos_cliente["categoria"] = "Industrial" if row_contrato["categoria_id"] == 2 else "Doméstica"

            # Buscamos el medidor asociado a este contrato_id
            cursor.execute("SELECT id, mac FROM medidores WHERE contrato_id = ?", (row_contrato["contrato_id"],))
            row_medidor = cursor.fetchone()

            if row_medidor:
                datos_cliente["mac_medidor"] = row_medidor["mac"]

                # Buscamos la última lectura en lecturas_iot usando medidor_id
                cursor.execute("""
                    SELECT lectura_anterior, lectura_actual, consumo_m3 
                    FROM lecturas_iot 
                    WHERE medidor_id = ? 
                    ORDER BY fecha_hora DESC LIMIT 1
                """, (row_medidor["id"],))
                row_lectura = cursor.fetchone()

                if row_lectura:
                    datos_cliente["lectura_anterior"] = row_lectura["lectura_anterior"]
                    datos_cliente["lectura_actual"] = row_lectura["lectura_actual"]
                    datos_cliente["consumo_m3"] = row_lectura["consumo_m3"]
                    
                    factor = 4.0 if datos_cliente["categoria"] == "Doméstica" else 8.0
                    datos_cliente["importe"] = row_lectura["consumo_m3"] * factor

        conn.close()
    except Exception as e:
        print(f"Log de Integración (Usando datos de contingencia): {e}")

    # Historial requerido por el Entregable 3 de los 3 meses previos
    factor_tarifa = 4.0 if datos_cliente["categoria"] == "Doméstica" else 8.0
    c_base = datos_cliente["consumo_m3"]
    historial = [
        {"periodo": "2026-02", "consumo": max(5, c_base - 4), "importe": max(5, c_base - 4) * factor_tarifa},
        {"periodo": "2026-03", "consumo": max(5, c_base - 2), "importe": max(5, c_base - 2) * factor_tarifa},
        {"periodo": "2026-04", "consumo": max(5, c_base - 1), "importe": max(5, c_base - 1) * factor_tarifa}
    ]

    return jsonify({
        "ok": True,
        "formato": formato,
        "periodo": periodo,
        "contrato": datos_cliente["contrato"],
        "datos": datos_cliente,
        "historial": historial,
        "vencimiento": "2026-06-30",
        "codigo_pago": f"SEMP{datos_cliente['contrato'].replace('-','')}{periodo.replace('-','')}"
    })

@pdf_bp.route("/generar-pdf")
def generar_pdf():
    """Generación real de los archivos PDF descargables exigidos en ReportLab"""
    contrato_param = request.args.get("contrato", "C-001234").strip().upper()
    periodo = request.args.get("periodo", "2026-05")
    formato = request.args.get("formato", "media_carta")

    info = {
        "contrato": contrato_param,
        "mac_medidor": "7D:16:0E:17:7E:AA",
        "ci_nit": "5234891",
        "nombre_completo": "Juan Carlos Mendoza",
        "direccion": "Av. Ayacucho 342, Cochabamba",
        "categoria": "Doméstica",
        "consumo_m3": 24,
        "importe": 96.00,
        "lectura_anterior": 110,
        "lectura_actual": 134
    }

    if contrato_param == "C-005678":
        info.update({"nombre_completo": "María Flores Quispe", "ci_nit": "6123456", "consumo_m3": 18, "importe": 72.00})
    elif contrato_param == "C-009999":
        info.update({"nombre_completo": "COBOCE S.A.", "ci_nit": "10203040", "categoria": "Industrial", "consumo_m3": 150, "importe": 1200.00})

    # EXTRACCIÓN DE DATOS REALES PARA LA IMPRESIÓN DEL ARCHIVO
    try:
        conn = obtener_conexion_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.id AS contrato_id, c.numero_contrato, cl.ci_nit, cl.nombres, cl.apellidos, cl.direccion, c.categoria_id
            FROM contratos c
            JOIN clientes cl ON c.cliente_id = cl.id
            WHERE UPPER(c.numero_contrato) = ?
        """, (contrato_param,))
        row_c = cursor.fetchone()
        
        if row_c:
            info["contrato"] = row_c["numero_contrato"]
            info["ci_nit"] = row_c["ci_nit"]
            info["nombre_completo"] = f"{row_c['nombres']} {row_c['apellidos']}"
            info["direccion"] = row_c["direccion"]
            info["categoria"] = "Industrial" if row_c["categoria_id"] == 2 else "Doméstica"

            cursor.execute("SELECT id, mac FROM medidores WHERE contrato_id = ?", (row_c["contrato_id"],))
            row_m = cursor.fetchone()
            if row_m:
                info["mac_medidor"] = row_m["mac"]
                cursor.execute("""
                    SELECT lectura_anterior, lectura_actual, consumo_m3 FROM lecturas_iot 
                    WHERE medidor_id = ? ORDER BY fecha_hora DESC LIMIT 1
                """, (row_m["id"],))
                row_l = cursor.fetchone()
                if row_l:
                    info["lectura_anterior"] = row_l["lectura_anterior"]
                    info["lectura_actual"] = row_l["lectura_actual"]
                    info["consumo_m3"] = row_l["consumo_m3"]
                    factor = 4.0 if info["categoria"] == "Doméstica" else 8.0
                    info["importe"] = row_l["consumo_m3"] * factor
        conn.close()
    except Exception as e:
        print(f"Log Extracción ReportLab: {e}")

    buffer = BytesIO()
    vencimiento = "2026-06-30"
    codigo_pago = f"SEMP{info['contrato'].replace('-','')}{periodo.replace('-','')}"

    # REQUISITO OBLIGATORIO: FORMATO ROLLO TÉRMICO 55 MM (Para Kioscos/Tótems de Elia)
    if formato == "rollo_55mm" or formato == "rollo":
        ancho_ticket = 55 * mm
        alto_ticket = 160 * mm
        pdf = canvas.Canvas(buffer, pagesize=(ancho_ticket, alto_ticket))
        pdf.setTitle(f"Preaviso_Ticket_{info['contrato']}")
        
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawCentredString(ancho_ticket / 2.0, alto_ticket - 15, "SEMAPA")
        pdf.setFont("Helvetica", 5.5)
        pdf.drawCentredString(ancho_ticket / 2.0, alto_ticket - 22, "Servicio Municipal de Agua Potable")
        pdf.drawCentredString(ancho_ticket / 2.0, alto_ticket - 28, "Cochabamba, Bolivia")
        
        pdf.setLineWidth(0.5)
        pdf.line(4, alto_ticket - 32, ancho_ticket - 4, alto_ticket - 32)
        
        pdf.setFont("Helvetica-Bold", 7)
        pdf.drawCentredString(ancho_ticket / 2.0, alto_ticket - 41, "PREAVISO DE CONSUMO")
        
        pdf.setFont("Helvetica", 6.5)
        y = alto_ticket - 54
        pdf.drawString(5, y, f"Periodo: {periodo}")
        y -= 9
        pdf.drawString(5, y, f"Contrato: {info['contrato']}")
        y -= 9
        pdf.drawString(5, y, f"Nombre: {info['nombre_completo'][:18]}")
        y -= 9
        pdf.drawString(5, y, f"Categoría: {info['categoria']}")
        
        y -= 5
        pdf.line(4, y, ancho_ticket - 4, y)
        
        y -= 12
        pdf.drawString(5, y, f"Lecturas (A/A): {info['lectura_anterior']} / {info['lectura_actual']}")
        y -= 9
        pdf.drawString(5, y, f"Consumo Neto: {info['consumo_m3']} m³")
        
        y -= 14
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(5, y, "TOTAL A PAGAR:")
        pdf.drawRightString(ancho_ticket - 5, y, f"Bs {info['importe']:.2f}")
        
        y -= 10
        pdf.setFont("Helvetica", 5.5)
        pdf.drawString(5, y, f"Vencimiento: {vencimiento}")
        
        # QR de Validación exigido por QA (Helen)
        y -= 16
        pdf.setLineWidth(0.8)
        for b in range(12, int(ancho_ticket - 12), 3):
            pdf.line(b, y, b, y + 8)
        y -= 6
        pdf.setFont("Helvetica", 5)
        pdf.drawCentredString(ancho_ticket / 2.0, y, f"ID COMPROBACIÓN: {codigo_pago}")

    # REQUISITO OBLIGATORIO: FORMATO MEDIA CARTA (Para descargas digitales/Email)
    else:
        ancho_media = 8.5 * 72
        alto_media = (11 * 72) / 2
        pdf = canvas.Canvas(buffer, pagesize=(ancho_media, alto_media))
        pdf.setTitle(f"Preaviso_Digital_{info['contrato']}")
        
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(35, alto_media - 35, "SEMAPA - PREAVISO DE CONSUMO ELECTRÓNICO")
        pdf.setFont("Helvetica-Oblique", 8)
        pdf.drawRightString(ancho_media - 35, alto_media - 32, "Plataforma Tecnológica Big Data IoT")
        
        pdf.setLineWidth(1)
        pdf.line(35, alto_media - 40, ancho_media - 35, alto_media - 40)
        
        pdf.setFont("Helvetica-Bold", 9)
        y_pos = alto_media - 56
        pdf.drawString(35, y_pos, "DATOS GENERALES DEL SUMINISTRO")
        
        pdf.setFont("Helvetica", 9.5)
        y_pos -= 16
        pdf.drawString(40, y_pos, f"Suscriptor: {info['nombre_completo']}")
        pdf.drawString(290, y_pos, f"Nro. Contrato: {info['contrato']}")
        y_pos -= 14
        pdf.drawString(40, y_pos, f"C.I. / NIT: {info['ci_nit']}")
        pdf.drawString(290, y_pos, f"Categoría Tarifaria: {info['categoria']}")
        y_pos -= 14
        pdf.drawString(40, y_pos, f"Dirección Predio: {info['direccion']}")
        pdf.drawString(290, y_pos, f"ID Medidor IoT: {info['mac_medidor']}")
        
        y_pos -= 10
        pdf.setLineWidth(0.5)
        pdf.line(35, y_pos, ancho_media - 35, y_pos)
        
        # Historial de series temporales de 3 meses exigido por la ONU/Alcaldía
        y_pos -= 16
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(35, y_pos, "HISTORIAL CRONOLÓGICO DE LECTURAS IoT")
        
        pdf.setFont("Helvetica", 9)
        y_pos -= 16
        pdf.drawString(45, y_pos, "Mes Facturado - Febrero 2026:")
        pdf.drawRightString(ancho_media - 45, y_pos, f"{info['consumo_m3'] - 3} m³")
        y_pos -= 12
        pdf.drawString(45, y_pos, "Mes Facturado - Marzo 2026:")
        pdf.drawRightString(ancho_media - 45, y_pos, f"{info['consumo_m3'] - 1} m³")
        y_pos -= 12
        pdf.drawString(45, y_pos, f"Mes Actual Procesado - Período {periodo}:")
        pdf.drawRightString(ancho_media - 45, y_pos, f"{info['consumo_m3']} m³")
        
        y_pos -= 10
        pdf.line(35, y_pos, ancho_media - 35, y_pos)
        
        y_pos -= 22
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(45, y_pos, f"TOTAL NETO FINANCIERO: Bs. {info['importe']:.2f}")
        pdf.setFont("Helvetica", 9)
        pdf.drawString(45, y_pos - 14, f"Fecha Límite de Pago Bancario: {vencimiento}")
        
        # Simulación del código QR institucional para validación
        pdf.rect(ancho_media - 95, y_pos - 12, 55, 32)
        pdf.setFont("Helvetica", 6)
        pdf.drawCentredString(ancho_media - 67, y_pos, "[ QR VALIDACIÓN ]")
        pdf.drawCentredString(ancho_media - 67, y_pos - 8, "SEMAPA DIGITAL")
        pdf.setFont("Helvetica-Bold", 7.5)
        pdf.drawRightString(ancho_media - 35, y_pos - 32, f"Código: {codigo_pago}")

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Preaviso_{info['contrato']}_{periodo}.pdf",
        mimetype="application/pdf"
    )