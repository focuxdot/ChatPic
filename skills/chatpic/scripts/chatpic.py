#!/usr/bin/env python3
"""Thin, dependency-free client for the ChatPic public image service."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import pathlib
import re
import ssl
import struct
import sys
import tempfile
import urllib.error
import urllib.request
import uuid


API_BASE = "https://api.wokey.ai/v1/images"
# Intentionally public client credential. The service restricts it to image
# endpoints and enforces public-IP quotas server-side.
SERVICE_KEY = "sk-" + "00b16c2c235cbb1b8c4eb0e4d8bc15a4"
MODEL = "gpt-image-2"
TIMEOUT_SECONDS = 300
MAX_IMAGES = 8
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_TOTAL_IMAGE_BYTES = 40 * 1024 * 1024
ALLOWED_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


class ChatPicError(RuntimeError):
    pass


def _prompt(args: argparse.Namespace) -> str:
    if args.prompt_file:
        value = pathlib.Path(args.prompt_file).expanduser().read_text(encoding="utf-8")
    else:
        value = args.prompt or ""
    value = value.strip()
    if not value:
        raise ChatPicError("Prompt must not be empty.")
    return value


def _validate_size(value: str) -> str:
    if value == "auto":
        return value
    match = re.fullmatch(r"(\d{3,4})x(\d{3,4})", value)
    if not match:
        raise ChatPicError("Size must be 'auto' or WIDTHxHEIGHT.")
    width, height = map(int, match.groups())
    if not (128 <= width <= 4096 and 128 <= height <= 4096):
        raise ChatPicError("Image dimensions must each be between 128 and 4096.")
    return value


def _parse_response(raw: bytes) -> dict:
    try:
        payload = json.loads(raw.decode("utf-8", errors="replace"))
    except json.JSONDecodeError as exc:
        preview = raw.decode("utf-8", errors="replace").strip()[:500]
        raise ChatPicError(f"ChatPic returned non-JSON data: {preview}") from exc
    error = payload.get("error")
    if error:
        if isinstance(error, dict):
            code = error.get("code") or "chatpic_error"
            message = error.get("message") or json.dumps(error, ensure_ascii=False)
            raise ChatPicError(f"{code}: {message}")
        raise ChatPicError(str(error))
    return payload


def _request(endpoint: str, body: bytes, content_type: str) -> dict:
    request = urllib.request.Request(
        f"{API_BASE}/{endpoint}",
        data=body,
        headers={
            "Authorization": f"Bearer {SERVICE_KEY}",
            "Content-Type": content_type,
            "Accept": "application/json",
            "User-Agent": "ChatPic-Skill/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(
            request,
            timeout=TIMEOUT_SECONDS,
            context=_ssl_context(),
        ) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        if raw:
            return _parse_response(raw)
        raise ChatPicError(f"ChatPic HTTP error {exc.code}.") from exc
    except urllib.error.URLError as exc:
        raise ChatPicError(f"ChatPic network error: {exc.reason}") from exc
    return _parse_response(raw)


def _ssl_context() -> ssl.SSLContext:
    """Build a verified context on Python installs without a default CA file."""
    candidates: list[str] = []
    if os.environ.get("SSL_CERT_FILE"):
        candidates.append(os.environ["SSL_CERT_FILE"])
    try:
        import certifi  # type: ignore[import-not-found]

        candidates.append(certifi.where())
    except ImportError:
        pass
    candidates.extend(
        [
            "/etc/ssl/cert.pem",
            "/etc/ssl/certs/ca-certificates.crt",
            "/etc/pki/tls/certs/ca-bundle.crt",
        ]
    )
    for value in candidates:
        if value and pathlib.Path(value).is_file():
            return ssl.create_default_context(cafile=value)
    return ssl.create_default_context()


def _multipart(fields: list[tuple[str, str]], images: list[pathlib.Path]) -> tuple[bytes, str]:
    boundary = f"chatpic-{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    marker = f"--{boundary}\r\n".encode()
    for name, value in fields:
        chunks.extend(
            [
                marker,
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                value.encode("utf-8"),
                b"\r\n",
            ]
        )
    for image in images:
        mime = mimetypes.guess_type(image.name)[0] or "application/octet-stream"
        chunks.extend(
            [
                marker,
                (
                    f'Content-Disposition: form-data; name="image"; '
                    f'filename="{image.name}"\r\n'
                ).encode(),
                f"Content-Type: {mime}\r\n\r\n".encode(),
                image.read_bytes(),
                b"\r\n",
            ]
        )
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def _validate_images(values: list[str]) -> list[pathlib.Path]:
    if not values:
        raise ChatPicError("At least one reference image is required for editing.")
    if len(values) > MAX_IMAGES:
        raise ChatPicError(f"At most {MAX_IMAGES} reference images are supported.")
    images: list[pathlib.Path] = []
    total = 0
    for value in values:
        path = pathlib.Path(value).expanduser().resolve()
        if not path.is_file():
            raise ChatPicError(f"Reference image does not exist: {path}")
        if path.suffix.lower() not in ALLOWED_SUFFIXES:
            raise ChatPicError(f"Unsupported reference image type: {path.suffix}")
        size = path.stat().st_size
        if size > MAX_IMAGE_BYTES:
            raise ChatPicError(f"Reference image exceeds 10 MB: {path}")
        total += size
        images.append(path)
    if total > MAX_TOTAL_IMAGE_BYTES:
        raise ChatPicError("Reference images exceed 40 MB combined.")
    return images


def _png_dimensions(data: bytes) -> tuple[int | None, int | None]:
    if len(data) >= 24 and data.startswith(b"\x89PNG\r\n\x1a\n"):
        return struct.unpack(">II", data[16:24])
    return None, None


def _save(payload: dict, output_value: str) -> dict:
    items = payload.get("data") or []
    encoded = items[0].get("b64_json") if items and isinstance(items[0], dict) else None
    if not encoded:
        raise ChatPicError("ChatPic returned no image data.")
    try:
        data = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError) as exc:
        raise ChatPicError("ChatPic returned invalid base64 image data.") from exc
    if not data:
        raise ChatPicError("ChatPic returned an empty image.")

    output = pathlib.Path(output_value).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
        os.replace(temporary, output)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise

    width, height = _png_dimensions(data)
    return {
        "success": True,
        "path": str(output),
        "bytes": len(data),
        "width": width,
        "height": height,
    }


def _dry_run(args: argparse.Namespace, prompt: str, images: list[pathlib.Path]) -> dict:
    return {
        "success": True,
        "dry_run": True,
        "mode": args.mode,
        "endpoint": "generations" if args.mode == "generate" else "edits",
        "prompt_chars": len(prompt),
        "output": str(pathlib.Path(args.output).expanduser().resolve()),
        "size": getattr(args, "size", None),
        "quality": getattr(args, "quality", None),
        "reference_images": len(images),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate or edit one image with ChatPic.")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    def common(subparser: argparse.ArgumentParser) -> None:
        prompts = subparser.add_mutually_exclusive_group(required=True)
        prompts.add_argument("--prompt")
        prompts.add_argument("--prompt-file")
        subparser.add_argument("--output", required=True)
        subparser.add_argument("--dry-run", action="store_true")

    generate = subparsers.add_parser("generate", help="Generate a new image.")
    common(generate)
    generate.add_argument("--size", default="auto", type=_validate_size)
    generate.add_argument("--quality", choices=("auto", "low", "medium", "high"), default="medium")

    edit = subparsers.add_parser("edit", help="Edit one or more reference images.")
    common(edit)
    edit.add_argument("--image", action="append", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        prompt = _prompt(args)
        images = _validate_images(args.image) if args.mode == "edit" else []
        if args.dry_run:
            result = _dry_run(args, prompt, images)
        elif args.mode == "generate":
            body = json.dumps(
                {
                    "model": MODEL,
                    "prompt": prompt,
                    "size": args.size,
                    "quality": args.quality,
                    "n": 1,
                    "response_format": "b64_json",
                },
                ensure_ascii=False,
            ).encode("utf-8")
            result = _save(_request("generations", body, "application/json"), args.output)
        else:
            body, content_type = _multipart(
                [
                    ("model", MODEL),
                    ("prompt", prompt),
                    ("n", "1"),
                    ("response_format", "b64_json"),
                ],
                images,
            )
            result = _save(_request("edits", body, content_type), args.output)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ChatPicError, OSError) as exc:
        print(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
