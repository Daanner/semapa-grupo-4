from flask import Blueprint, render_template, jsonify
import random, math

dashboard_bp = Blueprint("dashboard", __name__)

# ── Datos mock para el demo (sin BD) ──────────────────────
def _mock_distritos():
    distritos = [
        ("Distrito 1 – Cercado Norte", 18.4),
        ("Distrito 2 – Cercado Sur",   22.1),
        ("Distrito 3 – Sacaba",        31.7),
        ("Distrito 4 – Quillacollo",   28.3),
        ("Distrito 5 – Colcapirhua",   19.8),
        ("Distrito 6 – Tiquipaya",     24.5),
        ("Distrito 7 – Vinto",         35.2),
        ("Distrito 8 – Sipe Sipe",     41.0),
        ("Distrito 9 – Punata",        38.6),
        ("Distrito 10 – Cliza",        29.4),
        ("Distrito 11 – Tarata",       44.2),
        ("Distrito 12 – Arani",        50.1),
        ("Distrito 13 – Arbieto",      33.7),
        ("Distrito 14 – Tolata",       47.8),
    ]
    return [{"nombre": n, "consumo_m3": round(c * 1000 + random.uniform(-200, 200), 1)} for n, c in distritos]

def _mock_consumo_diario():
    meses = ["Feb", "Mar", "Abr"]
    data = []
    for mes in meses:
        for dia in range(1, 29 if mes == "Feb" else 31):
            base = 420000 + math.sin(dia / 5) * 15000
            data.append({
                "fecha": f"2026-{['02','03','04'][meses.index(mes)]}-{dia:02d}",
                "mes": mes,
                "consumo_m3": round(base + random.uniform(-8000, 8000)),
            })
    return data

def _mock_sensores():
    total = 120000
    activos = 117234
    fallas = total - activos
    return {
        "total": total,
        "activos": activos,
        "fallas": fallas,
        "pct_fallas": round(fallas / total * 100, 2),
        "radiobases": 14,
        "modelos": [
            {"modelo": "Itron OpenWay Riva", "cantidad": 35000},
            {"modelo": "Landis+Gyr E360",    "cantidad": 28000},
            {"modelo": "Honeywell Elster",   "cantidad": 24000},
            {"modelo": "Kamstrup MULTICAL",  "cantidad": 20000},
            {"modelo": "Sensus iPERL",       "cantidad": 13000},
        ]
    }

def _mock_clima():
    return [
        {"mes": "Feb", "semana": i+1,
         "temp_c": round(18 + i*1.5 + random.uniform(-1, 2), 1),
         "consumo_m3": round(390000 + i*12000 + random.uniform(-5000, 5000))}
        for i in range(12)
    ]

# ── Vistas ────────────────────────────────────────────────
@dashboard_bp.route("/")
def index():
    return render_template("dashboard/index.html")

@dashboard_bp.route("/alcaldia")
def alcaldia():
    return render_template("dashboard/alcaldia.html")

@dashboard_bp.route("/semapa")
def semapa():
    return render_template("dashboard/semapa.html")

# ── API mock endpoints (AJAX) ─────────────────────────────
@dashboard_bp.route("/api/distritos")
def api_distritos():
    return jsonify(_mock_distritos())

@dashboard_bp.route("/api/consumo-diario")
def api_consumo_diario():
    return jsonify(_mock_consumo_diario())

@dashboard_bp.route("/api/sensores")
def api_sensores():
    return jsonify(_mock_sensores())

@dashboard_bp.route("/api/clima")
def api_clima():
    return jsonify(_mock_clima())

@dashboard_bp.route("/api/resumen")
def api_resumen():
    return jsonify({
        "poblacion": 658068,
        "consumo_total_m3": 423800,
        "consumo_per_capita_L": round(423800 * 1000 / 658068, 1),
        "meta_onu_L": 300,
        "medidores_activos": 117234,
        "contratos": 100000,
        "infraestructuras": 80000,
        "alertas_sobreconsumo": 7,
        "zonas_estres_hidrico": 3,
    })
