# Contributing

Contributions should keep the Skills safe to run, portable across developer machines, and
consistent with the existing sender SDK workflow.

## Before Opening a Pull Request

1. Read the platform `SKILL.md` (`android/` or `ios/`) and the reference document relevant
   to the change.
2. Keep changes scoped to the requested behavior; preserve existing credential and project
   ownership rules.
3. Run the checks listed in the repository `README.md` (Development Checks).
4. Review `git status` and the staged diff for credentials, generated Android/Xcode state,
   AARs, xcframeworks, private keys, and machine-specific paths.
5. Describe what was tested and what remains unverified without a real receiver, service
   credentials, or Android/iOS device.

## Safety Rules

- Do not add credentials, tokens, passwords, verification codes, or private keys to source,
  examples, tests, issue reports, or logs.
- Do not change a host application's existing credential source during an incremental
  integration.
- Do not turn a read-only preflight into a network-mutating operation.
- Do not accept Android SDK or Xcode licenses, register an application, or send SMS in
  automated tests.
- Keep callback domains and numeric error codes distinct.
- Avoid adding dependencies: Python scripts use only the standard library, and Ruby scripts
  depend only on `xcodeproj`.

## Pull Requests

Use a focused title and explain the user-visible behavior. Include:

- the affected Skill/reference/script files;
- the reason for the change;
- validation commands and results;
- any compatibility, privacy, or release-build impact;
- any follow-up that requires a real Android/iOS device or receiver.

Please do not include real platform responses or diagnostic output containing app/device data.
