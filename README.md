<div align="center">

# 🔓 flomo API 逆向

**非官方 flomo 浮墨笔记 Python 客户端**

通过逆向 flomo Web 端 JS 源码，提取签名算法并实现笔记读取。

[![GitHub Stars](https://img.shields.io/github/stars/atian8179/hermes-skills?style=social)](https://github.com/atian8179/hermes-skills)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://python.org)

</div>

---

## ✨ 这是什么？

flomo 是一款优秀的卡片笔记工具，但没有开放 API 供第三方读取笔记。本项目通过**逆向 flomo Web 端 JavaScript 源码**，提取了完整的 API 签名算法，实现了：

- 📖 读取最新 200 条笔记
- 🏷️ 获取标签树
- 🔍 笔记搜索
- 👤 用户信息查询

## 🎯 核心发现

### 1. API 签名算法

从 `chunk-core.*.js` 的 `_getSign` 方法中逆向出签名逻辑：

```python
def get_sign(params):
    sorted_keys = sorted(params.keys())
    query = "&".join(f"{k}={params[k]}" for k in sorted_keys)
    return md5(query + SALT).hexdigest()
```

参数按 key 排序 → 拼接 → 加 salt → MD5，就这么简单。

### 2. SPA 路由陷阱

`GET /api/v1/memo/` 本应返回笔记列表，但被前端 SPA 的 catch-all 路由拦截，返回的是 HTML 页面。实际可用端点是：

> `GET /api/v1/memo/latest_updated_desc` ✅

### 3. Token 解析陷阱

access_token 包含 `|` 字符（如 `18951205|xxxx`），`json.loads()` 可能误解析，必须用管道方式读取。

## 🚀 快速开始

```bash
pip install -r requirements.txt  # 无额外依赖，仅需 Python 标准库
```

```python
from flomo_api import FlomoClient

# 登录
client = FlomoClient("your_email@example.com", "your_password")

# 读取最新 5 条笔记
memos = client.get_latest_memos_text(5)
for m in memos:
    print(f"【{m['created_at']}】{m['content'][:80]}")
    print(f"  标签: {m['tags']}")
```

或命令行直接使用：

```bash
export FLOMO_EMAIL="your_email"
export FLOMO_PASSWORD="your_password"
python flomo_api.py
```

## 📡 可用 API 端点

| 端点 | 说明 | 状态 |
|------|------|------|
| `POST /user/login_by_email` | 邮箱/手机号登录 | ✅ |
| `GET /memo/latest_updated_desc` | 最新200条笔记 | ✅ |
| `GET /tag/tree` | 标签树 | ✅ |
| `GET /user/me` | 用户信息 | ✅ |
| `GET /subscription/` | 订阅信息 | ✅ |
| `GET /memo/` | ~~笔记列表~~ | ❌ SPA 拦截 |

## 🏗️ 项目结构

```
hermes-skills/
├── README.md              # 你正在看的
├── LICENSE                # MIT 协议
├── flomo_api.py           # 独立 Python 客户端（可直接引用）
└── skills/
    └── flomo-read/
        └── SKILL.md       # Hermes Agent 技能文档
```

## 🔬 逆向过程

1. **入口**：`v.flomoapp.com` 加载 `index.*.js`
2. **定位**：在压缩后的 JS 中搜索 `login_by_email`，找到 API base URL
3. **签名**：搜索 `_getSign`，发现 salt 和排序规则
4. **验证**：curl 手工构造请求，逐步验证签名算法
5. **踩坑**：发现 `/memo/` 返回 HTML → 搜索 JS 路由表 → 找到 `latest_updated_desc`

整个逆向过程约 1 小时，用到的工具只有 curl 和浏览器 DevTools。

## ⚠️ 免责声明

- 本项目仅供**学习研究**使用
- API 签名算法可能随 flomo 版本更新而变化
- 请勿用于商业目的或大规模数据抓取
- 使用时请遵守 flomo 的服务条款

## 📄 License

[MIT](LICENSE)

---

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐ Star！**

这会让更多人发现它 🙏

</div>
