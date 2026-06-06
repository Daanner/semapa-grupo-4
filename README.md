# SEMAPA IoT Platform

Plataforma distribuida de gestión inteligente del consumo de agua — Municipio de Cochabamba.

## Equipo

| Rol | Módulo | Responsable(s) |
|-----|--------|----------------|
| Project Manager | Coordinación | Kevin Danner |
| ARquitecto SOftware | Coordinación | Alberto Ayllón |
| DBB | `app/db/` | Jesus Murillo · Cristhian Obario |
| Dashboard | `app/dashboard/` | Franz · Carmen Rosa |
| Mensajería | `app/mensajeria/` | Yesica Zenteno |
| PDF | `app/pdf/` | Alan Lopez · Miriam Apaza |
| Tótem | `app/totem/` | Flores Elia |
| Lector Manual | `app/lector/` | Kevin Trujillo |
| QA | transversal | Helen Pacari |

## Arranque rápido (demo sin BD)

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install flask python-dotenv
python run.py
```

Abrir: http://localhost:5000

## Módulos disponibles

| URL | Módulo |
|-----|--------|
| `/` | Inicio |
| `/dashboard/alcaldia` | Dashboard Alcaldía |
| `/dashboard/semapa` | Dashboard SEMAPA |
| `/mensajeria/` | Sistema de mensajería |
| `/pdf/` | Preavisos PDF |
| `/totem/` | Tótem ciudadano |
| `/lector/` | Lector manual |

## Stack

- **Backend**: Python · Flask · Blueprints

## Ramas Git

```
main         ← solo versiones estables (PM + QA)
develop      ← integración continua
feature/db
feature/dashboard
feature/mensajeria
feature/pdf
feature/totem
feature/lector
feature/qa
```
