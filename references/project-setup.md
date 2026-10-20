# Android project selection and creation

Support both an existing host application and a newly created test application. Do not require a pre-created project.

## Existing project

Inspect the user-provided path and current workspace for a Gradle settings file and a module applying `com.android.application`. If exactly one Android application project is clear, use it and preserve its build language, dependency style, package name, source layout, and architecture. If several application modules are present, ask the user which one is the integration target.

Do not create a replacement project merely because the existing project does not build yet. Environment or dependency failures belong to the environment and artifact workflows.

## No project

If the user says there is no project, or no Android application project can be found, use the current working directory when it is empty. In that case, do not ask for a destination path. Ask for a destination only when the current directory cannot safely contain the new project. The application name and final `applicationId` are user decisions. Resolve them one at a time using the following value-entry interaction:

1. The first response after detecting an empty directory must display the application-name menu. Do not preface or replace it with an open-ended request for project information. Display at least two concrete candidate values derived from the user's request or SDK test context, followed by a final numbered `自己输入` item. If no stronger context exists, use `投屏助手（推荐）`, `Sender SDK Test`, and `自己输入`.
2. Let the user enter a candidate number. If they choose `自己输入`, show a separate prompt where they type the custom value and press Enter. Do not accept free text at the numbered-menu prompt, do not treat an empty Enter as acceptance, and do not apply a timeout default.
3. Validate the selected or typed value immediately. If invalid, explain the validation error and repeat only that field's menu.
4. End the application-name prompt and wait for its answer. Only after the application name is accepted, generate and display at least two `applicationId` candidates from that name and the destination, followed by `自己输入`, then repeat the same numbered interaction for `applicationId`. If no reliable package-name derivation exists, use `com.example.castsender（推荐）`, `com.example.hpplay.sender`, and `自己输入`.

These are value selections, not binary approvals, so they do not use `y/n`. After both values are accepted, display the exact pair and ask one final `确认使用以上应用名和 applicationId 创建工程？[y/n]` approval. If the user answers `n`, return to the value-selection interaction; do not create files. If the request already contains a value, include that exact value as the first candidate rather than silently replacing it. Keep the candidate numbers stable within a prompt and always place `自己输入` last. Never ask `请提供两个信息`, `请提供应用名称和 applicationId`, or any equivalent two-field open question. The destination must be absent or empty. Never generate into a non-empty workspace root.

Use this terminal interaction shape:

```text
请选择应用名称（输入序号）：
1. 投屏助手（推荐）
2. Sender SDK Test
3. 自己输入
>

选择 3 后：
请输入应用名称：
>

请选择 applicationId（输入序号）：
1. com.example.castsender（推荐）
2. com.example.hpplay.sender
3. 自己输入
>

选择 3 后：
请输入 applicationId：
>
```

Ask these in the current Skill terminal session, not in a separate terminal. Do not ask for both fields in one prompt: finish and validate the application name first, then ask for `applicationId`.

Validate first without writing:

```bash
python3 scripts/create_android_project.py \
  --project-dir /path/to/new-project \
  --app-name "Sender SDK Test" \
  --package-name com.example.sendertest \
  --check
```

After the user accepts both values, run the read-only validation and show the exact application name and `applicationId` in the current session. Ask `确认使用以上应用名和 applicationId 创建工程？[y/n]`. Accept only `y` or `n`, case-insensitively. After `y`, create the project with the same exact values and `--confirm`; after `n`, return to the value-selection interaction without writing files:

```bash
python3 scripts/create_android_project.py \
  --project-dir /path/to/new-project \
  --app-name "Sender SDK Test" \
  --package-name com.example.sendertest \
  --confirm
```

Reprompt after empty or any response other than `y` or `n`; do not treat silence as approval. If either value changes after the final summary, run `--check` again and obtain a new `[y/n]` confirmation for the new pair. The generated project is a clean integration target, not a completed SDK demo. It contains one Java application module, a launcher Activity, an external-AAR dependency location, an explicit `androidx.core` dependency required by the AAR, a valid application icon for foreground notifications, least-privilege Manifest merge overrides, and no SDK credentials. It also runs `git init` so ignored credential files can pass onboarding's Git safety check. The environment workflow creates its Gradle Wrapper and installs any missing build tools afterward.

The generated `settings.gradle` retains `google()`, `mavenCentral()`, and `gradlePluginPortal()` and supports optional repository mirrors through `ANDROID_GRADLE_PLUGIN_MIRROR`, `ANDROID_GOOGLE_MAVEN_MIRROR`, and `ANDROID_CENTRAL_MAVEN_MIRROR`. Do not put repository usernames or passwords in the project files.

The defaults are Android Gradle Plugin 8.7.3, `compileSdk`/`targetSdk` 35, and `minSdk` 21. Override them only when the SDK release or test matrix requires another supported baseline.

After selecting or creating the project, inspect it for an existing sender SDK dependency, initialization, credentials, and casting implementation before choosing preflight checks. For an incremental capability request, follow [incremental integration](incremental-integration.md), preserve the working integration, and skip irrelevant artifact acquisition, onboarding, and scope selection. For a new/full integration, run the applicable read-only environment, artifact, and credential checks and complete any required decisions before editing integration code or performing a guarded action.
