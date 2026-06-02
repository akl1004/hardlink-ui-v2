# Contributing / 参与贡献

Thanks for your interest in Hardlink UI v2.

感谢你关注 Hardlink UI v2。

This project is still intentionally small and focused. Contributions are welcome, especially when they improve clarity, stability, packaging, and the Linux / NAS hardlink workflow without expanding the product into a generic file manager.

这个项目目前刻意保持小而专注。我们欢迎贡献，尤其欢迎那些能够提升清晰度、稳定性、打包质量，以及 Linux / NAS 硬链接工作流体验的改进，但不希望把它扩展成一个泛用文件管理器。

## Project Priorities / 项目优先级

Good contribution areas:

适合贡献的方向：

- documentation improvements
- packaging and deployment polish
- Linux / NAS path safety improvements
- UI clarity for hardlink-specific operations
- bug fixes that preserve current behavior boundaries

不太适合当前阶段的方向：

- turning the app into a general-purpose file browser
- broad filesystem automation with unclear safety guarantees
- hidden destructive behavior
- large architectural rewrites without a clear operational need
- authentication or user systems unless the project direction changes explicitly

## Ground Rules / 基本规则

Before opening a pull request, please keep these boundaries in mind:

提交 PR 前，请优先遵守这些边界：

- do not silently change hardlink creation behavior
- do not silently change delete behavior
- prefer explicit safety boundaries over convenience shortcuts
- prefer small, reviewable pull requests
- document operational tradeoffs clearly

## Development Notes / 开发说明

Typical local workflow:

常见本地流程：

```bash
cp .env.example .env
mkdir -p data
cp presets.example.json data/presets.json
docker compose up -d --build
```

If you use real media paths during local testing, make sure:

如果你在本地测试时挂载真实媒体目录，请确认：

- your mounted directories match `ALLOWED_ROOTS`
- your test environment does not point at unrelated disks or shares
- you understand whether a path operation is a hardlink action or an unlink action

## Pull Request Guidelines / PR 规范

Please include the following in your PR description when relevant:

如适用，请在 PR 描述中说明：

- what problem is being solved
- whether any filesystem-facing behavior changes
- whether Docker Compose or environment examples changed
- how the change was tested
- what remains intentionally out of scope

## Issues / 提问题建议

Bug reports are most helpful when they include:

高质量问题反馈最好包含：

- OS or NAS environment
- Docker or non-Docker setup
- example source and destination path layout
- expected behavior
- actual behavior
- relevant logs or screenshots

## Code Style / 代码风格

- keep changes small and focused
- preserve existing behavior unless the change is explicitly about behavior
- prefer readable code over clever code
- add comments only when they clarify non-obvious logic

## Security / 安全问题

Please do not open a public issue for a sensitive security problem.

如果是敏感安全问题，请不要直接开公开 issue。

See [SECURITY.md](./SECURITY.md) for the preferred reporting path.
