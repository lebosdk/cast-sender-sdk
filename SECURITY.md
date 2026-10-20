# Security Policy

## Scope

This repository contains a Codex Skill and helper scripts. It may contact the official
HPPlay platform for credential onboarding and the official SDK CDN for AAR acquisition when a
developer explicitly runs the corresponding workflow. It is not a credential vault and must
not contain production secrets.

## Reporting a Vulnerability

Do not open a public issue for a suspected credential leak, authentication flaw, unsafe
network request, or code-execution vulnerability. Use the repository owner's private GitHub
Security Advisory/reporting channel when it is enabled. If private reporting is unavailable,
contact the repository owner privately through the GitHub profile and include:

- a short description and impact;
- affected file, version, and environment;
- reproducible steps or a minimal proof of concept;
- whether any credential or personal data may have been exposed.

Redact tokens, passwords, verification codes, App Secrets, `md5Key`, private keys, phone
numbers, and receiver/device identifiers from the report.

## Credential Exposure

If a secret is committed accidentally, revoke or rotate it at the issuing platform first, then
remove it from the repository history with the repository owner's approved history-rewrite
process. Deleting the working-tree file alone is not sufficient because Git history is
retained by existing clones and remote references.

## Supported Versions

Security fixes target the latest version listed in `VERSION`. When reporting an older version,
include the exact version and whether the issue remains reproducible after updating.
