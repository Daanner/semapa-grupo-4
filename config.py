import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "semapa-dev-key-2026")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/semana")
    SQLALCHEMY_TRACK_MODIFICATIONS = False#############################
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/semapa")
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"

    # ── Correo (Gmail SMTP - gratis, sin servicios externos) ──
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")          # tu correo Gmail
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")  # contraseña de aplicación (16 chars)
    MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "SEMAPA")

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
