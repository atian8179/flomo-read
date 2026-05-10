<div align="center">

# 🔓 flomo-read

**让 AI Agent 直接读取你的 flomo 浮墨笔记**

[![GitHub Stars](https://img.shields.io/github/stars/atian8179/flomo-read?style=social)](https://github.com/atian8179/flomo-read)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

</div>

---

## 🚀 快速开始

**三步搞定：**

1. 复制这个仓库地址 👉 `https://github.com/atian8179/flomo-read`
2. 丢给你的 AI Agent（Hermes / OpenClaw），说：「帮我安装这个 skill」
3. 告诉它你的 flomo 手机号/邮箱和密码
4. 搞定！直接说「读一下我的 flomo 笔记」就行

**或者你想自己跑：**

```bash
export FLOMO_EMAIL="你的手机号或邮箱"
export FLOMO_PASSWORD="你的密码"
python flomo_api.py
```

**作为 Python 库：**

```python
from flomo_api import FlomoClient

client = FlomoClient("your_email", "your_password")
memos = client.get_latest_memos_text(5)
for m in memos:
    print(m["created_at"], m["content"])
```

## ✨ 能做什么

- 📖 读取最新 flomo 笔记（最多 200 条）
- 🏷️ 获取标签树
- 🔍 搜索笔记内容
- 🎙️ 支持语音转写笔记的读取

---

## 📖 API 使用指南

### FlomoClient 类方法

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `FlomoClient(email, password)` | 构造函数，自动登录 | 实例 |
| `get_latest_memos(limit=200)` | 获取最新笔记（原始 JSON） | `list[dict]` |
| `get_latest_memos_text(limit=10)` | 获取最新笔记（纯文本） | `list[dict]` |
| `get_tag_tree()` | 获取标签树 | `dict` |
| `get_user_info()` | 获取当前用户信息 | `dict` |
| `strip_html(content)` | 静态方法，去除 HTML 标签 | `str` |

### 纯文本版返回结构（get_latest_memos_text）

```python
{
    "content": "纯文本内容",
    "tags": ["读书", "AI"],
    "created_at": "2026-05-09 21:28:09",
    "source": "ios",       # ios / web / android / api
    "has_voice": True       # 是否包含语音转写
}
```

### 原始 JSON 返回结构（get_latest_memos）

```python
{
    "content": "<p>HTML格式内容</p>",
    "tags": ["标签1"],
    "created_at": "2026-05-09 21:28:09",
    "updated_at": "2026-05-09 21:28:17",
    "source": "ios",
    "slug": "MjM1ODQzOTM3",
    "files": [
        {
            "type": "recorded",       # 语音笔记
            "seconds": 125,
            "content": "语音转文字内容",
            "url": "https://flomo.oss-cn-shanghai.aliyuncs.com/..."
        }
    ]
}
```

---

## 📡 支持的 API 端点

以下是通过逆向确认可用的 flomo API 端点：

| 端点 | 方法 | 说明 | 状态 |
|------|------|------|------|
| `/user/login_by_email` | POST | 邮箱/手机号登录 | ✅ |
| `/memo/latest_updated_desc` | GET | 最新 200 条笔记（按更新时间倒序） | ✅ 主力端点 |
| `/tag/tree` | GET | 标签树 | ✅ |
| `/user/me` | GET | 用户信息 | ✅ |
| `/memo/search` | GET | 搜索笔记 | ✅ |
| `/subscription/` | GET | 订阅信息（Pro 状态等） | ✅ |
| `/login_device` | GET | 登录设备列表 | ✅ |
| `/incoming_webhook` | GET | API webhook 信息 | ✅ |
| `/emoji` | GET | emoji 列表 | ✅ |
| `/biz/config` | GET | 业务配置 | ✅ |
| `/memo/` | GET | ~~笔记列表~~ | ❌ SPA 拦截，返回 HTML |

> ⚠️ `latest_updated_desc` 是硬编码最多 200 条，不支持分页（已测试 limit/page/offset/cursor/before/since_id 等参数，均无效）。

---

## 🔬 核心原理

### 1. API 签名算法

从 `chunk-core.*.js` 的 `_getSign` 方法逆向出签名逻辑：

```python
import hashlib

def get_sign(params):
    sorted_keys = sorted(params.keys())
    query = "&".join(f"{k}={params[k]}" for k in sorted_keys)
    return hashlib.md5((query + SALT).encode()).hexdigest()
```

**流程**：参数按 key 字母排序 → 拼接 `key=value&` → 去末尾 `&` → 加 salt → MD5

### 2. 公共请求参数

每个 API 请求都需要带上：

```python
{
    "timestamp": 1715300000,   # Unix 时间戳
    "api_key": "flomo_web",
    "app_version": "2.0",
    "platform": "web",
    "sign": "计算出的签名"
}
```

### 3. 认证机制

- 登录接口：`POST /user/login_by_email`
- 返回 `access_token`（格式如 `18951206|SYxnkF...e3oqs85upo`，含 `|` 字符）
- 后续请求通过 `Authorization: Bearer {token}` 携带

---

## 🐛 踩坑记录

| 坑 | 说明 | 解决方案 |
|----|------|----------|
| `/memo/` 返回 HTML | 被 SPA catch-all 路由拦截 | 用 `/memo/latest_updated_desc` |
| token 解析失败 | access_token 含 `\|` 字符，`json.loads()` 可能误解析 | 用 `json.load(sys.stdin)` 管道读取 |
| v.flomoapp.com 403 | 检测 HeadlessChrome UA，无法浏览器自动化 | 直接调 API，不走浏览器 |
| 200 条上限 | 服务端硬编码，所有分页参数均无效 | 如需更多，用 `/memo/search` 按标签分批搜索 |
| gzip 压缩 | JS 文件是 gzip 压缩的 | curl 加 `--compressed` 或解压后再分析 |

---

## 🔍 逆向过程

整个逆向约 1 小时，只用到了 curl 和浏览器 DevTools：

1. **入口**：`v.flomoapp.com` 加载 `index.*.js`
2. **定位 API**：在压缩后的 JS 中搜索 `login_by_email`，找到 API base URL `https://flomoapp.com/api/v1`
3. **提取签名**：搜索 `_getSign`，发现 salt 和排序规则
4. **验证**：curl 手工构造请求，逐步验证签名算法正确性
5. **踩坑**：发现 `/memo/` 返回 HTML → 搜索 JS 路由表 → 找到 `latest_updated_desc`
6. **完整测试**：逐一测试所有端点，确认可用/不可用状态

---

## 🏗️ 项目结构

```
flomo-read/
├── README.md              # 你正在看的
├── LICENSE                # MIT 协议
├── flomo_api.py           # 独立 Python 客户端（可直接引用）
└── skills/
    └── flomo-read/
        └── SKILL.md       # AI Agent 技能文档（Hermes/OpenClaw 通用）
```

## ⚠️ 免责声明

- 本项目仅供**学习研究**使用
- API 签名算法可能随 flomo 版本更新而变化
- 请勿用于商业目的或大规模数据抓取
- 使用时请遵守 flomo 的服务条款

## 📄 License

[MIT](LICENSE)

---

<div align="center">

觉得有用？给个 ⭐ Star 吧 🙏

</div>
