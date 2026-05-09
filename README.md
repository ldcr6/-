<div align="center">

# 📈 ETH Price Alert Monitor

**基于滑动窗口算法的 ETH 价格波动实时监控与邮件告警系统**

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-brightgreen.svg)

</div>

---

## 📖 项目简介

一个轻量级的 ETH/USDT 价格监控工具，通过滑动窗口算法实时检测价格波动，当波动幅度超过预设阈值时自动发送邮件告警。适用于加密货币交易者、量化分析师和区块链开发者。

## ✨ 核心特性

- **滑动窗口算法** — 精确计算指定时间窗口内的价格变化幅度
- **多数据源支持** — Gate.io（主）/ CoinGlass（备），自动故障转移
- **智能告警冷却** — 同一方向 30 分钟内不重复告警，避免信息轰炸
- **邮件通知** — 支持 163/QQ/Gmail 等主流邮箱 SMTP 发送
- **纯 Python 实现** — 无复杂依赖，单文件可运行

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────┐
│                  主监控循环                       │
│         每 N 秒获取一次最新价格                    │
├─────────────────────────────────────────────────┤
│              多源价格获取层                       │
│    Gate.io (主)  ←→  CoinGlass (备)              │
├─────────────────────────────────────────────────┤
│              滑动窗口引擎                        │
│   deque 维护最近 M 分钟价格数据                   │
│   计算窗口内 (最新-最旧)/最旧 × 100%              │
├─────────────────────────────────────────────────┤
│              告警决策层                          │
│   |变化%| ≥ 阈值 → 冷却检查 → 邮件发送           │
└─────────────────────────────────────────────────┘
```

## 📁 项目结构

```
eth-price-alert/
├── monitor.py          # 主监控脚本
├── config.py           # 配置模块（读取环境变量）
├── .env.example        # 环境变量模板
├── requirements.txt    # Python 依赖
├── .gitignore          # Git 忽略规则
└── README.md           # 项目文档
```

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/ldcr6/eth-price-alert.git
cd eth-price-alert
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并填入你的配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 邮件配置（必须）
SENDER_EMAIL=your_email@163.com
SENDER_PASSWORD=your_smtp_authorization_code
RECEIVER_EMAIL=your_email@163.com

# 监控参数（可选）
THRESHOLD_PERCENT=1.0    # 波动阈值（%）
CHECK_INTERVAL=60        # 检查间隔（秒）
WINDOW_MINUTES=10        # 滑动窗口（分钟）
```

### 4. 运行

```bash
python monitor.py
```

## ⚙️ 配置说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `THRESHOLD_PERCENT` | `1.0` | 价格波动触发阈值（%） |
| `CHECK_INTERVAL` | `60` | 每次检查间隔（秒） |
| `WINDOW_MINUTES` | `10` | 滑动窗口时长（分钟） |
| `SMTP_HOST` | `smtp.163.com` | SMTP 服务器地址 |
| `SMTP_PORT` | `465` | SMTP 端口（SSL） |
| `EMAIL_ENABLED` | `true` | 是否启用邮件告警 |

### SMTP 授权码获取

- **163 邮箱**：设置 → POP3/SMTP/IMAP → 开启 SMTP → 获取授权码
- **QQ 邮箱**：设置 → 账户 → POP3/SMTP → 开启 → 获取授权码

## 📊 工作原理

### 滑动窗口算法

```python
# 价格数据以 (时间, 价格) 元组存储在 deque 中
prices = deque([
    (10:00, 2300.00),
    (10:01, 2305.50),
    (10:02, 2310.00),
    ...
])

# 计算窗口内变化百分比
change = (newest - oldest) / oldest × 100%
# 例: (2310 - 2300) / 2300 × 100% = +0.43%
```

### 告警冷却机制

```
10:00  价格 +1.2% → 触发告警 ✅ → 冷却开始（30min）
10:05  价格 +1.5% → 冷却中，跳过 ⏸️
10:10  价格 +2.0% → 冷却中，跳过 ⏸️
10:31  价格 +1.3% → 冷却结束，触发告警 ✅
```

## 📄 License

[MIT](LICENSE)

## 🙏 致谢

- [Gate.io API](https://www.gateio.pro/docs/developers/apiv4/) — 免费实时行情数据
- [CoinGlass API](https://docs.coinglass.com/) — 加密货币衍生品数据

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐ Star！**

</div>
