# ChatPic

[简体中文](README.md) | **English**

ChatPic gives AI coding agents a simple image-generation and image-editing Skill. Install the Skill, configure your own Wokey API key, and ask for an image in natural language to receive a local PNG.

It is designed for Agent Skills-compatible clients such as Hermes, Claude Code, and OpenClaw.

## Features

- Text-to-image generation
- Reference-image editing
- Chinese and English trigger phrases
- One image per request through `gpt-image-2`
- Dependency-free Python client

## Repository layout

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

The distributable Skill is the `skills/chatpic` directory. Repository documentation and tests stay outside the Skill so they do not consume Agent context.

## Install

### Option 1: Ask your agent to install it (recommended)

Send this message directly to Claude Code, Codex, OpenClaw, Hermes, or another compatible agent:

```text
Please install the ChatPic Skill for me: https://github.com/focuxdot/ChatPic
After installation, guide me through configuring my own Wokey API key.
Use this Skill's scripts by default for future image generation and editing.
```

Follow the agent's instructions, paste your key at the terminal's hidden input prompt, and press Enter. The saved key is reused automatically for future requests.

### Option 2: Install from your terminal

```bash
npx -y skills add focuxdot/ChatPic --skill chatpic --global
```

The installer detects your local agent and installs ChatPic into its global Skill directory. Node.js 18 or newer is required.

## Configure your API key

If ChatPic is already installed, or you want to replace your key, tell your agent:

```text
Help me configure my ChatPic API key.
```

The agent will open the interactive configuration command or provide a command ready to run in your local terminal. Paste your key and press Enter; file creation, saving, and permissions are handled automatically. Paste the key at the terminal's hidden input prompt, not into chat.

<details>
<summary>Run the configuration command manually</summary>

Replace `<skill_dir>` with the actual ChatPic installation directory:

```bash
python3 <skill_dir>/scripts/chatpic.py configure
```

Configuration is saved in `~/.config/chatpic/.env` and survives Skill upgrades. Run the same command again to replace your key.

</details>

Saving the key incurs no charges. Your Wokey account determines the allowance and billing for subsequent generation and editing.

## Use

Ask naturally; naming ChatPic is optional:

```text
帮我生一张图：一只橙色机械猫在操作 AI Agent，方形构图。
```

```text
把这张产品照片的背景换成极简白色摄影棚。
```

```text
Create a clean 16:9 hero image for an AI developer tool.
```

ChatPic also triggers on requests for covers, thumbnails, posters, banners, article illustrations, product images, avatars, wallpapers, background replacement, object removal, inpainting, outpainting, and style conversion.

## Development

Requires Python 3.10 or newer. Run the offline test suite with:

```bash
python3 -m unittest discover -s tests -v
```

Validate the Skill with a compatible Agent Skills validator before publishing.

Client documentation:

- [Hermes Skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)
- [Claude Code Skills](https://code.claude.com/docs/en/slash-commands)
- [OpenClaw Skills](https://docs.openclaw.ai/skills)

## License

MIT
