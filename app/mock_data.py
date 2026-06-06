"""
Datos mock que reflejan exactamente la estructura del CSV real:
  medidor_iot, lecturaAnterior, LecturaActual, fechaHoraLectura, radiobase, fecha_pago
El campo medidor_iot es una MAC address (XX:XX:XX:XX:XX:XX).
El consumo del período = LecturaActual - lecturaAnterior.
"""

# 10 medidores con MAC real extraída del CSV
MEDIDORES = {
    "7D:16:0E:17:7E:AA": {"contrato": "C-001234", "nombre": "Juan Carlos Mendoza",  "ci": "5234891",  "direccion": "Av. Ayacucho 342, Sacaba",    "radiobase": 2,  "tarifa": "Doméstica",  "categoria": 1},
    "D8:E9:8F:ED:58:69": {"contrato": "C-001235", "nombre": "María Flores Quispe",   "ci": "7891234",  "direccion": "Calle Sucre 112, Cercado",    "radiobase": 2,  "tarifa": "Doméstica",  "categoria": 1},
    "92:C5:A5:0E:4E:87": {"contrato": "C-001236", "nombre": "Roberto Quispe Mamani", "ci": "6123456",  "direccion": "Zona Norte, Quillacollo",     "radiobase": 3,  "tarifa": "Social",     "categoria": 2},
    "13:2B:00:FD:4D:C3": {"contrato": "C-001237", "nombre": "Empresa COBOCE S.A.",   "ci": "NIT-1234", "direccion": "Zona Industrial Norte",       "radiobase": 1,  "tarifa": "Industrial", "categoria": 6},
    "93:E7:39:FB:B7:B6": {"contrato": "C-001238", "nombre": "Colegio San Simón",     "ci": "NIT-5678", "direccion": "Av. Pando 890, Cercado",      "radiobase": 1,  "tarifa": "Estatal",    "categoria": 5},
    "0E:0C:55:8E:3A:0F": {"contrato": "C-001239", "nombre": "Ana Rojas Villca",      "ci": "4567890",  "direccion": "Barrio Linde, Sacaba",        "radiobase": 4,  "tarifa": "Doméstica",  "categoria": 1},
    "AD:91:76:E3:05:78": {"contrato": "C-001240", "nombre": "Pedro Vargas Cruz",     "ci": "3456789",  "direccion": "Av. Blanco Galindo Km 5",     "radiobase": 5,  "tarifa": "Doméstica",  "categoria": 1},
    "09:5F:F2:21:5F:93": {"contrato": "C-001241", "nombre": "Hotel Los Andes",       "ci": "NIT-9012", "direccion": "Plaza 14 de Septiembre 23",   "radiobase": 1,  "tarifa": "Comercial",  "categoria": 3},
    "24:E9:49:9E:1C:5E": {"contrato": "C-001242", "nombre": "Luisa Torrez Apaza",    "ci": "8901234",  "direccion": "Zona Sud, Colcapirhua",       "radiobase": 8,  "tarifa": "Doméstica",  "categoria": 1},
    "F8:D4:A4:6F:74:3A": {"contrato": "C-001243", "nombre": "Mercado Calatayud",     "ci": "NIT-3456", "direccion": "Calle Jordán s/n, Cercado",   "radiobase": 14, "tarifa": "Comercial",  "categoria": 3},
}

# Lecturas reales tomadas del CSV (medidor, lecturaAnterior, LecturaActual, fechaHora, radiobase, fecha_pago)
LECTURAS = [
    {"medidor_iot": "7D:16:0E:17:7E:AA", "lecturaAnterior": 1846, "LecturaActual": 1878, "fechaHoraLectura": "02/28/26 21:39", "radiobase": 2,  "fecha_pago": "03/26/26 13:35"},
    {"medidor_iot": "D8:E9:8F:ED:58:69", "lecturaAnterior": 432,  "LecturaActual": 460,  "fechaHoraLectura": "02/28/26 22:45", "radiobase": 2,  "fecha_pago": "03/09/26 15:30"},
    {"medidor_iot": "92:C5:A5:0E:4E:87", "lecturaAnterior": 3022, "LecturaActual": 3031, "fechaHoraLectura": "02/28/26 22:57", "radiobase": 3,  "fecha_pago": "03/26/26 13:03"},
    {"medidor_iot": "13:2B:00:FD:4D:C3", "lecturaAnterior": 4478, "LecturaActual": 4497, "fechaHoraLectura": "02/28/26 23:46", "radiobase": 1,  "fecha_pago": "03/19/26 1:52"},
    {"medidor_iot": "93:E7:39:FB:B7:B6", "lecturaAnterior": 3265, "LecturaActual": 3297, "fechaHoraLectura": "02/28/26 21:49", "radiobase": 1,  "fecha_pago": "03/04/26 18:37"},
    {"medidor_iot": "0E:0C:55:8E:3A:0F", "lecturaAnterior": 1716, "LecturaActual": 1741, "fechaHoraLectura": "02/28/26 23:16", "radiobase": 4,  "fecha_pago": "03/27/26 22:03"},
    {"medidor_iot": "AD:91:76:E3:05:78", "lecturaAnterior": 1433, "LecturaActual": 1439, "fechaHoraLectura": "02/28/26 20:47", "radiobase": 5,  "fecha_pago": "03/22/26 12:58"},
    {"medidor_iot": "09:5F:F2:21:5F:93", "lecturaAnterior": 1423, "LecturaActual": 1444, "fechaHoraLectura": "02/28/26 21:10", "radiobase": 1,  "fecha_pago": "03/27/26 0:30"},
    {"medidor_iot": "24:E9:49:9E:1C:5E", "lecturaAnterior": 2589, "LecturaActual": 2625, "fechaHoraLectura": "02/28/26 23:05", "radiobase": 8,  "fecha_pago": "03/20/26 15:06"},
    {"medidor_iot": "F8:D4:A4:6F:74:3A", "lecturaAnterior": 3660, "LecturaActual": 3678, "fechaHoraLectura": "02/28/26 22:41", "radiobase": 14, "fecha_pago": "03/16/26 15:20"},
]

def get_consumo(lectura: dict) -> int:
    """Consumo del período = LecturaActual - lecturaAnterior"""
    try:
        return int(lectura["LecturaActual"]) - int(lectura["lecturaAnterior"])
    except (KeyError, TypeError, ValueError):
        return 0

def get_medidor_info(mac: str) -> dict | None:
    return MEDIDORES.get(mac)

def get_lecturas_medidor(mac: str) -> list:
    return [l for l in LECTURAS if l["medidor_iot"] == mac]

# Tarifas por categoría (Bs/m³)
TARIFAS = {
    1: {"nombre": "Doméstica",    "precio_m3": 4.02},
    2: {"nombre": "Social",       "precio_m3": 2.50},
    3: {"nombre": "Comercial",    "precio_m3": 6.80},
    4: {"nombre": "Industrial A", "precio_m3": 9.50},
    5: {"nombre": "Estatal",      "precio_m3": 3.20},
    6: {"nombre": "Industrial B", "precio_m3": 12.00},
    7: {"nombre": "Especial",     "precio_m3": 5.10},
    8: {"nombre": "Uso múltiple", "precio_m3": 7.30},
    9: {"nombre": "Mixta",        "precio_m3": 5.80},
}

def calcular_importe(consumo_m3: float, categoria: int) -> float:
    tarifa = TARIFAS.get(categoria, TARIFAS[1])
    return round(consumo_m3 * tarifa["precio_m3"], 2)
