<div align="center">

# 🔓 flomo-read

**让 AI Agent 直接读取你的 flomo 浮墨笔记**

[![GitHub Stars](https://img.shields.io/github/stars/atian8179/flomo-read?style=social)](https://github.com/atian8179/flomo-read)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

</div>

---

## 怎么用？

**就这么简单：**

1. 复制这个仓库地址 👉 `https://github.com/atian8179/flomo-read`
2. 丢给你的 AI Agent（Hermes / OpenClaw），说：「帮我安装这个 skill」
3. 告诉它你的 flomo 手机号/邮箱和密码
4. 搞定！以后直接说「读一下我的 flomo 笔记」就行

**或者你想自己跑：**

```bash
export FLOMO_EMAIL="你的手机号或邮箱"
export FLOMO_PASSWORD="你的密码"
python flomo_api.py
```

## 它能做什么？

- 📖 读取你最新的 flomo 笔记（最多 200 条）
- 🏷️ 获取你的标签树
- 🔍 搜索笔记内容
- 🎙️ 支持语音转写笔记的读取

## 原理

通过逆向 flomo Web 端 JS 源码，提取了 API 签名算法。不需要浏览器，不需要 Selenium，纯 API 调用，稳定可靠。

## 作为 Python 库使用

```python
from flomo_api import FlomoClient

client = FlomoClient("your_email", "your_password")
memos = client.get_latest_memos_text(5)
for m in memos:
    print(m["created_at"], m["content"])
```

## ⚠️ 免责声明

仅供学习研究，请勿用于商业目的或大规模抓取。

## 📄 License

[MIT](LICENSE)

---

<div align="center">

觉得有用？给个 ⭐ Star 吧 🙏

</div>
