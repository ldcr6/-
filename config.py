"""
ETH Price Alert - Configuration
从环境变量或 .env 文件加载配置，敏感信息不写入代码
"""

import os
from pathlib import Path

# 加载 .env 文件（如果存在）
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

# ──────────────────────────────────────────────
# CoinGlass API（备选数据源）
# ──────────────────────────────────────────────
COINGLASS_API_KEY = os.environ.get("COINGLASS_API_KEY", "")

# ──────────────────────────────────────────────
# 监控参数
# ──────────────────────────────────────────────
SYMBOL = "ETH"
THRESHOLD_PERCENT = float(os.environ.get("THRESHOLD_PERCENT", "1.0"))
CHECK_INTERVAL_SECONDS = int(os.environ.get("CHECK_INTERVAL", "60"))
SLIDING_WINDOW_MINUTES = int(os.environ.get("WINDOW_MINUTES", "10"))

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
