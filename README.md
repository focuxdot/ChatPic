# ChatPic

**简体中文** | [English](README.en.md)

ChatPic 为 AI 编程 Agent 提供简单的图片生成与编辑 Skill。安装 Skill 后，只需用自然语言描述需求，即可获得本地 PNG 图片——无需注册账号、订阅服务、配置环境变量或提供个人 API Key。

适用于 Hermes、Claude Code、OpenClaw 等兼容 Agent Skills 的客户端。

## 功能

- 文生图
- 基于参考图编辑
- 支持中文和英文触发词
- 每次请求通过 `gpt-image-2` 生成一张图片
- 无第三方依赖的 Python 客户端

## 仓库结构

```text
chatpic/
├── skills/chatpic/
│   ├── SKILL.md
│   └── scripts/chatpic.py
├── tests/test_chatpic.py
├── LICENSE
├── README.md
└── README.en.md
```

可分发的 Skill 位于 `skills/chatpic` 目录。仓库文档和测试放在 Skill 目录之外，不会占用 Agent 上下文。

## 安装

### 方式一：让 Agent 安装（推荐）

把下面这句话直接发给 Claude Code、Codex、OpenClaw、Hermes 等 Agent：

```text
请帮我安装 ChatPic Skill：https://github.com/focuxdot/ChatPic
```

### 方式二：在终端安装

```bash
npx -y skills add focuxdot/ChatPic --skill chatpic --global
```

安装器会识别本机的 Agent，并将 ChatPic 安装到对应的全局 Skill 目录。需要 Node.js 18 或更高版本。

## 使用

直接用自然语言提出需求即可，不必特意提到 ChatPic：

```text
帮我生一张图：一只橙色机械猫在操作 AI Agent，方形构图。
```

```text
把这张产品照片的背景换成极简白色摄影棚。
```

```text
Create a clean 16:9 hero image for an AI developer tool.
```

ChatPic 也支持封面、缩略图、海报、横幅、文章插图、产品图、头像、壁纸、背景替换、物体移除、局部重绘、扩图和风格转换等需求。

## 开发

需要 Python 3.10 或更高版本。运行离线测试：

```bash
python3 -m unittest discover -s tests -v
```

发布前，请使用兼容的 Agent Skills 验证工具检查 Skill。

客户端文档：

- [Hermes Skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)
- [Claude Code Skills](https://code.claude.com/docs/en/slash-commands)
- [OpenClaw Skills](https://docs.openclaw.ai/skills)

## 许可证

MIT
