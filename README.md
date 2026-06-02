# Hardlink UI v2

<p align="center">
  A focused hardlink management Web UI for Linux and NAS media libraries.
</p>

<p align="center">
  一个面向 Linux / NAS 媒体库场景的硬链接管理 Web UI。
</p>

<p align="center">
  <img alt="Platform" src="https://img.shields.io/badge/platform-Linux%20%7C%20NAS-1f6feb">
  <img alt="Runtime" src="https://img.shields.io/badge/runtime-Python%20%2B%20Flask-0f766e">
  <img alt="Storage" src="https://img.shields.io/badge/storage-SQLite-c2410c">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-black">
</p>

---

## 中文简介

Hardlink UI v2 是一个轻量、直接、可自托管的 Web UI，用来帮助 Linux / NAS 用户管理硬链接相关操作。它适合媒体下载目录和媒体库目录分离的场景，提供预设目录对、任务记录查看、硬链接组扫描，以及受控范围内的单条 `unlink` 管理能力。

这个项目的目标不是“自动接管整个文件系统”，而是把高频硬链接维护工作变得更可见、更安全、更容易交给普通 NAS 用户使用。

### 这个项目适合谁

- 在 Linux、Debian、Ubuntu、Unraid、TrueNAS、群晖 Docker 等环境维护媒体库的人
- 需要把下载目录内容以硬链接方式整理到电影 / 剧集库的人
- 不想每次都靠命令行处理 inode、路径和删除行为的人
- 想把操作限制在明确白名单目录内，而不是给 Web UI 整盘权限的人

### 核心价值

- 聚焦硬链接工作流，而不是做一个泛文件管理器
- 保留文件系统真实语义，不掩盖 `hardlink` / `unlink` 的实际行为
- 对 NAS / 多目录挂载更友好，适合作为自托管工具部署
- 打包简单，适合 Docker Compose 直接落地

### Linux / NAS 典型使用场景

```text
/mnt/media/downloads
/mnt/media/library/movies
/mnt/media/library/tv
```

典型流程：

1. 下载器或整理器把文件写入下载目录
2. 你在 Hardlink UI 中配置源目录和目标目录预设
3. 在同一文件系统内创建硬链接，让同一个 inode 出现在多个路径
4. 媒体库读取整理后的目标路径，而原始下载路径仍可保留

重要前提：

- 硬链接只在同一文件系统内有效
- 跨盘、跨挂载点、跨文件系统不会形成真正的硬链接
- Docker 容器必须挂载真实媒体目录，否则 UI 看不到文件

### 安全边界

这个项目当前刻意保持边界清晰：

- 所有路径操作都应限制在 `ALLOWED_ROOTS` 白名单内
- “删除”语义是对某一条路径执行 `unlink`，不是删除所有硬链接副本
- 不在这个版本里引入认证，也不假装认证已经解决路径配置风险
- 不建议把整个根目录或无关共享目录加入白名单
- 不建议把容器挂载成超出实际需要的大范围目录

当前明确不做：

- 不修改现有硬链接创建行为
- 不修改现有删除行为
- 不在这个 PR 中引入认证、用户系统、多租户
- 不负责跨文件系统迁移或自动整理全库

### 功能概览

- 任务记录查看
- 预设源目录 / 目标目录管理
- 硬链接组扫描与展示
- 对目标路径执行单条 `unlink`
- SQLite 持久化任务和 UI 配置

### 快速安装

#### 方式 1：Docker Compose

```bash
git clone https://github.com/akl1004/hardlink-ui-v2.git
cd hardlink-ui-v2
mkdir -p data
cp .env.example .env
cp presets.example.json data/presets.json
docker compose up -d --build
```

默认访问地址：

```text
http://<your-server-ip>:18120
```

如果你修改了 `APP_PORT`，对外访问端口也会同步变化。

#### 方式 2：本地 Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
mkdir -p data
cp presets.example.json data/presets.json
python app.py
```

### Docker Compose 用法

仓库自带 `docker-compose.yml`，但首次部署前请至少完成两件事：

1. 修改 `.env` 中的 `ALLOWED_ROOTS`
2. 修改 `docker-compose.yml` 中的主机目录挂载

启动：

```bash
docker compose up -d --build
```

查看日志：

```bash
docker compose logs -f
```

停止：

```bash
docker compose down
```

### 配置示例

#### `.env`

```env
APP_PORT=18120
DB_PATH=/data/hardlink.db
ALLOWED_ROOTS=/mnt/media/downloads,/mnt/media/library
```

#### `docker-compose.yml`

```yaml
services:
  hardlink-ui:
    build: .
    ports:
      - "${APP_PORT:-18120}:${APP_PORT:-18120}"
    volumes:
      - ./data:/data
      - /mnt/media/downloads:/mnt/media/downloads
      - /mnt/media/library:/mnt/media/library
```

#### `data/presets.json`

```json
{
  "pairs": [
    {
      "name": "Movies",
      "src_root": "/mnt/media/downloads/movies",
      "dst_root": "/mnt/media/library/movies"
    },
    {
      "name": "TV",
      "src_root": "/mnt/media/downloads/tv",
      "dst_root": "/mnt/media/library/tv"
    }
  ],
  "target_shortcuts": ["Movies", "TV Shows", "Anime", "Unsorted"]
}
```

### 项目结构建议

```text
hardlink-ui-v2/
├── app.py
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── presets.example.json
└── data/
    └── presets.json
```

### 常见问题

#### 页面打开了，但看不到文件

- 检查 `docker-compose.yml` 是否正确挂载了主机目录
- 检查 `.env` 中的 `ALLOWED_ROOTS` 是否与挂载路径一致
- 检查 `data/presets.json` 中的路径是否位于白名单内

#### 出现权限错误

- 确认容器运行用户对挂载目录具有读写权限
- 如果你的 NAS 使用自定义 `PUID` / `PGID`，请按环境调整 Compose

#### 为什么不能跨盘创建硬链接

- 因为硬链接本质上是单一文件系统内的 inode 链接机制

### Screenshots

后续可以在这里补充：

- 首页
- 任务记录页
- 硬链接管理弹窗
- 预设配置示例

---

## English Overview

Hardlink UI v2 is a lightweight, self-hostable web UI for Linux and NAS users who rely on hardlinks in media library workflows. It provides preset source and destination pairs, job history viewing, hardlink group scanning, and path-scoped `unlink` management within explicitly allowed directories.

The project is designed to make repetitive hardlink maintenance more visible and easier to operate without pretending to be a full filesystem automation layer.

### Who This Is For

- people running Linux, Debian, Ubuntu, Unraid, TrueNAS, Synology Docker, or similar NAS setups
- users who organize downloaded media into movie or TV libraries with hardlinks
- operators who want a UI instead of repeating inode and path operations in a shell
- self-hosters who prefer explicit directory boundaries over broad disk access

### Why It Exists

- it focuses on hardlink workflows instead of becoming a generic file manager
- it keeps real filesystem semantics visible, including the difference between `hardlink` and `unlink`
- it fits NAS-style mounted directory layouts well
- it is simple to package and deploy with Docker Compose

### Typical Linux / NAS Use Case

```text
/mnt/media/downloads
/mnt/media/library/movies
/mnt/media/library/tv
```

A common flow looks like this:

1. A downloader or organizer writes files into a downloads directory.
2. You configure source and destination presets in Hardlink UI.
3. Hardlinks are created within the same filesystem so one inode can appear at multiple paths.
4. Your media library reads from the organized destination path while the original download path can still remain in place.

Key constraints:

- hardlinks only work within the same filesystem
- cross-disk or cross-filesystem paths do not create true hardlinks
- the container must mount the real media directories you want the UI to access

### Safety Boundaries

This project intentionally keeps its boundaries explicit:

- all path operations should stay inside the `ALLOWED_ROOTS` whitelist
- delete behavior means unlinking one path entry, not removing every linked copy
- this version does not introduce authentication
- you should not add your entire root filesystem or unrelated shares to the whitelist
- you should not mount more host directories than the app actually needs

Explicit non-goals:

- no changes to current hardlink creation behavior
- no changes to current delete behavior
- no authentication, user system, or multi-tenant layer in this PR
- no cross-filesystem migration or full-library automation

### Features

- job history viewing
- preset source and destination management
- hardlink group scanning and display
- path-level `unlink` handling for hardlinked targets
- SQLite-backed persistence for jobs and UI settings

### Quick Start

#### Option 1: Docker Compose

```bash
git clone https://github.com/akl1004/hardlink-ui-v2.git
cd hardlink-ui-v2
mkdir -p data
cp .env.example .env
cp presets.example.json data/presets.json
docker compose up -d --build
```

Default URL:

```text
http://<your-server-ip>:18120
```

If you change `APP_PORT`, the exposed port changes with it.

#### Option 2: Local Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
mkdir -p data
cp presets.example.json data/presets.json
python app.py
```

### Docker Compose Usage

The repository ships with a `docker-compose.yml`, but before first use you should at least:

1. update `ALLOWED_ROOTS` in `.env`
2. update the host path mounts in `docker-compose.yml`

Start:

```bash
docker compose up -d --build
```

Logs:

```bash
docker compose logs -f
```

Stop:

```bash
docker compose down
```

### Configuration Examples

#### `.env`

```env
APP_PORT=18120
DB_PATH=/data/hardlink.db
ALLOWED_ROOTS=/mnt/media/downloads,/mnt/media/library
```

#### `docker-compose.yml`

```yaml
services:
  hardlink-ui:
    build: .
    ports:
      - "${APP_PORT:-18120}:${APP_PORT:-18120}"
    volumes:
      - ./data:/data
      - /mnt/media/downloads:/mnt/media/downloads
      - /mnt/media/library:/mnt/media/library
```

#### `data/presets.json`

```json
{
  "pairs": [
    {
      "name": "Movies",
      "src_root": "/mnt/media/downloads/movies",
      "dst_root": "/mnt/media/library/movies"
    },
    {
      "name": "TV",
      "src_root": "/mnt/media/downloads/tv",
      "dst_root": "/mnt/media/library/tv"
    }
  ],
  "target_shortcuts": ["Movies", "TV Shows", "Anime", "Unsorted"]
}
```

### Suggested Repository Layout

```text
hardlink-ui-v2/
├── app.py
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── presets.example.json
└── data/
    └── presets.json
```

### Common Issues

#### The UI opens but files do not appear

- confirm your host directories are mounted in `docker-compose.yml`
- confirm `ALLOWED_ROOTS` matches those mounted paths
- confirm `data/presets.json` points to paths inside the whitelist

#### Permission errors

- make sure the container user can read and write the mounted directories
- if your NAS uses custom `PUID` / `PGID` values, adjust Compose for your environment

#### Why hardlinks do not work across disks

- because hardlinks are an inode-level feature within a single filesystem

### Screenshots

Suggested placeholders for future screenshots:

- home page
- job history view
- hardlink management dialog
- preset configuration example

## License

MIT

## Community

- [Contributing](./CONTRIBUTING.md)
- [Security](./SECURITY.md)
