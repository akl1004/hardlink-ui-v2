Hardlink UI（Docker 版）

这个包是在你现有 UI 风格基础上扩展的版本：新增“🧰 管理”弹窗，用来扫描并管理所有硬链接文件（包含 MoviePilot/其它应用创建的硬链接）。
UI 仍然保持原来的视觉与交互习惯，只是多了一个弹窗入口。

功能概览
- 📜 记录：原有记录/删除管理（保持不变）
- 🧰 管理：扫描硬链接组（同 inode 多路径），按“稳定 canonical（最短路径 + 字典序）”显示源/目标，并支持对目标路径执行 unlink 删除

重要说明（非常关键）
1) “删除”在管理弹窗里是 unlink：只删除该路径这一条硬链接目录项，其它硬链接仍保留。
2) 硬链接只能在同一文件系统内生效；跨盘只是复制，不会出现在硬链接组。
3) Docker 容器必须挂载你需要管理的目录，否则容器看不到也无法删除。

快速安装（Docker Compose）
1. Upload project to your NAS/Server (e.g. `/opt/hardlink-ui`)
2. Enter directory:
   `cd /opt/hardlink-ui`
3. Create data directory:
   `mkdir -p data`
4. **Configure Env**:
   Copy `.env.example` to `.env` and update `ALLOWED_ROOTS` to match your media paths.
5. **Configure Presets**:
   Copy `presets.example.json` to `data/presets.json` and edit it to define your source/target folders.
6. **Configure Docker**:
   Edit `docker-compose.yml` volumes to map your actual media directories.
7. Start:
   `docker compose up -d --build`
8. Access at `http://<IP>:18120`

## Common Issues
- **Permission Denied**: Ensure the container has write access to your mapped volumes.
- **Empty List**: Check if `ALLOWED_ROOTS` in `.env` matches your docker volumes and `presets.json` paths.
