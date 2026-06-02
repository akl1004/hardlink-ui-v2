# Security Policy / 安全说明

## Scope / 适用范围

Hardlink UI v2 is a self-hosted tool that can perform filesystem-related operations inside explicitly mounted and allowed directories.

Hardlink UI v2 是一个自托管工具，会在明确挂载且被允许的目录范围内执行文件系统相关操作。

Because of that, security for this project is closely tied to deployment boundaries:

因此，这个项目的安全性和部署边界强相关：

- directory mounts
- `ALLOWED_ROOTS`
- host file permissions
- operator understanding of `hardlink` and `unlink` semantics

## Current Security Model / 当前安全模型

The current project model is intentionally simple:

当前项目模型刻意保持简单：

- path access should be restricted to `ALLOWED_ROOTS`
- operators are expected to mount only the directories they actually need
- delete behavior is path-level unlink behavior, not bulk media cleanup
- this project does not provide authentication yet

This means the application should be deployed only on trusted private networks or behind your own access controls until authentication exists.

这意味着，在认证机制加入之前，建议只把它部署在受信任的私有网络环境中，或者放在你自己的反向代理 / 访问控制之后。

## Supported Security Work / 当前欢迎的安全改进

Useful security-related contributions include:

欢迎的安全改进方向包括：

- path validation hardening
- clearer operational warnings
- safer defaults in packaging and documentation
- better explanation of deployment boundaries

## Out of Scope for the Current Release / 当前版本暂不处理

- full authentication and user management
- internet-exposed multi-user deployment support
- broad role-based access control

## Reporting a Vulnerability / 漏洞报告方式

If you believe you have found a security vulnerability, please avoid opening a public GitHub issue with exploit details.

如果你认为发现了安全漏洞，请不要直接在公开 GitHub issue 中披露可利用细节。

Preferred approach:

建议方式：

1. Open a private contact path with the maintainer if available.
2. Share a minimal reproduction and impact description.
3. Include deployment assumptions, mounted paths, and whether the issue requires misconfiguration.

如果当前仓库还没有单独的安全邮箱，可以先通过 GitHub 联系维护者，并在公开内容中只描述高层级风险，不要公开利用细节。

## Deployment Advice / 部署建议

- do not expose the app directly to the public internet without an additional access layer
- do not mount more directories than necessary
- do not add `/` or unrelated shared storage to `ALLOWED_ROOTS`
- test changes in a non-production library path first

## Coordinated Fixes / 协调修复

When a valid security issue is confirmed, the preferred path is:

一旦确认安全问题，优先处理方式是：

1. understand the exact boundary failure
2. minimize behavior change outside the fix
3. update documentation if operator safety assumptions need to be clearer
