"""
ETH 价格波动监控脚本
- 每分钟从 Gate.io 获取 ETH 最新价格
- 维护 10 分钟滑动窗口
- 价格波动超过 1% 时发送邮件提醒
- 冷却机制：同一方向 30 分钟内不重复告警
"""

import time
import json
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
    print("请先安装 requests: pip install requests")
    exit(1)

from config import (
    COINGLASS_API_KEY, SYMBOL, THRESHOLD_PERCENT,
    CHECK_INTERVAL_SECONDS, SLIDING_WINDOW_MINUTES,
    EMAIL_ENABLED, SMTP_HOST, SMTP_PORT, SMTP_USE_SSL,
    SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL
)


# ──────────────────────────────────────────────
# 数据源
# ──────────────────────────────────────────────

def fetch_from_gateio() -> Optional[float]:
    """从 Gate.io 获取 ETH/USDT 最新价格"""
    try:
        url = "https://api.gateio.ws/api/v4/spot/tickers"
        params = {"currency_pair": "ETH_USDT"}
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if isinstance(data, list) and len(data) > 0:
            return float(data[0]["last"])
    except Exception as e:
        print(f"[Gate.io] 失败: {e}")
    return None


def fetch_from_coinglass() -> Optional[float]:
    """从 CoinGlass 获取 ETH 价格（需要付费计划）"""
    try:
        url = "https://open-api-v4.coinglass.com/api/futures/coins-price-change"
        headers = {
            "CG-API-KEY": COINGLASS_API_KEY,
            "Accept": "application/json"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        if data.get("code") == "0" and data.get("data"):
            for coin in data["data"]:
                if coin.get("symbol") == "ETH":
                    return float(coin.get("currentPrice", 0))
    except Exception as e:
        print(f"[CoinGlass] 失败: {e}")
    return None


def fetch_eth_price() -> Optional[float]:
    """获取 ETH 当前价格（多源）"""
    price = fetch_from_gateio()
    if price is not None:
        return price
    
    price = fetch_from_coinglass()
    if price is not None:
        return price
    
    print("[警告] 所有数据源均获取失败")
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

    def get_extremes(self) -> Optional[dict]:
        if len(self.prices) < 2:
            return None
        self._cleanup()
        prices_only = [p[1] for p in self.prices]
        return {
            "min": min(prices_only),
            "max": max(prices_only),
            "current": prices_only[-1],
            "oldest": prices_only[0],
            "count": len(prices_only)
        }

    def calc_change_percent(self) -> Optional[float]:
        if len(self.prices) < 2:
            return None
        self._cleanup()
        if len(self.prices) < 2:
            return None
        oldest = self.prices[0][1]
        newest = self.prices[-1][1]
        if oldest == 0:
            return None
        return ((newest - oldest) / oldest) * 100


# ──────────────────────────────────────────────
# 告警冷却
# ──────────────────────────────────────────────

class AlertCooldown:
    def __init__(self, cooldown_minutes: int = 30):
        self.cooldown = timedelta(minutes=cooldown_minutes)
        self.last_alert: dict = {}

    def should_alert(self, direction: str) -> bool:
        now = datetime.now()
        last = self.last_alert.get(direction)
        if last and (now - last) < self.cooldown:
            return False
        return True

    def record_alert(self, direction: str):
        self.last_alert[direction] = datetime.now()


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
                时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                来源: ETH 价格监控脚本
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
# 告警格式
# ──────────────────────────────────────────────

def format_alert(change_pct: float, extremes: dict) -> str:
    direction = "📈 上涨" if change_pct > 0 else "📉 下跌"
    return f"""ETH 价格在过去 {SLIDING_WINDOW_MINUTES} 分钟内 {direction} {abs(change_pct):.2f}%

当前价格: ${extremes['current']:,.2f}
窗口起始: ${extremes['oldest']:,.2f}
窗口最高: ${extremes['max']:,.2f}
窗口最低: ${extremes['min']:,.2f}
数据点数: {extremes['count']} 个

阈值: ±{THRESHOLD_PERCENT}%
方向: {direction}"""


# ──────────────────────────────────────────────
# 主循环
# ──────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  ETH 价格波动监控")
    print(f"  数据源: Gate.io (主) / CoinGlass (备)")
    print(f"  币种: {SYMBOL}")
    print(f"  阈值: ±{THRESHOLD_PERCENT}%")
    print(f"  窗口: {SLIDING_WINDOW_MINUTES} 分钟")
    print(f"  检查间隔: {CHECK_INTERVAL_SECONDS} 秒")
    print(f"  邮件提醒: {'开启' if EMAIL_ENABLED else '关闭'}")
    print("=" * 60)
    print()

    window = PriceWindow(SLIDING_WINDOW_MINUTES)
    cooldown = AlertCooldown(cooldown_minutes=30)
    check_count = 0
    alert_count = 0

    while True:
        try:
            price = fetch_eth_price()
            check_count += 1

            if price is None:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 第 {check_count} 次 — 获取失败，跳过")
                time.sleep(CHECK_INTERVAL_SECONDS)
                continue

            window.add(price)
            extremes = window.get_extremes()
            change_pct = window.calc_change_percent()

            status = ""
            if change_pct is not None:
                status = f" | 变化: {change_pct:+.3f}%"

                if abs(change_pct) >= THRESHOLD_PERCENT:
                    direction = "up" if change_pct > 0 else "down"

                    if cooldown.should_alert(direction):
                        alert_count += 1
                        print(f"\n{'!'*60}")
                        print(f"  ⚠️  告警 #{alert_count}: {change_pct:+.2f}%")
                        print(f"{'!'*60}\n")

                        body = format_alert(change_pct, extremes)
                        subject = f"⚠️ ETH {'上涨' if change_pct > 0 else '下跌'} {abs(change_pct):.2f}% — ${price:,.2f}"
                        send_email(subject, body)
                        cooldown.record_alert(direction)
                    else:
                        status += " [冷却中]"

            print(f"[{datetime.now().strftime('%H:%M:%S')}] 第 {check_count} 次 | ETH: ${price:,.2f}{status}")

        except KeyboardInterrupt:
            print(f"\n监控停止。共 {check_count} 次检查，{alert_count} 次告警。")
            break
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 异常: {e}")

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
