---
name: flomo-read
description: 读取 flomo 浮墨笔记 — 登录、获取笔记列表、搜索笔记。通过逆向 flomo Web API 实现。
---

# flomo 笔记读取

## 核心原理

flomo 新版 Web API（GET 请求）大部分端点被 SPA 路由覆盖，但通过逆向 JS 源码找到了签名算法和可用端点。

### API Base URL
- `https://flomoapp.com/api/v1`
- 大部分 GET 端点可用，但 `/memo/`（列表）被 SPA 拦截返回 HTML
- **可用替代端点**：`/memo/latest_updated_desc`（返回最新200条笔记，按更新时间倒序）

### 签名算法

从 JS 源码（`chunk-core.*.js`）逆向出的签名逻辑：

```python
import hashlib

def get_sign(params):
    """flomo API 签名"""
    sorted_keys = sorted(params.keys())
    parts = []
    for key in sorted_keys:
        val = params[key]
        if val is None:
            continue
        if isinstance(val, list):
            val.sort()
            for v in val:
                parts.append(f"{key}[]={v}&")
        else:
            parts.append(f"{key}={val}&")
    query = "".join(parts)[:-1]  # 去掉末尾 &
    salt = "dbbc3dd73364b4084c3a69346e0ce2b2"
    return hashlib.md5((query + salt).encode()).hexdigest()
```

### 公共参数

每个 API 请求都需要带上：
- `timestamp`: 当前 unix 时间戳
- `api_key`: `flomo_web`
- `app_version`: `2.0`
- `platform`: `web`
- `sign`: 上述签名算法计算结果

### 认证

- 登录接口：`POST /user/login_by_email`
- 登录参数：`email`（手机号或邮箱）+ `password` + 公共参数 + sign
- 登录返回 `access_token`（格式如 `18951206|SYxnkF...e3oqs85upo`，49字符）
- ⚠️ **注意**：access_token 中包含 `|` 字符，Python 的 `json.loads` 可能将某些字节解析为 Ellipsis，必须用 `json.load(sys.stdin)` 方式从 curl 管道读取

### 登录示例

```python
import hashlib, time, json

ts = int(time.time())
params = {
    "email": "18811368179",
    "password": "27008899",
    "timestamp": ts,
    "api_key": "flomo_web",
    "app_version": "2.0",
    "platform": "web"
}
sign = get_sign(params)
params["sign"] = sign

# curl 登录，用管道给 python 解析（避免 access_token 中的特殊字符问题）
body = json.dumps(params)
result = terminal(command=f"""
curl -s 'https://flomoapp.com/api/v1/user/login_by_email' \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{body}' 2>&1 | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])"
""")
access_token = result.get("output", "").strip()
```

### 可用 GET 端点

| 端点 | 说明 |
|------|------|
| `/memo/latest_updated_desc` | 最新200条笔记（按更新时间倒序）✅ 主力端点 |
| `/tag/tree` | 标签树 |
| `/tag/updated/` | 标签更新列表 |
| `/notification/mine` | 通知 |
| `/login_device` | 登录设备 |
| `/incoming_webhook` | API webhook 信息 |
| `/emoji` | emoji 列表 |
| `/biz/config` | 业务配置 |
| `/subscription/` | 订阅信息 |
| `/user/me` | 用户信息（注意此端点跳过额外参数，只需 timestamp） |

### 不可用端点（被 SPA 拦截）

- `/memo/` — 返回 HTML 而非 JSON，需用 `/memo/latest_updated_desc` 替代
- `/memo/{slug}/revisions` — 同样被拦截

### 读取笔记示例

```python
ts = int(time.time())
params = {"timestamp": ts, "api_key": "flomo_web", "app_version": "2.0", "platform": "web"}
sign = get_sign(params)
qs = "&".join(f"{k}={params[k]}" for k in sorted(params.keys())) + f"&sign={sign}"

# 保存到文件再解析（JSON 可能很大，含特殊字符）
result = terminal(command=f"""
curl -s 'https://flomoapp.com/api/v1/memo/latest_updated_desc?{qs}' \
  -H 'Accept: application/json' \
  -H 'Authorization: Bearer {access_token}' \
  -o /tmp/flomo_memos.json \
  -w '%{{http_code}}'
""")
```

### 笔记数据结构

```json
{
  "content": "<p>HTML格式内容</p>",
  "creator_id": 37966,
  "source": "ios|web|android|api",
  "tags": ["标签1"],
  "pin": 0,
  "created_at": "2026-05-09 21:28:09",
  "updated_at": "2026-05-09 21:28:17",
  "slug": "MjM1ODQzOTM3",
  "files": [
    {
      "type": "recorded",
      "seconds": 125,
      "content": "语音转文字内容",
      "url": "https://flomo.oss-cn-shanghai.aliyuncs.com/..."
    }
  ]
}
```

## 用户账号信息

- 昵称：地平线
- Pro 会员到期：2026-12-01
- slug：Mzc5NjY

## 踩坑记录

1. **access_token 解析陷阱**：token 中含 `|` 和特殊字符，Python `json.loads()` 从字符串变量解析可能出错（Ellipsis 问题），必须用 `json.load(sys.stdin)` 从管道读取
2. **`/memo/` 端点被 SPA 拦截**：所有 GET 到 `/api/v1/memo/` 的请求返回 HTML，不是 JSON。必须用 `/memo/latest_updated_desc` 替代
3. **v.flomoapp.com 返回 403**：新版 Web SPA 对 headless Chrome 返回 403（检测 HeadlessChrome UA），无法通过浏览器自动化读取
4. **签名 salt**：`dbbc3dd73364b4084c3a69346e0ce2b2`，从 JS 源码 `_getSign` 方法提取
5. **access_token 有效期**：每次登录获取新 token，token 可能有时效限制，建议每次读取前重新登录获取
