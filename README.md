<div align="center">

# 📈 ETH Price Alert Monitor v2

**基于双滑动窗口算法的 ETH 价格波动实时监控与邮件告警系统**

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-brightgreen.svg)

</div>

---

## 📖 项目简介

轻量级 ETH/USDT 价格监控工具。每分钟整秒对齐采样，通过双滑动窗口（5 分钟 / 10 分钟）检测价格波动，超过绝对金额阈值时自动发送邮件告警。

## ✨ 核心特性

- **整分对齐** — 启动后等到下一个整分 0 秒开始，之后每分钟 0 秒精确采样
- **双窗口检测** — 5 分钟 ≥ $10 和 10 分钟 ≥ $20 两个独立窗口同时监控
- **绝对金额告警** — 以美元为单位，直观易懂
- **独立冷却** — 每个窗口独立冷却，避免重复告警
- **免费数据源** — Gate.io API，无需 API Key，国内可访问

## 🏗️ 工作原理

```
启动 → 等待到整分 0 秒
       ↓
每 60 秒循环：
  获取 ETH/USDT 最新价格
       ↓
  存入 5 分钟窗口 + 10 分钟窗口
       ↓
  检查 5 分钟窗口：|变化| ≥ $10 且冷却结束 → 发邮件
       ↓
  检查 10 分钟窗口：|变化| ≥ $20 且冷却结束 → 发邮件
       ↓
  输出状态日志
       ↓
  等待下一个整分 0 秒
```

### 告警示例

```
22:24:00 ETH: $2,300 | 5min:+$3.00 | 10min:+$5.00
22:25:00 ETH: $2,305 | 5min:+$8.00 | 10min:+$12.00
22:26:00 ETH: $2,308 | 5min:+$11.00 | 10min:+$15.00
                               ↓
              🚨 5 分钟窗口触发！$11 ≥ $10 → 发邮件
                               ↓
                    冷却 15 分钟（5min 窗口）
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

复制 `.env.example` 为 `.env`：

```bash
cp .env.example .env
```

编辑 `.env`，填入邮箱配置：

```env
SENDER_EMAIL=your_email@163.com
SENDER_PASSWORD=your_smtp_authorization_code
RECEIVER_EMAIL=your_email@163.com
```

### 3. 运行

```bash
python monitor.py
```

输出示例：

```
============================================================
  ETH 价格波动监控 v2
  数据源: Gate.io
  币种: ETH
  窗口1: 5 分钟 / ±$10
  窗口2: 10 分钟 / ±$20
============================================================

[22:24:00] #1 ETH: $2,313.82 | 5min:-- | 10min:--
[22:25:00] #2 ETH: $2,315.50 | 5min:+$1.68 | 10min:+$1.68
[22:26:00] #3 ETH: $2,320.00 | 5min:+$6.18 | 10min:+$6.18
```

## ⚙️ 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `WINDOW_1_MINUTES` | `5` | 窗口1时长（分钟） |
| `WINDOW_1_THRESHOLD` | `10` | 窗口1触发金额（美元） |
| `WINDOW_2_MINUTES` | `10` | 窗口2时长（分钟） |
| `WINDOW_2_THRESHOLD` | `20` | 窗口2触发金额（美元） |
| `COOLDOWN_1_MINUTES` | `15` | 窗口1冷却时间（分钟） |
| `COOLDOWN_2_MINUTES` | `30` | 窗口2冷却时间（分钟） |
| `SMTP_HOST` | `smtp.163.com` | SMTP 服务器 |
| `SMTP_PORT` | `465` | SMTP 端口 |

### SMTP 授权码获取

- **163 邮箱**：设置 → POP3/SMTP/IMAP → 开启 SMTP → 获取授权码
- **QQ 邮箱**：设置 → 账户 → POP3/SMTP → 开启 → 获取授权码

## 📁 项目结构

```
eth-price-alert/
├── monitor.py          # 主监控脚本
├── config.py           # 配置模块（读取环境变量）
├── .env.example        # 环境变量模板
├── requirements.txt    # Python 依赖
├── .gitignore          # Git 忽略规则
├── LICENSE             # MIT 许可证
└── README.md           # 项目文档
```

## 📄 License

[MIT](LICENSE)

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐ Star！**

</div>
