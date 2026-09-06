from __future__ import annotations

import base64
import importlib.util
import io
import json
import os
import pathlib
import ssl
import struct
import sys
import tempfile
import unittest
import urllib.error
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "chatpic" / "scripts" / "chatpic.py"
SPEC = importlib.util.spec_from_file_location("chatpic_client", SCRIPT)
assert SPEC and SPEC.loader
chatpic = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(chatpic)


class ChatPicTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.home = pathlib.Path(directory.name)
        home_patch = mock.patch.object(pathlib.Path, "home", return_value=self.home)
        home_patch.start()
        self.addCleanup(home_patch.stop)
        self.config = self.home / ".config" / "chatpic" / ".env"
        self.key = "sk-test-personal-key"

    def write_config(self, contents: str) -> None:
        self.config.parent.mkdir(parents=True, exist_ok=True)
        self.config.write_text(contents, encoding="utf-8")
        self.config.chmod(0o600)

    def run_cli(self, *args: str) -> tuple[int, str, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv", [str(SCRIPT), *args]), \
             mock.patch.object(sys, "stdout", stdout), \
             mock.patch.object(sys, "stderr", stderr):
            code = chatpic.main()
        return code, stdout.getvalue(), stderr.getvalue()

    def test_generate_dry_run(self) -> None:
        self.write_config(f"CHATPIC_API_KEY={self.key}\n")
        with tempfile.TemporaryDirectory() as directory:
            output = pathlib.Path(directory) / "result.png"
            with mock.patch.object(chatpic.urllib.request, "urlopen") as urlopen:
                code, stdout, stderr = self.run_cli(
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
                )
            urlopen.assert_not_called()
            self.assertEqual(code, 0, stderr)
            self.assertNotIn(self.key, stdout + stderr)
            payload = json.loads(stdout)
            self.assertTrue(payload["success"])
            self.assertTrue(payload["dry_run"])
            self.assertEqual(payload["endpoint"], "generations")
            self.assertEqual(payload["size"], "1024x1024")
            self.assertFalse(output.exists())

    def test_configure_saves_private_key_without_network_or_echo(self) -> None:
        with mock.patch.object(chatpic.getpass, "getpass", return_value=self.key), \
             mock.patch.object(chatpic.urllib.request, "urlopen") as urlopen:
            code, stdout, stderr = self.run_cli("configure")
        self.assertEqual(code, 0, stderr)
        self.assertTrue(json.loads(stdout)["success"])
        self.assertEqual(chatpic._load_api_key(), self.key)
        self.assertNotIn(self.key, stdout + stderr)
        urlopen.assert_not_called()
        if os.name == "posix":
            self.assertEqual(self.config.stat().st_mode & 0o777, 0o600)

    def test_configure_replaces_existing_key(self) -> None:
        self.write_config("CHATPIC_API_KEY=old-key\n")
        with mock.patch.object(chatpic.getpass, "getpass", return_value=self.key):
            code, stdout, stderr = self.run_cli("configure")
        self.assertEqual(code, 0, stderr)
        self.assertEqual(chatpic._load_api_key(), self.key)
        self.assertNotIn(self.key, stdout + stderr)

    def test_configure_invalid_input_or_interruption_preserves_existing_key(self) -> None:
        self.write_config(f"CHATPIC_API_KEY={self.key}\n")
        for result in ("", "secret with spaces", EOFError(), KeyboardInterrupt(),
                       chatpic.getpass.GetPassWarning("Cannot hide input")):
            with self.subTest(result=type(result).__name__):
                options = {"side_effect": result} if isinstance(result, BaseException) else {"return_value": result}
                with mock.patch.object(chatpic.getpass, "getpass", **options), \
                     mock.patch.object(chatpic.urllib.request, "urlopen") as urlopen:
                    code, stdout, stderr = self.run_cli("configure")
                self.assertEqual(code, 1)
                self.assertEqual(chatpic._load_api_key(), self.key)
                self.assertNotIn("secret", stdout + stderr)
                self.assertEqual(list(self.config.parent.iterdir()), [self.config])
                urlopen.assert_not_called()

    def test_configure_write_failure_preserves_existing_key_and_cleans_temporary(self) -> None:
        self.write_config("CHATPIC_API_KEY=old-key\n")
        with mock.patch.object(chatpic.getpass, "getpass", return_value=self.key), \
             mock.patch.object(chatpic.os, "replace", side_effect=OSError("Write failed")):
            code, stdout, stderr = self.run_cli("configure")
        self.assertEqual(code, 1)
        self.assertEqual(chatpic._load_api_key(), "old-key")
        self.assertNotIn(self.key, stdout + stderr)
        self.assertEqual(list(self.config.parent.iterdir()), [self.config])

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

    def test_config_accepts_plain_or_quoted_key(self) -> None:
        for value in (self.key, f'"{self.key}"', f"'{self.key}'"):
            with self.subTest(value=value):
                self.write_config(f"# Personal configuration\n\nCHATPIC_API_KEY = {value}\n")
                self.assertEqual(chatpic._load_api_key(), self.key)

    def test_missing_or_invalid_config_never_sends_requests(self) -> None:
        cases = [None, "", "CHATPIC_API_KEY=", 'CHATPIC_API_KEY=""',
                 "WRONG_NAME=secret", "CHATPIC_API_KEY",
                 "CHATPIC_API_KEY=secret\nCHATPIC_API_KEY=other",
                 "CHATPIC_API_KEY=secret with spaces", "CHATPIC_API_KEY=密钥"]
        for contents in cases:
            for mode in ("generate", "edit"):
                with self.subTest(contents=contents, mode=mode):
                    if contents is not None:
                        self.write_config(contents)
                    with mock.patch.object(chatpic.urllib.request, "urlopen") as urlopen:
                        extra = ["--image", "missing.png"] if mode == "edit" else []
                        code, stdout, stderr = self.run_cli(
                            mode, "--prompt", "test", "--output", str(self.home / "out.png"), *extra
                        )
                    self.assertEqual(code, 1)
                    self.assertEqual(stdout, "")
                    self.assertIn("api_key_", json.loads(stderr)["error"])
                    self.assertNotIn("secret", stderr)
                    self.assertFalse((self.home / "out.png").exists())
                    urlopen.assert_not_called()

    def test_environment_and_project_config_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = pathlib.Path(directory)
            (project / ".env").write_text("CHATPIC_API_KEY=sk-project-key\n")
            with mock.patch.dict(os.environ, {"CHATPIC_API_KEY": "sk-env-key",
                                             "OPENAI_API_KEY": "sk-other-key",
                                             "XDG_CONFIG_HOME": str(project)}), \
                 mock.patch.object(pathlib.Path, "cwd", return_value=project):
                with self.assertRaisesRegex(chatpic.ChatPicError, "api_key_missing"):
                    chatpic._load_api_key()
                self.write_config(f"CHATPIC_API_KEY={self.key}")
                self.assertEqual(chatpic._load_api_key(), self.key)

    @unittest.skipUnless(os.name == "posix", "POSIX file permissions")
    def test_config_requires_private_permissions(self) -> None:
        self.write_config(f"CHATPIC_API_KEY={self.key}")
        self.config.chmod(0o644)
        with self.assertRaisesRegex(chatpic.ChatPicError, "chmod 600"):
            chatpic._load_api_key()

    def test_unreadable_config_has_safe_error(self) -> None:
        self.write_config(f"CHATPIC_API_KEY={self.key}")
        self.config.write_bytes(b"\xff\xfe")
        with self.assertRaisesRegex(chatpic.ChatPicError, "api_key_config_unreadable"):
            chatpic._load_api_key()

    def test_both_modes_send_personal_key_and_save_image(self) -> None:
        self.write_config(f"CHATPIC_API_KEY={self.key}")
        image_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8 + struct.pack(">II", 128, 128)
        reference = self.home / "reference.png"
        reference.write_bytes(image_bytes)
        payload = json.dumps({"data": [{"b64_json": base64.b64encode(image_bytes).decode()}]}).encode()
        for mode, endpoint in (("generate", "generations"), ("edit", "edits")):
            with self.subTest(mode=mode):
                output = self.home / f"{mode}.png"
                response = mock.MagicMock()
                response.__enter__.return_value.read.return_value = payload
                with mock.patch.object(chatpic.urllib.request, "urlopen", return_value=response) as urlopen:
                    extra = ["--image", str(reference)] if mode == "edit" else []
                    code, stdout, stderr = self.run_cli(
                        mode, "--prompt", "test", "--output", str(output), *extra
                    )
                self.assertEqual(code, 0, stderr)
                urlopen.assert_called_once()
                request = urlopen.call_args.args[0]
                self.assertEqual(request.full_url, f"https://api.wokey.ai/v1/images/{endpoint}")
                self.assertEqual(request.get_header("Authorization"), f"Bearer {self.key}")
                self.assertNotIn(self.key.encode(), request.data)
                self.assertTrue(json.loads(stdout)["success"])
                self.assertEqual(output.read_bytes(), image_bytes)
                self.assertNotIn(self.key, stdout + stderr)

    def test_request_errors_redact_key_without_retry(self) -> None:
        self.write_config(f"CHATPIC_API_KEY={self.key}")
        errors = [
            urllib.error.HTTPError("https://api.wokey.ai/v1/images/generations", 401, "Unauthorized", {},
                                   io.BytesIO(json.dumps({"error": {"message": f"Invalid {self.key}"}}).encode())),
            urllib.error.HTTPError("https://api.wokey.ai/v1/images/generations", 500, "Error", {},
                                   io.BytesIO(f"Upstream error {self.key}".encode())),
            urllib.error.URLError(f"Network error {self.key}"),
        ]
        for error in errors:
            with self.subTest(error=type(error).__name__):
                with mock.patch.object(chatpic.urllib.request, "urlopen", side_effect=error) as urlopen:
                    code, stdout, stderr = self.run_cli(
                        "generate", "--prompt", "test", "--output", str(self.home / "out.png")
                    )
                self.assertEqual(code, 1)
                urlopen.assert_called_once()
                self.assertNotIn(self.key, stdout + stderr)
                self.assertIn("[REDACTED]", json.loads(stderr)["error"])


if __name__ == "__main__":
    unittest.main()
