import os

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()


class Config:
    SECRET_KEY = "this_is_a_super_secure_32_char_secret_key_123"
    SQLALCHEMY_DATABASE_URI = "sqlite:///database.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = "this_is_a_super_secure_32_char_secret_key_123"
    GOOGLE_CHAT_WEBHOOK_URL = os.getenv("GOOGLE_CHAT_WEBHOOK_URL", "").strip()
    DAILY_REPORT_TIMEZONE = os.getenv("DAILY_REPORT_TIMEZONE", "Asia/Kolkata").strip() or "Asia/Kolkata"
    DAILY_REPORT_HOUR = int(os.getenv("DAILY_REPORT_HOUR", "20"))
    DAILY_REPORT_MINUTE = int(os.getenv("DAILY_REPORT_MINUTE", "20"))
    ENABLE_DAILY_REPORT_SCHEDULER = os.getenv("ENABLE_DAILY_REPORT_SCHEDULER", "1").strip().lower() not in {"0", "false", "no"}
    ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")
    ROBOFLOW_MODEL_ID = os.getenv("ROBOFLOW_MODEL_ID", "kulhad-detector/1").strip() or "kulhad-detector/1"
    ROBOFLOW_API_URL = os.getenv("ROBOFLOW_API_URL", "https://serverless.roboflow.com").strip() or "https://serverless.roboflow.com"
