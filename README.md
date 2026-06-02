# Hardlink UI v2

Hardlink UI v2 is a lightweight web UI for Linux and NAS media library workflows. It helps you review hardlink job history, manage preset source and destination pairs, and inspect or handle hardlinked files within explicitly allowed directories.

The goal of this project is to provide a simple, self-hostable, Docker-friendly interface for common hardlink maintenance tasks without hiding the underlying filesystem constraints.

## Project Purpose

This project is intended for people who:

- run Linux, Debian, Ubuntu, Unraid, Synology Docker, TrueNAS SCALE, or similar NAS environments
- use hardlinks to move media from download paths into library paths
- want a simple web UI instead of ad-hoc shell commands for reviewing records and managing hardlinked paths
- prefer explicit directory boundaries over broad filesystem access

## Linux / NAS Hardlink Use Case

A typical layout looks like this:

```text
/mnt/media/downloads
/mnt/media/library/movies
/mnt/media/library/tv
```

A common workflow is:

1. A downloader or organizer writes files into a downloads directory.
2. Hardlink UI is configured with source and destination presets.
3. Hardlinks are created within the same filesystem so one inode can appear at multiple paths.
4. Your media library can read the organized destination path while the original download path still exists.

Important notes:

- hardlinks only work within the same filesystem
- cross-disk or cross-filesystem paths will not produce hardlinks
- the Docker container must mount the real media paths you want the UI to see

## Safety Boundaries

This repository intentionally keeps its behavior explicit.

- Operations are restricted to paths under `ALLOWED_ROOTS`.
- Delete actions are path-level `unlink` operations, not bulk removal of all linked copies.
- This project does not add authentication in this release.
- You should avoid adding your whole root filesystem or unrelated shares to `ALLOWED_ROOTS`.
- You should mount only the minimum host directories the app actually needs.

Current non-goals:

- no changes to existing hardlink creation behavior
- no changes to existing delete behavior
- no authentication, user system, or multi-tenant support in this PR
- no cross-filesystem migration or media management automation

## Features

- job and history viewing
- preset source and destination management
- hardlink group scanning and display
- path-level `unlink` management for hardlinked targets
- SQLite-backed persistence for jobs and UI settings

## Installation

### Option 1: Docker Compose

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

### Option 2: Local Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
mkdir -p data
cp presets.example.json data/presets.json
python app.py
```

## Docker Compose Usage

The repository includes a release-oriented `docker-compose.yml`. Before starting it, update:

1. `ALLOWED_ROOTS` in `.env`
2. host path mounts in `docker-compose.yml`

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

## Configuration Examples

### `.env`

```env
APP_PORT=18120
DB_PATH=/data/hardlink.db
ALLOWED_ROOTS=/mnt/media/downloads,/mnt/media/library
```

### `docker-compose.yml`

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

### `data/presets.json`

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

## Suggested Repository Layout

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

## Common Issues

### The UI opens but files do not appear

- confirm your host paths are mounted in `docker-compose.yml`
- confirm `.env` uses `ALLOWED_ROOTS` values that match those mounts
- confirm `data/presets.json` paths are inside the allowed roots

### Permission denied errors

- make sure the container user can read and write the mounted directories
- if your NAS uses custom `PUID` / `PGID` values, adjust the Compose file for your environment

### Why hardlinks do not work across disks

- because hardlinks are an inode feature within a single filesystem

## Screenshots

Placeholder section for future screenshots:

- main page
- history view
- hardlink management dialog
- preset configuration example

## License

MIT
