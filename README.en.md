# ChatPic

[简体中文](README.md) | **English**

ChatPic gives AI coding agents a simple image-generation and image-editing Skill. Install the Skill, ask for an image in natural language, and receive a local PNG—no account, subscription, environment variable, or personal API key required.

It is designed for Agent Skills-compatible clients such as Hermes, Claude Code, and OpenClaw.

## Features

- Text-to-image generation
- Reference-image editing
- Chinese and English trigger phrases
- One image per request through `gpt-image-2`
- Built-in public client credential
- Server-side endpoint restrictions and public-IP quotas
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

### Hermes

```bash
hermes skills install focuxdot/chatpic/skills/chatpic
```

If another final image-generation Skill competes with ChatPic, optionally disable that Skill through `hermes skills config`. ChatPic still works without this tuning.

### Claude Code

```bash
git clone https://github.com/focuxdot/chatpic.git
mkdir -p ~/.claude/skills
cp -R ./chatpic/skills/chatpic ~/.claude/skills/chatpic
```

### OpenClaw

```bash
git clone https://github.com/focuxdot/chatpic.git
openclaw skills install ./chatpic/skills/chatpic --global
```

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

## Public service model

The embedded client credential is intentionally public. It is restricted server-side to image generation and editing and shares the same public-IP trial controls as the Wokey web image service.

- Users do not configure or bring a key.
- The service may reject requests when the public-IP allowance is exhausted or the client IP cannot be determined.
- Limits, availability, models, and commercial terms may change.
- Do not use forwarded-IP headers or other methods to bypass service controls.

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
