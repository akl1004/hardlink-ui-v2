import os
import time
import json
import csv
import io
import sqlite3
import shutil
import stat
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from flask import Flask, request, jsonify, render_template, abort, send_file, make_response
from i18n import TRANSLATIONS

APP_PORT = int(os.environ.get("APP_PORT", "18120"))
DB_PATH = os.environ.get("DB_PATH", "/data/hardlink.db")

# 允许操作的根目录白名单（强烈建议只填你需要管理的卷/目录）
# 可用环境变量覆盖：ALLOWED_ROOTS=/vol2/1000,/vol3/1000,/vol5/1000
_env_roots = [p.strip() for p in os.environ.get("ALLOWED_ROOTS", "").split(",") if p.strip()]
if _env_roots:
    ALLOWED_ROOTS = [Path(p) for p in _env_roots]
else:
    ALLOWED_ROOTS = [
        # Path("/vol2/1000"), # Example
    ]


VIDEO_EXT = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".m4v", ".ts", ".m2ts", ".flv", ".webm", ".iso"}
SUB_EXT = {".srt", ".ass", ".ssa", ".vtt", ".sub", ".idx"}


def _resolve(p: Path) -> Path:
    try:
        return p.resolve()
    except Exception:
        return Path(os.path.abspath(str(p)))


def is_under_allowed(p: Path) -> bool:
    pp = _resolve(p)
    for r in ALLOWED_ROOTS:
        rr = _resolve(r)
        try:
            pp.relative_to(rr)
            return True
        except Exception:
            continue
    return False


def safe_resolve(p: str) -> Path:
    if not p:
        abort(400, "path is required")
    pp = _resolve(Path(p))
    if not is_under_allowed(pp):
        abort(403, f"path not allowed: {pp}")
    return pp


def now_ts() -> int:
    return int(time.time())


DB_LOCK = threading.Lock()


def db_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    os.makedirs(Path(DB_PATH).parent, exist_ok=True)
    with DB_LOCK:
        conn = db_conn()
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS link_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at INTEGER NOT NULL,
            op TEXT NOT NULL,
            src TEXT,
            dst TEXT,
            item_type TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT,
            note TEXT
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at INTEGER NOT NULL,
            started_at INTEGER,
            finished_at INTEGER,
            job_type TEXT NOT NULL,
            status TEXT NOT NULL,
            total_files INTEGER NOT NULL DEFAULT 0,
            done_files INTEGER NOT NULL DEFAULT 0,
            message TEXT,
            params_json TEXT
        )
        """)
        # NEW: UI shortcuts config persisted in DB (per preset)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS ui_shortcuts (
            preset_key TEXT PRIMARY KEY,
            base_path TEXT NOT NULL,
            shortcuts_json TEXT NOT NULL,
            updated_at INTEGER NOT NULL
        )
        """)
        conn.commit()
        conn.close()


def db_add_record(op: str, src: str, dst: str, item_type: str, status: str, message: str = "", note: str = ""):
    with DB_LOCK:
        conn = db_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO link_jobs(created_at, op, src, dst, item_type, status, message, note)
            VALUES(?,?,?,?,?,?,?,?)
        """, (now_ts(), op, src, dst, item_type, status, message, note))
        conn.commit()
        conn.close()


def db_list_records(limit: int = 200, offset: int = 0,
                    q: str = "", op: str = "", status: str = "",
                    include_deleted: bool = True) -> Tuple[int, List[Dict[str, Any]]]:
    q = (q or "").strip()
    op = (op or "").strip()
    status = (status or "").strip()

    where = []
    args: List[Any] = []
    
    # User Request: "Don't need to show delete files records [separately], just add note to link file"
    # Filter out explicit deletion records to keep the list clean, as we now track deletion status in the original LINK record.
    # We do this ALWAYS, regardless of include_deleted, to merge the view as requested.
    where.append("(op NOT LIKE 'DELETE_%' AND op != 'UNLINK_MANAGE')")

    if q:
        where.append("(src LIKE ? OR dst LIKE ? OR note LIKE ? OR message LIKE ?)")
        like = f"%{q}%"
        args += [like, like, like, like]
    if op:
        where.append("op = ?")
        args.append(op)
    if status:
        where.append("status = ?")
        args.append(status)

    if not include_deleted:
        # If user unchecks "Include Deleted", we additionally hide items that are marked as UNLINKED/Deleted.
        # This allows "Include Deleted" checkbox to toggle visibility of the blue/gray "Deleted" link records.
        where.append("status != 'UNLINKED' AND status NOT LIKE 'DELETED%' AND note NOT LIKE '%已删除%'")

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    with DB_LOCK:
        conn = db_conn()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) AS c FROM link_jobs {where_sql}", tuple(args))
        total = int(cur.fetchone()["c"])
        cur.execute(f"""
            SELECT * FROM link_jobs
            {where_sql}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """, tuple(args + [limit, offset]))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
    return total, rows


def db_job_create(job_type: str, params: Dict[str, Any]) -> int:
    with DB_LOCK:
        conn = db_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO jobs(created_at, started_at, finished_at, job_type, status, total_files, done_files, message, params_json)
            VALUES(?,?,?,?,?,?,?,?,?)
        """, (now_ts(), None, None, job_type, "PENDING", 0, 0, "", json.dumps(params, ensure_ascii=False)))
        job_id = cur.lastrowid
        conn.commit()
        conn.close()
        return int(job_id)


def db_job_update(job_id: int, **fields):
    if not fields:
        return
    keys = []
    args = []
    for k, v in fields.items():
        keys.append(f"{k}=?")
        args.append(v)
    args.append(job_id)
    with DB_LOCK:
        conn = db_conn()
        cur = conn.cursor()
        cur.execute(f"UPDATE jobs SET {', '.join(keys)} WHERE id=?", tuple(args))
        conn.commit()
        conn.close()


def db_job_get(job_id: int) -> Optional[Dict[str, Any]]:
    with DB_LOCK:
        conn = db_conn()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM jobs WHERE id=?", (job_id,))
        row = cur.fetchone()
        conn.close()
    return dict(row) if row else None


def db_jobs_list(limit: int = 50) -> List[Dict[str, Any]]:
    with DB_LOCK:
        conn = db_conn()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT ?", (limit,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
    return rows


# NEW: UI shortcuts config
def db_get_ui_shortcuts(preset_key: str) -> Optional[Dict[str, Any]]:
    preset_key = (preset_key or "").strip()
    if not preset_key:
        return None
    with DB_LOCK:
        conn = db_conn()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM ui_shortcuts WHERE preset_key=?", (preset_key,))
        row = cur.fetchone()
        conn.close()
    if not row:
        return None
    d = dict(row)
    try:
        shortcuts = json.loads(d.get("shortcuts_json") or "[]")
        if not isinstance(shortcuts, list):
            shortcuts = []
    except Exception:
        shortcuts = []
    return {
        "preset_key": d.get("preset_key"),
        "base_path": d.get("base_path") or "",
        "shortcuts": shortcuts,
        "updated_at": d.get("updated_at") or 0
    }


def db_set_ui_shortcuts(preset_key: str, base_path: str, shortcuts: List[Dict[str, Any]]):
    preset_key = (preset_key or "").strip()
    if not preset_key:
        abort(400, "preset_key required")

    base_path = (base_path or "").strip()
    if not base_path:
        abort(400, "base_path required")

    # Validate paths (absolute only). Relative paths are fine.
    def _validate_path(s: str):
        s = (s or "").strip()
        if not s:
            return
        if s.startswith("/"):
            _ = safe_resolve(s)  # only checks allowed roots

    _validate_path(base_path)
    for sc in shortcuts:
        if not isinstance(sc, dict):
            continue
        _validate_path(sc.get("path") or "")

    payload = json.dumps(shortcuts, ensure_ascii=False)
    with DB_LOCK:
        conn = db_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO ui_shortcuts(preset_key, base_path, shortcuts_json, updated_at)
            VALUES(?,?,?,?)
            ON CONFLICT(preset_key) DO UPDATE SET
                base_path=excluded.base_path,
                shortcuts_json=excluded.shortcuts_json,
                updated_at=excluded.updated_at
        """, (preset_key, base_path, payload, now_ts()))
        conn.commit()
        conn.close()


@dataclass
class ActiveLinkIndex:
    built_at: float
    active_src_exact: set
    active_dir_ancestors: set
    deleted_dst: set


ACTIVE_CACHE: Optional[ActiveLinkIndex] = None
ACTIVE_CACHE_TTL = 30.0


def build_active_index() -> ActiveLinkIndex:
    with DB_LOCK:
        conn = db_conn()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT op, status, src, dst, note
            FROM link_jobs
            ORDER BY id DESC
            LIMIT 20000
        """)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()

    deleted_dst = set()
    link_ok = []
    for r in rows:
        op = r.get("op") or ""
        st = r.get("status") or ""
        note = r.get("note") or ""
        dst = r.get("dst") or ""
        if op.startswith("DELETE_") or st.startswith("DELETED") or ("已删除" in note):
            if dst:
                deleted_dst.add(dst)

    for r in rows:
        if (r.get("op") == "LINK") and (r.get("status") == "OK"):
            dst = r.get("dst") or ""
            if dst and dst not in deleted_dst:
                link_ok.append(r)

    active_src_exact = set()
    active_dir_ancestors = set()

    def add_ancestors(p: Path):
        pp = _resolve(p)
        if not is_under_allowed(pp):
            return
        curp = pp
        while True:
            if is_under_allowed(curp):
                active_dir_ancestors.add(str(curp))
            parent = curp.parent
            if parent == curp:
                break
            curp = parent
            if len(str(curp)) <= 1:
                break

    for r in link_ok:
        src = r.get("src") or ""
        if not src:
            continue
        active_src_exact.add(src)
        add_ancestors(Path(src) if Path(src).is_dir() else Path(src).parent)

    return ActiveLinkIndex(built_at=time.time(), active_src_exact=active_src_exact,
                           active_dir_ancestors=active_dir_ancestors, deleted_dst=deleted_dst)


def get_active_index(force: bool = False) -> ActiveLinkIndex:
    global ACTIVE_CACHE
    if force or (ACTIVE_CACHE is None) or ((time.time() - ACTIVE_CACHE.built_at) > ACTIVE_CACHE_TTL):
        ACTIVE_CACHE = build_active_index()
    return ACTIVE_CACHE


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def is_video(p: Path) -> bool:
    return p.suffix.lower() in VIDEO_EXT


def is_subtitle(p: Path) -> bool:
    return p.suffix.lower() in SUB_EXT


def unique_path(dst: Path) -> Path:
    base = dst.name
    stem = dst.stem
    suf = dst.suffix
    parent = dst.parent
    n = 1
    while True:
        if suf:
            cand = parent / f"{stem}_{n}{suf}"
        else:
            cand = parent / f"{base}_{n}"
        if not cand.exists():
            return cand
        n += 1


def apply_conflict_policy(dst: Path, policy: str) -> Optional[Path]:
    if not dst.exists():
        return dst
    policy = (policy or "skip").lower()
    if policy == "skip":
        return None
    if policy == "overwrite":
        if dst.is_dir():
            shutil.rmtree(dst)
        else:
            dst.unlink()
        return dst
    if policy == "rename":
        return unique_path(dst)
    return None


def hardlink_file(src: Path, dst: Path):
    ensure_dir(dst.parent)
    os.link(src, dst)


def link_dir_keep_top(src_dir: Path, dst_root: Path, policy: str,
                      job_id: Optional[int] = None,
                      cancel_event: Optional[threading.Event] = None):
    top_name = src_dir.name
    dst_top = dst_root / top_name

    dst_top_final = apply_conflict_policy(dst_top, policy)
    if dst_top_final is None:
        raise FileExistsError(f"dst dir exists, policy=skip: {dst_top}")
    dst_top = dst_top_final
    ensure_dir(dst_top)

    total = 0
    done = 0

    for root, _, files in os.walk(src_dir):
        if cancel_event and cancel_event.is_set():
            raise RuntimeError("CANCELLED")
        root_p = Path(root)
        rel = root_p.relative_to(src_dir)
        ensure_dir(dst_top / rel)

        for fn in files:
            if cancel_event and cancel_event.is_set():
                raise RuntimeError("CANCELLED")

            total += 1
            if job_id is not None:
                db_job_update(job_id, total_files=total)

            s = root_p / fn
            d = dst_top / rel / fn

            d_final = apply_conflict_policy(d, policy)
            if d_final is None:
                continue

            ensure_dir(d_final.parent)
            hardlink_file(s, d_final)
            done += 1
            if job_id is not None:
                db_job_update(job_id, done_files=done)

    return str(dst_top), total, done


RUNNING_JOBS: Dict[int, threading.Event] = {}


def start_job_thread(job_id: int):
    cancel_event = threading.Event()
    RUNNING_JOBS[job_id] = cancel_event
    t = threading.Thread(target=_job_worker, args=(job_id, cancel_event), daemon=True)
    t.start()


def _job_worker(job_id: int, cancel_event: threading.Event):
    job = db_job_get(job_id)
    if not job:
        return
    try:
        params = json.loads(job.get("params_json") or "{}")
    except Exception:
        params = {}

    db_job_update(job_id, status="RUNNING", started_at=now_ts(), message="开始执行")

    try:
        if job.get("job_type") == "LINK":
            _run_link_job(job_id, params, cancel_event)
        else:
            raise RuntimeError("unknown job_type")
        db_job_update(job_id, status="DONE", finished_at=now_ts(), message="完成")
    except Exception as ex:
        msg = str(ex)
        if "CANCELLED" in msg:
            db_job_update(job_id, status="CANCELLED", finished_at=now_ts(), message="已取消")
        else:
            db_job_update(job_id, status="FAILED", finished_at=now_ts(), message=msg[:500])
    finally:
        try:
            get_active_index(force=True)
        except Exception:
            pass
        RUNNING_JOBS.pop(job_id, None)


def _run_link_job(job_id: int, params: Dict[str, Any], cancel_event: threading.Event):
    src_items = params.get("src_items") or []
    dst_root_s = params.get("dst_root") or ""
    note = (params.get("note") or "").strip()
    policy = (params.get("conflict_policy") or "skip").lower()

    dst_root = safe_resolve(dst_root_s)
    if (not dst_root.exists()) or (not dst_root.is_dir()):
        raise FileNotFoundError("dst_root not exists/dir")

    for sp in src_items:
        if cancel_event.is_set():
            raise RuntimeError("CANCELLED")
        src_s = str(sp)
        try:
            src = safe_resolve(src_s)
            if not src.exists():
                raise FileNotFoundError(f"src not exists: {src}")

            if src.stat().st_dev != dst_root.stat().st_dev:
                raise OSError("cross-filesystem hardlink not allowed (different mount/device)")

            if src.is_dir():
                dst_top, total, done = link_dir_keep_top(src, dst_root, policy, job_id=job_id, cancel_event=cancel_event)
                db_add_record("LINK", str(src), dst_top, "DIR", "OK", f"linked dir keep-top: total={total} done={done}", note)
            else:
                dst = dst_root / src.name
                dst_final = apply_conflict_policy(dst, policy)
                if dst_final is None:
                    db_add_record("LINK", str(src), str(dst), "FILE", "SKIPPED", "dst exists, policy=skip", note)
                    continue
                ensure_dir(dst_final.parent)
                hardlink_file(src, dst_final)
                db_add_record("LINK", str(src), str(dst_final), "FILE", "OK", "linked file", note)
        except Exception as ex:
            db_add_record("LINK", src_s, str(dst_root), "DIR" if src_s.endswith("/") else "FILE", "FAIL", str(ex), note)


app = Flask(__name__)


@app.get("/")
def index():
    # Helper to get language
    lang = request.args.get("lang")
    if not lang:
        lang = request.cookies.get("lang", "zh")
    if lang not in TRANSLATIONS:
        lang = "zh"
    
    # Cookie update logic
    resp = make_response(render_template("index.html", lang=lang, i18n_json=json.dumps(TRANSLATIONS[lang], ensure_ascii=False)))
    resp.set_cookie("lang", lang, max_age=365*24*60*60)
    return resp

@app.context_processor
def inject_i18n():
    def get_lang():
        lang = request.args.get("lang")
        if not lang:
            lang = request.cookies.get("lang", "zh")
        if lang not in TRANSLATIONS:
            lang = "zh"
        return lang

    def t(key, default=None):
        lang = get_lang()
        val = TRANSLATIONS.get(lang, {}).get(key)
        return val if val else (default or key)
    
    return dict(t=t, current_lang=get_lang())


@app.get("/api/presets")
def presets():
    # Load presets from data/presets.json if exists
    presets_file = Path(DB_PATH).parent / "presets.json"
    pairs = []
    shortcuts = ["电影", "剧集", "动漫", "待整理", "已整理"]

    if presets_file.exists():
        try:
            with open(presets_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                pairs = data.get("pairs", [])
                if "target_shortcuts" in data:
                    shortcuts = data["target_shortcuts"]
        except Exception as e:
            print(f"Error loading presets: {e}")

    # Fallback/Default if empty (or for new users)
    if not pairs:
        pairs = []

    return jsonify({
        "allowed_roots": [str(r) for r in ALLOWED_ROOTS],
        "pairs": pairs,
        "target_shortcuts": shortcuts
    })


# NEW: UI shortcuts API (persisted in DB)
@app.get("/api/ui/shortcuts")
def api_ui_shortcuts_get():
    preset_key = (request.args.get("preset_key") or "").strip()
    if not preset_key:
        return jsonify({"ok": False, "error": "preset_key required"}), 400
    cfg = db_get_ui_shortcuts(preset_key)
    if not cfg:
        return jsonify({"ok": True, "found": False}), 200
    return jsonify({"ok": True, "found": True, "base_path": cfg["base_path"], "shortcuts": cfg["shortcuts"], "updated_at": cfg["updated_at"]})


@app.post("/api/ui/shortcuts")
def api_ui_shortcuts_set():
    data = request.get_json(force=True)
    preset_key = (data.get("preset_key") or "").strip()
    base_path = (data.get("base_path") or "").strip()
    shortcuts = data.get("shortcuts") or []
    if not isinstance(shortcuts, list):
        return jsonify({"ok": False, "error": "shortcuts must be list"}), 400

    # sanitize shortcuts structure
    cleaned: List[Dict[str, Any]] = []
    for sc in shortcuts:
        if not isinstance(sc, dict):
            continue
        label = str(sc.get("label") or "").strip()
        path = str(sc.get("path") or "").strip()
        if not label:
            continue
        # simple max length
        label = label.replace("/", "_").replace("\\", "_")[:60]
        path = path[:500]
        cleaned.append({"label": label, "path": path})

    try:
        db_set_ui_shortcuts(preset_key, base_path, cleaned)
    except Exception as ex:
        return jsonify({"ok": False, "error": str(ex)}), 400

    return jsonify({"ok": True})


@app.get("/api/list")
def api_list():
    base = safe_resolve(request.args.get("path", ""))
    show_hidden = request.args.get("hidden", "0") == "1"
    q = (request.args.get("q") or "").lower().strip()
    sort_key = request.args.get("sort", "mtime")
    order = request.args.get("order", "desc")
    only = (request.args.get("only") or "all").lower()
    link_filter = (request.args.get("link") or "all").lower()  # NEW: all|linked|unlinked

    page = int(request.args.get("page", "1") or "1")
    page_size = int(request.args.get("page_size", "200") or "200")
    page = max(1, page)
    page_size = min(max(20, page_size), 1000)

    if not base.exists():
        return jsonify({"path": str(base), "items": [], "error": "path not exists", "total": 0}), 200
    if not base.is_dir():
        return jsonify({"path": str(base), "items": [], "error": "path not dir", "total": 0}), 200

    idx = get_active_index()
    active_exact = idx.active_src_exact
    active_anc = idx.active_dir_ancestors

    items = []
    try:
        for e in base.iterdir():
            name = e.name
            if not show_hidden and name.startswith("."):
                continue
            if q and q not in name.lower():
                continue

            try:
                st = e.stat()
            except FileNotFoundError:
                continue

            is_dir = e.is_dir()
            if only == "dirs" and not is_dir:
                continue
            if only == "files" and is_dir:
                continue
            if only == "video":
                if is_dir or not is_video(e):
                    continue
            if only == "subs":
                if is_dir or not is_subtitle(e):
                    continue

            p = str(e)
            link_mark = "none"
            if p in active_exact:
                link_mark = "exact"
            elif is_dir and (p in active_anc):
                link_mark = "partial"

            # NEW: link filter
            if link_filter == "linked":
                if link_mark == "none":
                    continue
            elif link_filter == "unlinked":
                if link_mark != "none":
                    continue

            items.append({
                "name": name,
                "path": p,
                "is_dir": is_dir,
                "size": 0 if is_dir else int(st.st_size),
                "mtime": int(st.st_mtime),
                "link_mark": link_mark
            })
    except PermissionError as ex:
        return jsonify({"path": str(base), "items": [], "error": str(ex), "total": 0}), 200

    reverse = (order == "desc")

    def key_fn(x):
        if sort_key == "mtime":
            return x["mtime"]
        if sort_key == "size":
            return x["size"]
        return x["name"].lower()

    dirs = [x for x in items if x["is_dir"]]
    files = [x for x in items if not x["is_dir"]]
    dirs.sort(key=key_fn, reverse=reverse)
    files.sort(key=key_fn, reverse=reverse)
    merged = dirs + files

    total = len(merged)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = merged[start:end]

    return jsonify({
        "path": str(base),
        "items": page_items,
        "total": total,
        "page": page,
        "page_size": page_size
    })


@app.post("/api/mkdir")
def api_mkdir():
    data = request.get_json(force=True)
    p = safe_resolve(data.get("path") or "")
    ensure_dir(p)
    return jsonify({"ok": True, "path": str(p)})


@app.post("/api/precheck")
def api_precheck():
    data = request.get_json(force=True)
    src_items = data.get("src_items") or []
    dst_root_s = data.get("dst_root") or ""
    dst_root = safe_resolve(dst_root_s)

    conflicts = []
    if not dst_root.exists() or not dst_root.is_dir():
        return jsonify({"ok": False, "error": "dst_root not exists/dir"}), 400

    for sp in src_items:
        try:
            src = safe_resolve(str(sp))
            if not src.exists():
                conflicts.append({"src": str(src), "dst": "", "type": "MISSING", "reason": "src not exists"})
                continue
            dst = dst_root / src.name
            if dst.exists():
                conflicts.append({"src": str(src), "dst": str(dst), "type": "DIR" if src.is_dir() else "FILE", "reason": "dst exists"})
        except Exception as ex:
            conflicts.append({"src": str(sp), "dst": "", "type": "ERROR", "reason": str(ex)})

    return jsonify({"ok": True, "conflicts": conflicts})


@app.post("/api/link")
def api_link():
    data = request.get_json(force=True)
    src_items = data.get("src_items") or []
    dst_root = data.get("dst_root") or ""
    note = (data.get("note") or "").strip()
    policy = (data.get("conflict_policy") or "skip").lower()

    if not src_items:
        return jsonify({"ok": False, "error": "no src_items"}), 400
    dr = safe_resolve(dst_root)
    if not dr.exists() or not dr.is_dir():
        return jsonify({"ok": False, "error": "dst_root not exists/dir"}), 400

    params = {"src_items": src_items, "dst_root": dst_root, "note": note, "conflict_policy": policy}
    job_id = db_job_create("LINK", params)
    start_job_thread(job_id)
    return jsonify({"ok": True, "job_id": job_id})


@app.get("/api/jobs")
def api_jobs():
    return jsonify({"ok": True, "jobs": db_jobs_list(limit=int(request.args.get("limit", "50") or "50"))})


@app.get("/api/jobs/<int:job_id>")
def api_job_get(job_id: int):
    j = db_job_get(job_id)
    if not j:
        return jsonify({"ok": False, "error": "not found"}), 404
    return jsonify({"ok": True, "job": j})


@app.post("/api/jobs/<int:job_id>/cancel")
def api_job_cancel(job_id: int):
    ev = RUNNING_JOBS.get(job_id)
    if not ev:
        return jsonify({"ok": True, "message": "not running"})
    ev.set()
    return jsonify({"ok": True, "message": "cancel requested"})


@app.get("/api/records")
def api_records():
    limit = int(request.args.get("limit", "200") or "200")
    offset = int(request.args.get("offset", "0") or "0")
    q = request.args.get("q", "") or ""
    op = request.args.get("op", "") or ""
    status = request.args.get("status", "") or ""
    include_deleted = (request.args.get("include_deleted", "1") == "1")

    total, rows = db_list_records(limit=limit, offset=offset, q=q, op=op, status=status, include_deleted=include_deleted)
    return jsonify({"ok": True, "total": total, "rows": rows, "limit": limit, "offset": offset})


@app.get("/api/records/export")
def api_records_export():
    fmt = (request.args.get("fmt") or "json").lower()
    total, rows = db_list_records(limit=20000, offset=0, q=request.args.get("q", "") or "",
                                  op=request.args.get("op", "") or "", status=request.args.get("status", "") or "",
                                  include_deleted=(request.args.get("include_deleted", "1") == "1"))

    if fmt == "csv":
        output = io.StringIO()
        w = csv.writer(output)
        w.writerow(["id", "created_at", "op", "src", "dst", "item_type", "status", "message", "note"])
        for r in rows:
            w.writerow([r.get("id"), r.get("created_at"), r.get("op"), r.get("src"), r.get("dst"),
                        r.get("item_type"), r.get("status"), r.get("message"), r.get("note")])
        mem = io.BytesIO(output.getvalue().encode("utf-8"))
        mem.seek(0)
        return send_file(mem, mimetype="text/csv", as_attachment=True, download_name="hardlink_records.csv")

    mem = io.BytesIO(json.dumps({"total": total, "rows": rows}, ensure_ascii=False, indent=2).encode("utf-8"))
    mem.seek(0)
    return send_file(mem, mimetype="application/json", as_attachment=True, download_name="hardlink_records.json")


@app.post("/api/records/import")
def api_records_import():
    data = request.get_json(force=True)
    rows = data.get("rows") or []
    if not isinstance(rows, list):
        return jsonify({"ok": False, "error": "rows must be list"}), 400
    n = 0
    for r in rows:
        try:
            op = r.get("op") or "LINK"
            src = r.get("src") or ""
            dst = r.get("dst") or ""
            item_type = r.get("item_type") or "FILE"
            status = r.get("status") or "OK"
            msg = r.get("message") or ""
            note = r.get("note") or ""
            db_add_record(op, src, dst, item_type, status, msg, note)
            n += 1
        except Exception:
            continue
    get_active_index(force=True)
    return jsonify({"ok": True, "imported": n})


@app.post("/api/delete")
def api_delete():
    data = request.get_json(force=True)
    mode = data.get("mode")
    items = data.get("items") or []
    confirm = bool(data.get("confirm"))
    note = (data.get("note") or "").strip()

    if mode not in ("target", "target_recursive", "both"):
        return jsonify({"ok": False, "error": "mode must be target / target_recursive / both"}), 400
    if not confirm:
        return jsonify({"ok": False, "error": "confirm required"}), 400
    if not items:
        return jsonify({"ok": False, "error": "no items"}), 400

    def delete_path_recursive(p: Path):
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()

    def update_original_link_record(dst_path: str, note_suffix: str):
        try:
            with DB_LOCK:
                conn = db_conn()
                cur = conn.cursor()
                cur.execute("SELECT id, note FROM link_jobs WHERE dst=? AND (op='LINK' OR op='HARDLINK') ORDER BY id DESC LIMIT 1", (dst_path,))
                row = cur.fetchone()
                if row:
                    old_note = row[1] or ""
                    new_note = (old_note + " | " + note_suffix).strip()
                    cur.execute("UPDATE link_jobs SET note=?, status='UNLINKED' WHERE id=?", (new_note, row[0]))
                conn.commit()
                conn.close()
        except Exception:
            pass

    results = []
    for it in items:
        src_s = it.get("src") or ""
        dst_s = it.get("dst") or ""
        item_type = it.get("type") or "FILE"
        try:
            dst = safe_resolve(dst_s) if dst_s else None
            src = safe_resolve(src_s) if src_s else None

            if mode == "target":
                if not dst or not dst.exists():
                    raise FileNotFoundError("dst not exists")
                if dst.is_dir():
                    dst.rmdir()
                else:
                    dst.unlink()
                
                # Update original record instead of adding DELETE
                update_original_link_record(dst_s, "已删除")
                results.append({"dst": dst_s, "status": "DELETED"})

            elif mode == "target_recursive":
                if not dst or not dst.exists():
                    raise FileNotFoundError("dst not exists")
                delete_path_recursive(dst)
                
                # For recursive, we might need to find all records under this path?
                # Simple approximation: update the record for the dir itself if exists, or do nothing.
                # User requirement is mostly for files.
                update_original_link_record(dst_s, "已删除(递归)")
                results.append({"dst": dst_s, "status": "DELETED_RECURSIVE"})

            else:
                if not dst or not dst.exists():
                    raise FileNotFoundError("dst not exists")
                if not src or not src.exists():
                    raise FileNotFoundError("src not exists")

                if dst.is_dir():
                    dst.rmdir()
                else:
                    dst.unlink()

                if src.is_dir():
                    src.rmdir()
                else:
                    src.unlink()

                update_original_link_record(dst_s, "已删除(双删)")
                results.append({"src": src_s, "dst": dst_s, "status": "DELETED_BOTH"})

        except Exception as ex:
            # On failure, we might still want to record the failure? 
            # Original code recorded db_add_record(..., "FAIL", ...)
            # Let's keep recording failures as they are important for debugging.
            op = "DELETE_BOTH" if mode == "both" else ("DELETE_TARGET_RECURSIVE" if mode == "target_recursive" else "DELETE_TARGET")
            db_add_record(op, src_s, dst_s, item_type, "FAIL", str(ex), note)
            results.append({"src": src_s, "dst": dst_s, "status": "FAIL", "error": str(ex)})

    get_active_index(force=True)
    return jsonify({"ok": True, "results": results})


@app.get("/api/hardlinks/groups")
def api_hardlinks_groups():
    # 默认扫描范围：ALLOWED_ROOTS（与允许硬链接目录范围一致）
    offset = int(request.args.get("offset", "0"))
    limit_groups = int(request.args.get("limit_groups", "200"))
    max_paths = int(request.args.get("max_paths", "80"))
    max_files = int(request.args.get("max_files", "300000"))

    offset = max(0, offset)
    limit_groups = max(1, min(1000, limit_groups))
    max_paths = max(0, min(5000, max_paths))
    max_files = max(1, min(2_000_000, max_files))

    roots = [str(p) for p in ALLOWED_ROOTS]

    inode_map: Dict[Tuple[int, int], List[str]] = {}
    scanned = 0

    def add_path(full: str):
        nonlocal scanned
        try:
            st = os.stat(full, follow_symlinks=False)
        except Exception:
            return
        scanned += 1
        if not stat.S_ISREG(st.st_mode):
            return
        if st.st_nlink <= 1:
            return
        key = (int(st.st_dev), int(st.st_ino))
        inode_map.setdefault(key, []).append(full)

    for r in roots:
        try:
            rr = str(safe_resolve(r))
        except Exception:
            continue
        for dirpath, dirnames, filenames in os.walk(rr):
            for name in filenames:
                if scanned >= max_files:
                    break
                add_path(os.path.join(dirpath, name))
            if scanned >= max_files:
                break
        if scanned >= max_files:
            break

    groups: List[Dict[str, Any]] = []
    for (dev, ino), paths in inode_map.items():
        uniq = sorted(set(paths))
        if len(uniq) < 2:
            continue
        canonical = sorted(uniq, key=lambda x: (len(x), x))[0]  # 稳定 canonical
        targets = [p for p in uniq if p != canonical]
        if max_paths and len(targets) > max_paths:
            targets = targets[:max_paths]
        groups.append({"dev": dev, "ino": ino, "src": canonical, "targets": targets})

    # 排序稳定：目标多的在前，其次源路径字典序
    groups.sort(key=lambda g: (-len(g["targets"]), g["src"]))
    total = len(groups)

    # 分页切片
    groups = groups[offset: offset + limit_groups]

    return jsonify({
        "ok": True,
        "roots": roots,
        "scanned_files": scanned,
        "total_groups": total,
        "offset": offset,
        "limit": limit_groups,
        "groups": groups
    })


@app.post("/api/hardlinks/unlink")
def api_hardlinks_unlink():
    data = request.get_json(force=True, silent=True) or {}
    # Support single path or list of paths
    paths = data.get("paths")
    if not paths:
        if data.get("path"):
            paths = [data.get("path")]
    
    if not paths or not isinstance(paths, list):
        return jsonify({"ok": False, "error": "path or paths required"}), 400

    deleted_count = 0
    errors = []

    for path in paths:
        try:
            p = safe_resolve(str(path))
            if not p.exists():
                errors.append(f"{path}: not found")
                continue
            if p.is_dir():
                errors.append(f"{path}: is dir")
                continue

            # 只删除该路径（unlink 一个硬链接目录项）
            p.unlink()
            deleted_count += 1
            
            # UPDATE RECORD: Find the original LINK record for this dst and update it
            try:
                # We need to find the record where dst matches the deleted path
                with DB_LOCK:
                    conn = db_conn()
                    cur = conn.cursor()
                    # Find latest link record for this dst
                    cur.execute("SELECT id, note FROM link_jobs WHERE dst=? AND (op='LINK' OR op='HARDLINK') ORDER BY id DESC LIMIT 1", (str(p),))
                    row = cur.fetchone()
                    if row:
                        old_note = row[1] or ""
                        new_note = (old_note + " | 已删除").strip()
                        # Update status to UNLINKED or keep OK but with note? User said "add a note".
                        # Let's mark status as UNLINKED for clarity or just update note.
                        # User specifically said: "in the link file add a note that it was deleted"
                        # And "don't show delete records" -> We won't insert UNLINK_MANAGE record.
                        cur.execute("UPDATE link_jobs SET note=?, status='UNLINKED' WHERE id=?", (new_note, row[0]))
                    else:
                         # If no link record found, maybe we should insert one? 
                         # User said "don't show delete records". So if no link record exists, we do nothing in DB or maybe insert one but hidden?
                         # Let's just do nothing if no match found, as the requirement is about hiding/modifying.
                         pass
                    conn.commit()
                    conn.close()
            except Exception:
                pass

        except Exception as e:
            errors.append(f"{path}: {str(e)}")

    # Only rebuild index once
    try:
        get_active_index(force=True)
    except Exception:
        pass

    return jsonify({"ok": True, "deleted": deleted_count, "errors": errors})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=APP_PORT, debug=False)
