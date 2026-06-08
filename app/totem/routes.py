from flask import Blueprint, render_template, request, jsonify
from app import db  

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
    data   = request.get_json() or {}
    # Capturamos el dato del teclado táctil (CI, Contrato o dirección MAC)

    buscar = str(data.get("ci") or data.get("medidor_iot") or data.get("contrato") or data.get("id_medidor") or "").strip()
    if not buscar:
        return jsonify({"ok": False, "error": "Debe ingresar un criterio de búsqueda"}), 400
    id_medidor_num = None
    if buscar.isdigit():
        id_medidor_num = int(buscar)

    buscar_upper = buscar.upper()
    try:
        # 1. CONSULTA PRINCIPAL: Cruzamos los datos del cliente, su contrato activo y su medidor
        query_cliente = """
            SELECT 
                c.nombres || ' ' || COALESCE(c.apellidos, '') AS nombre_completo,
                con.numero_contrato,
                m.id AS medidor_id,
                m.mac AS mac_medidor,
                r.nombre AS nombre_radiobase,
                cat.nombre AS categoria_tarifa,
                cat.tarifa_base
            FROM clientes c
            JOIN contratos con ON c.id = con.cliente_id
            JOIN medidores m ON con.id = m.contrato_id
            JOIN radiobases r ON m.radiobase_id = r.id
            JOIN categorias_tarifarias cat ON con.categoria_id = cat.id
            WHERE UPPER(c.ci_nit) = :buscar 
               OR UPPER(con.numero_contrato) = :buscar 
               OR UPPER(m.mac) = :buscar
               OR (:id_medidor_num IS NOT NULL AND m.id = :id_medidor_num)
            LIMIT 1
        """
        
       
        resultado = db.session.execute(db.text(query_cliente), {"buscar": buscar_upper, "id_medidor_num":id_medidor_num}).fetchone()

        # Si PostgreSQL no devuelve ninguna fila
        if not resultado:
            return jsonify({"ok": False, "error": "No se encontró ningún registro asociado en SEMAPA"}), 404

        # Desempaquetamos la fila obtenida
        nombre_completo, contrato, medidor_id, mac_medidor, radiobase, tarifa, tarifa_base = resultado

        # 2. CONSULTA DE TELEMETRÍA: Traemos la última lectura enviada por el medidor inteligente
        query_lectura = """
            SELECT lectura_anterior, lectura_actual, consumo_m3, fecha_hora
            FROM lecturas_iot
            WHERE medidor_id = :medidor_id
            ORDER BY fecha_hora DESC
            LIMIT 1
        """
       
        lectura_res = db.session.execute(db.text(query_lectura), {"medidor_id": medidor_id}).fetchone()

        # Validamos si existen lecturas registradas para este dispositivo
        if lectura_res:
            lect_ant, lect_act, consumo, fecha_hora = lectura_res
            fecha_str = fecha_hora.strftime('%Y-%m-%d %H:%M')
        else:
            lect_ant, lect_act, consumo, fecha_str = 0.0, 0.0, 0.0, "Sin lecturas recientes"

        # 3. LÓGICA DE NEGOCIO (Cálculo del importe de la factura)
        # Convertimos tipos de datos numéricos de la BD a float para realizar la operación matemática
        costo_por_m3 = 2.50  # Costo por metro cúbico excedente o consumido
        importe = float(tarifa_base) + (float(consumo) * costo_por_m3)

        # Retornamos la respuesta con la estructura JSON 
        return jsonify({
            "ok": True,  
            "datos": {
                "nombre": nombre_completo,
                "contrato": contrato,
                "medidor_id": int(medidor_id),
                "medidor_iot": mac_medidor,
                "radiobase": radiobase,
                "tarifa": tarifa,
                "consumo_m3": float(consumo),
                "lecturaAnterior": float(lect_ant),
                "LecturaActual": float(lect_act),
                "fechaHoraLectura": fecha_str,
                "deuda_total": round(importe, 2),
                "cuotas": [
                    {"periodo": "2026-04", "importe": round(importe * 0.95, 2), "estado": "vencida"},
                    {"periodo": "2026-05", "importe": round(importe, 2),        "estado": "vencida"},
                    {"periodo": "2026-06", "importe": round(importe * 1.07, 2), "estado": "pendiente"},
                ] if importe > 0 else []
            }
        })

    except Exception as e:
        # Captura errores de sintaxis SQL o problemas imprevistos en la conexión
        return jsonify({"ok": False, "error": f"Error interno en la base de datos: {str(e)}"}), 500
    
@totem_bp.route("/api/historial/<string:medidor_id>", methods=["GET"])
def api_historial(medidor_id):
    try:
        parametro = str(medidor_id).strip()
        
        id_numerico = None
        if parametro.isdigit():
            id_numerico = int(parametro)
        else:
            query_buscar_id = "SELECT id FROM medidores WHERE UPPER(mac) = :mac LIMIT 1"
            res_id = db.session.execute(db.text(query_buscar_id), {"mac": parametro.upper()}).fetchone()
            if res_id:
                id_numerico = res_id[0]

        if id_numerico is None:
            return jsonify({
                "ok": True,
                "medidor_id": medidor_id,
                "historial": [],
                "msg": "No se encontraron medidores asociados al identificador proporcionado"
            })

        query_historial = """
            SELECT 
                fecha_hora,
                lectura_anterior,
                lectura_actual,
                consumo_m3,
                hash_evento
            FROM lecturas_iot
            WHERE medidor_id = :id_numerico
            ORDER BY fecha_hora DESC
        """
        
        resultados = db.session.execute(db.text(query_historial), {"id_numerico": id_numerico}).fetchall()
        
        historial = []
        for fila in resultados:
            historial.append({
                "fecha_hora": fila.fecha_hora.strftime('%Y-%m-%d %H:%M'),
                "lectura_anterior": float(fila.lectura_anterior),
                "lectura_actual": float(fila.lectura_actual),
                "consumo_m3": float(fila.consumo_m3),
                "hash": fila.hash_evento if fila.hash_evento is not None else 'N/A'
            })
            
        return jsonify({
            "ok": True,
            "medidor_id": medidor_id,
            "historial": historial
        })

    except Exception as e:
        print(f"🚨 ERROR EN API_HISTORIAL: {str(e)}")
        return jsonify({"ok": False, "error": f"Error al obtener el historial: {str(e)}"}), 500