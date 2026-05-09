"""
ETH Price Alert - Configuration
敏感信息通过环境变量或 .env 文件配置
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

# ──────────────────────────────────────────────
# 数据源
# ──────────────────────────────────────────────
COINGLASS_API_KEY = os.environ.get("COINGLASS_API_KEY", "")

# ──────────────────────────────────────────────
# 监控参数
# ──────────────────────────────────────────────
SYMBOL = "ETH"

# 窗口1：5 分钟内波动 ≥ $10
WINDOW_1_MINUTES = int(os.environ.get("WINDOW_1_MINUTES", "5"))
WINDOW_1_THRESHOLD = float(os.environ.get("WINDOW_1_THRESHOLD", "10"))  # 美元

# 窗口2：10 分钟内波动 ≥ $20
WINDOW_2_MINUTES = int(os.environ.get("WINDOW_2_MINUTES", "10"))
WINDOW_2_THRESHOLD = float(os.environ.get("WINDOW_2_THRESHOLD", "20"))  # 美元

# 冷却时间（分钟）
COOLDOWN_1_MINUTES = int(os.environ.get("COOLDOWN_1_MINUTES", "15"))
COOLDOWN_2_MINUTES = int(os.environ.get("COOLDOWN_2_MINUTES", "30"))

# ──────────────────────────────────────────────
# 邮件配置
# ──────────────────────────────────────────────
EMAIL_ENABLED = os.environ.get("EMAIL_ENABLED", "true").lower() == "true"
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.163.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USE_SSL = os.environ.get("SMTP_USE_SSL", "true").lower() == "true"
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL", "")
