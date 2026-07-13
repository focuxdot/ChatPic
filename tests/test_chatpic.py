from __future__ import annotations

import base64
import importlib.util
import json
import pathlib
import ssl
import struct
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "chatpic" / "scripts" / "chatpic.py"
SPEC = importlib.util.spec_from_file_location("chatpic_client", SCRIPT)
assert SPEC and SPEC.loader
chatpic = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(chatpic)


class ChatPicTests(unittest.TestCase):
    def test_generate_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = pathlib.Path(directory) / "result.png"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "generate",
                    "--prompt",
                    "a blue circle",
                    "--output",
                    str(output),
                    "--size",
                    "1024x1024",
                    "--quality",
                    "low",
                    "--dry-run",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout)
            self.assertTrue(payload["success"])
            self.assertTrue(payload["dry_run"])
            self.assertEqual(payload["endpoint"], "generations")
            self.assertEqual(payload["size"], "1024x1024")
            self.assertFalse(output.exists())

    def test_size_validation(self) -> None:
        self.assertEqual(chatpic._validate_size("auto"), "auto")
        self.assertEqual(chatpic._validate_size("1024x1536"), "1024x1536")
        with self.assertRaises(chatpic.ChatPicError):
            chatpic._validate_size("64x64")
        with self.assertRaises(chatpic.ChatPicError):
            chatpic._validate_size("square")

    def test_response_error_is_detected(self) -> None:
        raw = json.dumps(
            {"error": {"code": "trial_exhausted", "message": "Try later."}}
        ).encode()
        with self.assertRaisesRegex(chatpic.ChatPicError, "trial_exhausted"):
            chatpic._parse_response(raw)

    def test_png_dimensions(self) -> None:
        png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8 + struct.pack(">II", 1254, 1254)
        self.assertEqual(chatpic._png_dimensions(png), (1254, 1254))
        self.assertEqual(chatpic._png_dimensions(b"not-png"), (None, None))

    def test_base64_sample_is_valid(self) -> None:
        data = b"sample-image-bytes"
        self.assertEqual(base64.b64decode(base64.b64encode(data), validate=True), data)

    def test_ssl_context_is_verified(self) -> None:
        context = chatpic._ssl_context()
        self.assertIsInstance(context, ssl.SSLContext)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(context.check_hostname)

    def test_public_key_is_intentionally_composed(self) -> None:
        self.assertTrue(chatpic.SERVICE_KEY.startswith("sk-"))
        self.assertGreater(len(chatpic.SERVICE_KEY), 20)


if __name__ == "__main__":
    unittest.main()
