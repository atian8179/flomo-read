"""
flomo API 逆向 - 非官方 Python 客户端
通过逆向 flomo Web 端 JS 源码，实现笔记读取功能。

⚠️ 仅供学习研究使用，请勿用于商业目的。

Usage:
    from flomo_api import FlomoClient

    client = FlomoClient("your_email", "your_password")
    memos = client.get_latest_memos()
    for m in memos[:5]:
        print(m["created_at"], m["content"][:50])
"""

import hashlib
import json
import re
import time
import html as html_mod
import subprocess


# 从 flomo Web 端 JS 源码（chunk-core.*.js）逆向出的签名 salt
FLOMO_SIGN_SALT = "dbbc3dd73364b4084c3a69346e0ce2b2"
FLOMO_API_BASE = "https://flomoapp.com/api/v1"


def get_sign(params: dict) -> str:
    """
    flomo API 签名算法（逆向自 JS _getSign 方法）
    
    流程：参数按 key 排序 → 拼接 key=value& → 去末尾& → 加 salt → MD5
    """
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
    query = "".join(parts)[:-1]
    return hashlib.md5((query + FLOMO_SIGN_SALT).encode()).hexdigest()


def _build_common_params() -> dict:
    """构建公共请求参数"""
    return {
        "timestamp": int(time.time()),
        "api_key": "flomo_web",
        "app_version": "2.0",
        "platform": "web",
    }


def _curl_json(url: str, method: str = "GET", headers: dict = None, data: dict = None) -> dict:
    """通过 curl 发送请求并解析 JSON 响应"""
    cmd = ["curl", "-s", url, "-w", "\n%{http_code}"]
    if method == "POST":
        cmd.extend(["-X", "POST", "-H", "Content-Type: application/json"])
        if data:
            cmd.extend(["-d", json.dumps(data)])
    if headers:
        for k, v in headers.items():
            cmd.extend(["-H", f"{k}: {v}"])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    lines = result.stdout.strip().rsplit("\n", 1)
    body = lines[0]
    status = int(lines[1]) if len(lines) > 1 else 0

    if status != 200:
        raise Exception(f"HTTP {status}: {body[:200]}")

    # 用管道方式避免 access_token 中的特殊字符问题
    return json.loads(body)


class FlomoClient:
    """flomo 非官方 API 客户端"""

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.access_token: str = ""
        self.user_info: dict = {}
        self._login()

    def _login(self):
        """登录并获取 access_token"""
        params = {
            "email": self.email,
            "password": self.password,
            **_build_common_params(),
        }
        params["sign"] = get_sign(params)

        # ⚠️ access_token 含 | 等特殊字符，必须用管道方式解析
        body = json.dumps(params)
        result = subprocess.run(
            [
                "curl", "-s",
                f"{FLOMO_API_BASE}/user/login_by_email",
                "-X", "POST",
                "-H", "Content-Type: application/json",
                "-d", body,
            ],
            capture_output=True, text=True, timeout=30,
        )
        data = json.loads(result.stdout)
        if data.get("code") != 0:
            raise Exception(f"登录失败: {data.get('message')}")

        self.user_info = data["data"]
        self.access_token = self.user_info["access_token"]

    def _auth_get(self, endpoint: str) -> dict:
        """带认证的 GET 请求"""
        params = _build_common_params()
        params["sign"] = get_sign(params)
        qs = "&".join(f"{k}={params[k]}" for k in sorted(params.keys()))

        url = f"{FLOMO_API_BASE}{endpoint}?{qs}"
        result = subprocess.run(
            ["curl", "-s", url,
             "-H", "Accept: application/json",
             "-H", f"Authorization: Bearer {self.access_token}"],
            capture_output=True, text=True, timeout=30,
        )
        return json.loads(result.stdout)

    def get_latest_memos(self, limit: int = 200) -> list:
        """获取最新笔记（按更新时间倒序，最多200条）"""
        data = self._auth_get("/memo/latest_updated_desc")
        if data.get("code") != 0:
            raise Exception(f"获取笔记失败: {data.get('message')}")
        memos = data.get("data", [])
        return memos[:limit]

    def get_tag_tree(self) -> dict:
        """获取标签树"""
        return self._auth_get("/tag/tree")

    def get_user_info(self) -> dict:
        """获取用户信息"""
        return self.user_info

    @staticmethod
    def strip_html(content: str) -> str:
        """去除 HTML 标签，返回纯文本"""
        content = re.sub(r"<[^>]+>", "", content)
        return html_mod.unescape(content).strip()

    def get_latest_memos_text(self, limit: int = 10) -> list:
        """获取最新笔记的纯文本版本"""
        memos = self.get_latest_memos(limit)
        result = []
        for m in memos:
            text = self.strip_html(m.get("content", ""))
            result.append({
                "content": text,
                "tags": m.get("tags", []),
                "created_at": m.get("created_at", ""),
                "source": m.get("source", ""),
                "has_voice": any(f.get("type") == "recorded" for f in m.get("files", [])),
            })
        return result


if __name__ == "__main__":
    import os

    email = os.environ.get("FLOMO_EMAIL", "")
    password = os.environ.get("FLOMO_PASSWORD", "")

    if not email or not password:
        print("请设置环境变量 FLOMO_EMAIL 和 FLOMO_PASSWORD")
        exit(1)

    client = FlomoClient(email, password)
    print(f"✅ 登录成功: {client.user_info.get('name')} (Pro到期: {client.user_info.get('pro_expired_at')})")

    memos = client.get_latest_memos_text(5)
    print(f"\n最近 {len(memos)} 条笔记:\n")
    for i, m in enumerate(memos, 1):
        voice_tag = " [语音]" if m["has_voice"] else ""
        print(f"【{i}】{m['created_at']} (来自{m['source']}){voice_tag}")
        print(f"   {m['content'][:100]}...")
        print()
