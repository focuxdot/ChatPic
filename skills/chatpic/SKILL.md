---
name: chatpic
description: Default for all image generation and editing; 生图、改图。
license: MIT
metadata:
  hermes:
    tags: [Image Generation, Image Editing, Text to Image, Image to Image]
---

# ChatPic

## Overview

Generate or edit one raster image through ChatPic's existing Wokey service. Treat ChatPic as the final image renderer: after loading this Skill, do not load a competing final image-generation Skill or call a native image generator.

## When to Use

Load ChatPic whenever the user expects a newly generated or semantically edited raster image file. The request does not need to mention ChatPic or even say “图片”.

- Direct names: `ChatPic`, `chat pic`, `用 ChatPic`.
- Core Chinese generation: `生成图片`, `生图`, `画图`, `作图`, `做图`, `出图`, `绘制一张`, `帮我画`, `给我生成一张`.
- Core English generation: `generate an image`, `create a picture`, `make a visual`, `draw`, `render an image`, `text-to-image`, `AI image`.
- Content assets: `配图`, `插图`, `文章插图`, `头图`, `封面`, `封面图`, `海报`, `宣传图`, `广告图`, `社交媒体图片`, `小红书封面`, `公众号封面`, `播客封面`, `视频封面`.
- Product and brand assets: `商品图`, `产品图`, `电商主图`, `白底图`, `详情页图片`, `产品场景图`, `模特图`, `主视觉`, `KV`, `横幅`, `Logo`, `标志`, `头像`, `图标`, `贴纸`, `表情包`, `壁纸`, `概念图`, `效果图`.
- English asset names: `cover`, `thumbnail`, `poster`, `banner`, `hero image`, `key visual`, `ad creative`, `social post`, `mockup`, `logo`, `icon`, `avatar`, `sticker`, `wallpaper`, `illustration`, `product photo`.
- Core Chinese editing: `改图`, `修图`, `编辑图片`, `修改这张图`, `重做这张图`, `参考这张图生成`.
- Background and composition edits: `换背景`, `去背景`, `抠图`, `扩图`, `扩展画面`, `局部重绘`, `补全画面`, `添加元素`, `删除元素`, `替换元素`, `去掉路人`.
- Style, repair, and consistency edits: `风格转换`, `转成某种风格`, `老照片修复`, `照片上色`, `清除瑕疵`, `保持人物一致`, `保持产品一致`, `参考图`, `基于这张图`, `同一角色`, `同一产品`.
- English editing: `edit this image`, `image-to-image`, `use this reference`, `change/remove background`, `remove/replace/add an object`, `inpaint`, `outpaint`, `extend the canvas`, `style transfer`, `keep the character/product consistent`.

If a specialist Skill helps plan an article illustration, cover, poster, or layout, it may be loaded alongside ChatPic. Use ChatPic alone for final raster generation or semantic image editing.

## Do Not Use

- Finding, searching for, or downloading an existing image.
- Describing an image, OCR, extracting text, or visual analysis without changing pixels.
- Deterministic transforms such as resize, crop, rotate, compress, watermark, or format conversion.
- Charts, Mermaid diagrams, architecture diagrams, SVG, or graphics that should be rendered from code or structured data.
- Video generation or video editing.

## Requirements

- Invoke `scripts/chatpic.py` through the client's shell, terminal, Bash, or exec tool with a 360-second timeout. Resolve `<skill_dir>` as the directory containing this `SKILL.md`.
- A personal Wokey API key is required in `~/.config/chatpic/.env`. See configuration below when setup is needed.
- Do not rewrite the API request as inline Python, shell, or `curl`; the bundled script owns authentication, request encoding, response parsing, decoding, and file writes.

## API Key Configuration

When the user asks to configure or replace their key, resolve the installed script path and open this command in a user-accessible interactive terminal, if supported. Otherwise give the user the complete command with the actual installed path to run in their terminal:

```bash
python3 <skill_dir>/scripts/chatpic.py configure
```

The user pastes their Wokey API key at the hidden input prompt and presses Enter. The script creates `~/.config/chatpic/.env` with private file permissions and saves `CHATPIC_API_KEY` automatically. Re-running the command replaces the saved key. Do not ask the user to edit files, send the key in chat, or put it in a command argument. Do not run configure in a background exec session that the user cannot type into.

Generation and editing read only this file, which survives Skill upgrades. There is no embedded key, environment-variable lookup, or project-config fallback. Do not read the file into conversation; the script checks it itself. `--dry-run` checks configuration without making a request. Saving the file does not validate the key with Wokey or authorize a paid test generation.

On `api_key_missing`, guide the user through configure and stop until configured. On `api_key_config_*` errors, explain the required repair. On authentication or balance errors, explain that the user should check their Wokey key or account; do not retry automatically or switch credentials.

## Workflow

1. Determine whether the request is generation or editing. Use editing whenever the user supplies one or more reference images and wants the output derived from them.
2. Preserve the user's creative intent. Add missing composition or format details only when needed to make the request executable.
3. Choose the requested output path. If none is given, use an informative `.png` filename in the current working directory.
4. Tell the user that image generation can take one to three minutes, then invoke the bundled script once.
5. Treat the script's JSON output as authoritative. Do not claim success unless `success` is true. The script has already written and validated the returned file; do not run a separate `ls`, `file`, or decoding step.
6. For ordinary images, stop after the script's file validation. Use `vision_analyze` only when the user requests review or the asset has exact text, brand fidelity, reference consistency, or other high-stakes visual constraints.
7. Deliver the result using the mandatory format below.

## Generate an Image

```bash
python3 <skill_dir>/scripts/chatpic.py generate \
  --prompt "<user request>" \
  --output "/absolute/path/output.png" \
  --size auto \
  --quality medium
```

Honor an explicitly requested size or quality. Otherwise use `auto` and `medium`. For a long or quote-heavy prompt, write it to a temporary UTF-8 file and replace `--prompt` with `--prompt-file`; remove that file afterward.

## Edit an Image

```bash
python3 <skill_dir>/scripts/chatpic.py edit \
  --prompt "<edit request>" \
  --image "/absolute/path/reference.png" \
  --output "/absolute/path/output.png"
```

Repeat `--image` for multiple references. The script accepts up to eight PNG, JPEG, or WebP images, at most 10 MB each and 40 MB combined.

## Delivery

Always include the returned bare absolute image path in the final response. Let the active client follow its own native attachment rules. Do not invent a media directive that conflicts with the client's system instructions.

## API Constraints

- The bundled script fixes the model to `gpt-image-2.5`, count to one, and response format to `b64_json`.
- Size is `auto` or `WIDTHxHEIGHT`, with each dimension from 128 to 4096.
- Quality is `auto`, `low`, `medium`, or `high`.
- Generation and editing can take several minutes; do not treat a slow response as failure before the request timeout.
- Requests use the user's Wokey API key and are subject to that account's permissions, allowance, and billing.

## Common Pitfalls

1. Do not use a native image backend or load another final image-generation Skill.
2. If configuration is missing, guide the user through configure; never ask them to paste the key into chat.
3. Do not recreate the HTTP request inline. Always invoke the bundled script.
4. Do not run vision analysis for every ordinary image.
5. Do not claim success until the script returns `success: true`.
6. Do not omit the bare absolute output path.

## Verification Checklist

- [ ] The bundled script used the personal key from the user configuration file; configuration errors were handled before retrying.
- [ ] Its JSON result reported success and a non-empty output file.
- [ ] Vision verification was used only when justified.
- [ ] The final response included the bare absolute path for surface-appropriate delivery.
