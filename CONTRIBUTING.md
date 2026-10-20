# Contributing

Contributions should keep the Skill safe to run, portable across developer machines, and
consistent with the existing sender SDK workflow.

## Before Opening a Pull Request

1. Read `SKILL.md` and the reference document relevant to the change.
2. Keep changes scoped to the requested behavior; preserve existing credential and project
   ownership rules.
3. Run `python3 -m py_compile scripts/*.py` and `git diff --check`.
4. Review `git status` and the staged diff for credentials, generated Android state, AARs,
   private keys, and machine-specific paths.
5. Describe what was tested and what remains unverified without a real receiver, service
   credentials, or Android device.

## Safety Rules

- Do not add credentials, tokens, passwords, verification codes, or private keys to source,
  examples, tests, issue reports, or logs.
- Do not change a host application's existing credential source during an incremental
  integration.
- Do not turn a read-only preflight into a network-mutating operation.
- Do not accept Android SDK licenses, register an application, or send SMS in automated tests.
- Keep callback domains and numeric error codes distinct.
- Avoid adding dependencies when the Python standard library is sufficient.

## Pull Requests

Use a focused title and explain the user-visible behavior. Include:

- the affected Skill/reference/script files;
- the reason for the change;
- validation commands and results;
- any compatibility, privacy, or release-build impact;
- any follow-up that requires a real Android device or receiver.

Please do not include real platform responses or diagnostic output containing app/device data.
