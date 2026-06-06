from flask import Blueprint, jsonify, request

from app.db.repository import (
    database_status,
    get_clima_consumo,
    get_consumo_diario,
    get_distritos_consumo,
    get_preaviso,
    get_resumen,
    get_sensores,
    init_db,
    registrar_lectura_manual,
    seed_db,
)


db_bp = Blueprint("db", __name__)


@db_bp.route("/")
def index():
    return jsonify({
        "modulo": "DBB/DBA SEMAPA Grupo 4",
        "descripcion": "Base de datos real para reemplazar el mockup visual del sistema.",
        "endpoints": [
            "/db/status",
            "/db/seed",
            "/db/reset-seed",
            "/db/api/resumen",
            "/db/api/distritos",
            "/db/api/consumo-diario",
            "/db/api/sensores",
            "/db/api/clima",
            "/db/api/preaviso?buscar=C-000001&periodo=2026-04",
        ],
    })


@db_bp.route("/status")
def status():
    init_db()
    return jsonify(database_status())


@db_bp.route("/seed")
def seed():
    return jsonify(seed_db(force=False))


@db_bp.route("/reset-seed")
def reset_seed():
    lecturas = int(request.args.get("lecturas", 100000))
    medidores = int(request.args.get("medidores", 1200))
    contratos = int(request.args.get("contratos", 1000))
    infra = int(request.args.get("infra", 1000))
    return jsonify(seed_db(force=True, total_infraestructuras=infra, total_contratos=contratos, total_medidores=medidores, total_lecturas=lecturas))


@db_bp.route("/api/resumen")
def api_resumen():
    return jsonify(get_resumen())


@db_bp.route("/api/distritos")
def api_distritos():
    return jsonify(get_distritos_consumo())


@db_bp.route("/api/consumo-diario")
def api_consumo_diario():
    return jsonify(get_consumo_diario())


@db_bp.route("/api/sensores")
def api_sensores():
    return jsonify(get_sensores())


@db_bp.route("/api/clima")
def api_clima():
    return jsonify(get_clima_consumo())


@db_bp.route("/api/preaviso")
def api_preaviso():
    buscar = request.args.get("buscar") or request.args.get("contrato") or request.args.get("ci") or request.args.get("medidor") or ""
    periodo = request.args.get("periodo", "2026-04")
    data = get_preaviso(buscar, periodo)
    if not data:
        return jsonify({"ok": False, "error": "No se encontró contrato, CI o medidor"}), 404
    return jsonify({"ok": True, "preaviso": data})


@db_bp.route("/api/registrar-lectura", methods=["POST"])
def api_registrar_lectura():
    return jsonify(registrar_lectura_manual(request.get_json() or {}))
