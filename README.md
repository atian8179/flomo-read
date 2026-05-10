# Hermes Skills

Hermes Agent 自定义技能集合。

## Skills

### [flomo-read](skills/flomo-read/SKILL.md)

读取 flomo 浮墨笔记 —— 通过逆向 flomo Web API 实现登录、获取笔记列表。

- 支持账号密码登录
- 支持读取最新 200 条笔记
- 支持标签树、通知等端点
- 内置 API 签名算法（MD5 + salt）

## 使用

将 `skills/` 目录下的技能复制到 `~/.hermes/skills/` 对应分类目录即可。

## License

MIT
