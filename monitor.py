"""
ETH 价格波动监控脚本 v2

功能：
  - 每分钟 0 秒对齐检查（整分整秒）
  - 双滑动窗口：5 分钟 / 10 分钟
  - 5 分钟波动 ≥ $10 → 邮件告警
  - 10 分钟波动 ≥ $20 → 邮件告警
  - 每个窗口独立冷却（15min / 30min）

数据源：Gate.io（免费，国内可访问）
"""

import time
import smtplib
import ssl
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import deque
from typing import Optional

try:
    import requests
except ImportError:
    print("请先安装依赖: pip install requests python-dotenv")
    exit(1)

from config import (
    SYMBOL,
    WINDOW_1_MINUTES, WINDOW_1_THRESHOLD,
    WINDOW_2_MINUTES, WINDOW_2_THRESHOLD,
    COOLDOWN_1_MINUTES, COOLDOWN_2_MINUTES,
    EMAIL_ENABLED, SMTP_HOST, SMTP_PORT, SMTP_USE_SSL,
    SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL
)


# ──────────────────────────────────────────────
# 数据源
# ──────────────────────────────────────────────

def fetch_eth_price() -> Optional[float]:
    """从 Gate.io 获取 ETH/USDT 最新价格"""
    try:
        url = "https://api.gateio.ws/api/v4/spot/tickers"
        resp = requests.get(url, params={"currency_pair": "ETH_USDT"}, timeout=10)
        data = resp.json()
        if isinstance(data, list) and len(data) > 0:
            return float(data[0]["last"])
    except Exception as e:
        print(f"[错误] 获取价格失败: {e}")
    return None


# ──────────────────────────────────────────────
# 滑动窗口
# ──────────────────────────────────────────────

class PriceWindow:
    """滑动窗口：记录最近 N 分钟的价格"""

    def __init__(self, window_minutes: int):
        self.window = timedelta(minutes=window_minutes)
        self.prices: deque = deque()

    def add(self, price: float):
        now = datetime.now()
        self.prices.append((now, price))
        self._cleanup()

    def _cleanup(self):
        cutoff = datetime.now() - self.window
        while self.prices and self.prices[0][0] < cutoff:
            self.prices.popleft()

    def calc_change(self) -> Optional[float]:
        """计算窗口内价格变化（绝对金额，美元）"""
        if len(self.prices) < 2:
            return None
        self._cleanup()
        if len(self.prices) < 2:
            return None
        oldest = self.prices[0][1]
        newest = self.prices[-1][1]
        return newest - oldest

    def get_info(self) -> Optional[dict]:
        """返回窗口统计信息"""
        if len(self.prices) < 2:
            return None
        self._cleanup()
        prices_only = [p[1] for p in self.prices]
        return {
            "oldest": prices_only[0],
            "newest": prices_only[-1],
            "min": min(prices_only),
            "max": max(prices_only),
            "count": len(prices_only)
        }


# ──────────────────────────────────────────────
# 告警冷却
# ──────────────────────────────────────────────

class AlertCooldown:
    def __init__(self):
        self.last_alert: Optional[datetime] = None

    def should_alert(self, cooldown_minutes: int) -> bool:
        if self.last_alert is None:
            return True
        return (datetime.now() - self.last_alert) >= timedelta(minutes=cooldown_minutes)

    def record_alert(self):
        self.last_alert = datetime.now()


# ──────────────────────────────────────────────
# 邮件发送
# ──────────────────────────────────────────────

def send_email(subject: str, body: str) -> bool:
    if not EMAIL_ENABLED:
        print(f"[邮件未启用] {subject}")
        return True
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg["Subject"] = subject

        html = f"""
        <html>
        <body style="font-family:Arial,sans-serif;padding:20px;">
            <h2 style="color:#d32f2f;">⚠️ ETH 价格波动提醒</h2>
            <div style="background:#f5f5f5;padding:15px;border-radius:8px;">
                <pre style="font-size:14px;line-height:1.6;">{body}</pre>
            </div>
            <p style="color:#888;font-size:12px;">
                时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </body>
        </html>
        """
        msg.attach(MIMEText(html, "html", "utf-8"))
        context = ssl.create_default_context()

        if SMTP_USE_SSL:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls(context=context)
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())

        print(f"[邮件已发送] {subject}")
        return True
    except Exception as e:
        print(f"[邮件发送失败] {e}")
        return False


# ──────────────────────────────────────────────
# 时间对齐
# ──────────────────────────────────────────────

def wait_until_next_minute():
    """等待到下一个整分 0 秒"""
    now = datetime.now()
    seconds_left = 60 - now.second
    if seconds_left == 60:
        return  # 已经是 0 秒
    print(f"[{now.strftime('%H:%M:%S')}] 等待 {seconds_left} 秒到下一个整分...")
    time.sleep(seconds_left)


# ──────────────────────────────────────────────
# 告警内容
# ──────────────────────────────────────────────

def format_alert(window_name: str, threshold: float, change: float, info: dict) -> str:
    direction = "📈 上涨" if change > 0 else "📉 下跌"
    return f"""{window_name} 触发告警

{direction} ${abs(change):.2f}（阈值 ±${threshold:.0f}）

当前价格: ${info['newest']:,.2f}
窗口起始: ${info['oldest']:,.2f}
窗口最高: ${info['max']:,.2f}
窗口最低: ${info['min']:,.2f}
数据点数: {info['count']} 个"""


# ──────────────────────────────────────────────
# 主循环
# ──────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  ETH 价格波动监控 v2")
    print(f"  数据源: Gate.io")
    print(f"  币种: {SYMBOL}")
    print(f"  窗口1: {WINDOW_1_MINUTES} 分钟 / ±${WINDOW_1_THRESHOLD:.0f}")
    print(f"  窗口2: {WINDOW_2_MINUTES} 分钟 / ±${WINDOW_2_THRESHOLD:.0f}")
    print(f"  冷却1: {COOLDOWN_1_MINUTES} 分钟 | 冷却2: {COOLDOWN_2_MINUTES} 分钟")
    print(f"  邮件: {'开启' if EMAIL_ENABLED else '关闭'}")
    print("=" * 60)

    # 初始化
    window_1 = PriceWindow(WINDOW_1_MINUTES)
    window_2 = PriceWindow(WINDOW_2_MINUTES)
    cooldown_1 = AlertCooldown()
    cooldown_2 = AlertCooldown()
    check_count = 0
    alert_count = 0

    # 时间对齐
    wait_until_next_minute()
    print()

    while True:
        try:
            now = datetime.now()
            price = fetch_eth_price()
            check_count += 1

            if price is None:
                print(f"[{now.strftime('%H:%M:%S')}] 第 {check_count} 次 — 获取失败")
                time.sleep(60)
                continue

            # 存入两个窗口
            window_1.add(price)
            window_2.add(price)

            # 检查窗口1
            change_1 = window_1.calc_change()
            alert_1 = ""
            if change_1 is not None and abs(change_1) >= WINDOW_1_THRESHOLD:
                if cooldown_1.should_alert(COOLDOWN_1_MINUTES):
                    info_1 = window_1.get_info()
                    alert_count += 1
                    body = format_alert("5 分钟窗口", WINDOW_1_THRESHOLD, change_1, info_1)
                    subject = f"⚠️ ETH {WINDOW_1_MINUTES}min {'↑' if change_1 > 0 else '↓'}${abs(change_1):.2f} — ${price:,.2f}"
                    send_email(subject, body)
                    cooldown_1.record_alert()
                    alert_1 = f" | 🚨 5min: {change_1:+.2f}$"
                else:
                    alert_1 = f" | 5min 冷却中"

            # 检查窗口2
            change_2 = window_2.calc_change()
            alert_2 = ""
            if change_2 is not None and abs(change_2) >= WINDOW_2_THRESHOLD:
                if cooldown_2.should_alert(COOLDOWN_2_MINUTES):
                    info_2 = window_2.get_info()
                    alert_count += 1
                    body = format_alert("10 分钟窗口", WINDOW_2_THRESHOLD, change_2, info_2)
                    subject = f"⚠️ ETH {WINDOW_2_MINUTES}min {'↑' if change_2 > 0 else '↓'}${abs(change_2):.2f} — ${price:,.2f}"
                    send_email(subject, body)
                    cooldown_2.record_alert()
                    alert_2 = f" | 🚨 10min: {change_2:+.2f}$"
                else:
                    alert_2 = f" | 10min 冷却中"

            # 状态输出
            c1 = f"5min:{change_1:+.2f}$" if change_1 else "5min:--"
            c2 = f"10min:{change_2:+.2f}$" if change_2 else "10min:--"
            print(f"[{now.strftime('%H:%M:%S')}] #{check_count} ETH: ${price:,.2f} | {c1} | {c2}{alert_1}{alert_2}")

        except KeyboardInterrupt:
            print(f"\n监控停止。共 {check_count} 次检查，{alert_count} 次告警。")
            break
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 异常: {e}")

        time.sleep(60)


if __name__ == "__main__":
    main()
