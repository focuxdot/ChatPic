# Security

## Public client credential

ChatPic intentionally contains a public client credential so users can install and use the Skill without configuring a personal secret. The credential is restricted server-side to image endpoints and protected by public-IP quotas.

The presence of this credential in the repository is not, by itself, a credential leak. Please report cases where it can access unrelated endpoints, bypass service controls, expose private data, or gain privileges beyond public image generation and editing.

## Reporting

Use the repository's private GitHub Security Advisory flow for vulnerabilities. Do not include exploit details, user data, or bypass instructions in a public issue.
