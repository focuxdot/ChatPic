# Security

## Personal API key

ChatPic requires the user's own Wokey API key in `~/.config/chatpic/.env` as `CHATPIC_API_KEY`. It has no embedded credential and does not read API keys from environment variables or project files.

The `configure` command accepts hidden terminal input and saves the key atomically, using file mode `600` on POSIX systems. It refuses input when the terminal cannot hide it. The configuration file contains the key in plaintext. On POSIX systems, the script rejects files accessible to group or other users; set its permissions to `600`. Keep real keys out of chats, source code, and Git. The script does not print the key and redacts it from reported request errors.

Requests use the configured key for image generation and editing at `https://api.wokey.ai/v1/images`. Missing, empty, or invalid configuration stops the script before any request. Account permissions, allowance, billing, routing, and abuse controls are enforced by Wokey; client configuration does not bypass those controls.

## Reporting

Use the repository's private GitHub Security Advisory flow for vulnerabilities. Do not include exploit details, user data, or bypass instructions in a public issue.
