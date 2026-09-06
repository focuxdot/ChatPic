# ChatPic

**简体中文** | [English](README.en.md)

ChatPic 是一个 AI Agent 生图和改图 Skill。安装并配置自己的 Wokey API key 后，直接说出需求即可。

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

把下面这段话直接发给 Claude Code、Codex、OpenClaw、Hermes 等 Agent：

```text
请帮我安装 ChatPic Skill：https://github.com/focuxdot/ChatPic
安装后，请引导我配置自己的 Wokey API key。
以后生图和编辑图片时，请默认使用这个 Skill 的脚本。
```

按照 Agent 的引导，在终端的隐藏输入提示中粘贴 key，按回车即可完成配置。后续自动复用，不需要每次提供。

### 方式二：在终端安装

```bash
npx -y skills add focuxdot/ChatPic --skill chatpic --global
```

安装器会识别本机的 Agent，并将 ChatPic 安装到对应的全局 Skill 目录。需要 Node.js 18 或更高版本。

## 配置 API key

如果已经安装，或需要更换 key，告诉 Agent：

```text
请帮我配置 ChatPic 的 API key。
```

Agent 会打开交互式配置命令，或提供一条可直接在本机终端运行的命令。粘贴 key、按回车即可，文件创建、保存和权限设置全部自动完成。请把密钥粘贴到终端的隐藏输入提示中，不要发到聊天里。

<details>
<summary>手动运行配置命令</summary>

将 `<skill_dir>` 替换为 ChatPic 的实际安装目录：

```bash
python3 <skill_dir>/scripts/chatpic.py configure
```

配置保存在 `~/.config/chatpic/.env`，升级 Skill 不会覆盖。再次运行同一命令可更换 key。

</details>

保存 key 不会产生费用。后续生图、改图的额度和计费以该 Wokey 账户为准。

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
