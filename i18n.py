# -*- coding: utf-8 -*-

TRANSLATIONS = {
    "zh": {
        # Header / Global
        "APP_TITLE": "Hardlink Manager Final",
        "BRAND_NAME": "Hardlink Pro",
        "THEME_BTN": "主题",
        "MANAGE_BTN": "管理",
        "LOGS_BTN": "记录",
        "LANG_BTN": "En",

        # Panes
        "PANE_SRC_TITLE": "源文件 (Source)",
        "PANE_DST_TITLE": "目标路径 (Target)",
        "BTN_REFRESH": "刷新",
        "BTN_SET_ROOT": "设为快捷根",
        "PLACEHOLDER_SEARCH": "输入路径...",
        "PLACEHOLDER_SHORTCUT_NAME": "快捷名",
        "PLACEHOLDER_SHORTCUT_PATH": "相对路径",
        "BTN_ADD": "添加",
        
        # Source Filters
        "OPT_SHOW_ALL": "显示全部",
        "OPT_DIRS_ONLY": "仅文件夹",
        "OPT_VIDEO_ONLY": "仅视频",
        "OPT_STATUS": "状态",
        "OPT_UNLINKED": "未链",
        "OPT_LINKED": "已链",
        
        # Table Headers
        "TH_FILENAME": "文件名",
        "TH_SIZE": "大小",
        "TH_STATUS": "状态",
        "TH_DIR_NAME": "目录名称 (点击进入)",
        "TH_TIME": "时间",
        "TH_CHECK": "全选",

        # Action Bar
        "ACT_TITLE": "执行操作",
        "LBL_POLICY": "冲突处理策略",
        "OPT_SKIP": "⚠️ 冲突：跳过 (Skip)",
        "OPT_OVERWRITE": "⚠️ 冲突：覆盖 (Overwrite)",
        "OPT_RENAME": "⚠️ 冲突：自动改名",
        "LBL_NOTE": "备注信息",
        "PLACEHOLDER_NOTE": "备注信息（可选）",
        "BTN_PRECHECK": "🔍 预检查",
        "BTN_LINK": "🚀 开始硬链接",
        
        # Logs Modal
        "LOGS_TITLE": "记录管理与删除",
        "BTN_CLOSE": "关闭 ✕",
        "OPT_ALL_STATUS": "所有状态",
        "OPT_OK": "成功 (OK)",
        "OPT_FAIL": "失败 (FAIL)",
        "LBL_INCLUDE_DELETED": "含已删",
        "TH_OP": "操作",
        "TH_SRC_INFO": "源文件 / 信息",
        "TH_DST": "目标",
        "LBL_DELETE_OP": "🗑️ 删除操作:",
        "OPT_DEL_TARGET_REC": "仅删目标 (文件/递归目录)",
        "OPT_DEL_TARGET": "仅删目标 (非空目录报错)",
        "OPT_DEL_BOTH": "高风险: 同时删除源+目标",
        "LBL_CONFIRM_EXEC": "确认执行",
        "BTN_EXEC_DELETE": "执行删除",

        # Manage Modal
        "MANAGE_TITLE": "硬链接管理 (按源分组)",
        "PLACEHOLDER_SEARCH_MANAGE": "搜索路径 / 文件名...",
        "BTN_RESCAN": "🔄 重新全盘扫描",
        "MSG_SCANNING": "扫描中…（目录大时会稍慢）",
        "MSG_FOUND_GROUPS": "发现硬链接组：{groups}（扫描文件：{scanned}）",
        "MSG_NO_MATCH": "没有找到匹配的硬链接组",
        "TH_SOURCE_GROUP": "源文件 (组)",
        "TH_LINKS_COUNT": "链接数",
        "TH_ACTIONS": "操作",
        "BTN_DELETE_SELECTED": "批量删除选中",
        
        # JS Messages
        "MSG_LOAD_FAIL": "列表加载失败",
        "MSG_DST_LOAD_FAIL": "目标列表失败",
        "MSG_PRECHECK_NO_SEL": "请先勾选源文件",
        "MSG_PRECHECK_PASS": "✅ 检查通过，无冲突。",
        "MSG_PRECHECK_CONFLICT": "⚠️ 发现冲突:\n",
        "MSG_LINK_CONFIRM": "确认对 {n} 个项目创建硬链接？",
        "MSG_LINK_STARTED": "🚀 任务已后台运行",
        "MSG_LINK_FAIL": "提交失败: ",
        "MSG_DELETE_NO_CONFIRM": "请先勾选“确认执行”",
        "MSG_DELETE_NO_SEL": "请先勾选要删除的记录",
        "MSG_DELETE_SUCCESS": "✅ 删除执行完毕",
        "MSG_DELETE_FAIL": "❌ 删除失败: ",
        "MSG_SET_SHORTCUT_ROOT": "已设为快捷根目录",
        "MSG_INIT_ERROR": "初始化错误",
        "MSG_CANCEL_REQUESTED": "已请求取消",
        
        # Manage Modal Alerts
        "MSG_UNLINK_CONFIRM": "确认删除该路径（unlink）？\n\n{path}\n\n注意：只删除该目录项，其它硬链接仍保留。",
        "MSG_DELETE_CONFIRM_BATCH": "⚠️ 确认批量删除选中的 {n} 个项目？\n\n这将从文件系统中 unlink 这些路径。\n（如果它们是唯一的，文件将被永久删除！）",
        "MSG_DELETE_BATCH_START": "正在批量删除...",
        "MSG_DELETE_BATCH_PARTIAL": "部分完成：已删除 {k} 个，失败 {f} 个。\n\n首个错误: {err}",
        "MSG_DELETE_BATCH_DONE": "✅ 成功删除 {n} 个项目",
        "MSG_DELETE_BATCH_FAIL": "批量删除失败: ",
        "MSG_DELETE_REQ_ERR": "请求异常: ",

        # Status Labels
        "STATUS_OK": "成功",
        "STATUS_FAIL": "失败",
        "STATUS_UNLINKED": "已删除",
        "STATUS_SKIPPED": "跳过",
        "BADGE_LINKED": "已链",
        "BADGE_PARTIAL": "部分",
        "BADGE_DELETED": "已删",
        "BADGE_SOURCE_TYPE": "外部/本工具生成",
        
        # Mobile Nav
        "NAV_SRC": "源文件",
        "NAV_DST": "目标",
        "NAV_ACT": "执行",
        
        # Empty States
        "EMPTY_DIR": "空目录",
    },
    "en": {
        # Header / Global
        "APP_TITLE": "Hardlink Manager Final",
        "BRAND_NAME": "Hardlink Pro",
        "THEME_BTN": "Theme",
        "MANAGE_BTN": "Manage",
        "LOGS_BTN": "Logs",
        "LANG_BTN": "中",

        # Panes
        "PANE_SRC_TITLE": "Source Files",
        "PANE_DST_TITLE": "Target Path",
        "BTN_REFRESH": "Refresh",
        "BTN_SET_ROOT": "Set as Root",
        "PLACEHOLDER_SEARCH": "Enter path...",
        "PLACEHOLDER_SHORTCUT_NAME": "Alias",
        "PLACEHOLDER_SHORTCUT_PATH": "Rel Path",
        "BTN_ADD": "Add",
        
        # Source Filters
        "OPT_SHOW_ALL": "All",
        "OPT_DIRS_ONLY": "Dirs Only",
        "OPT_VIDEO_ONLY": "Video Only",
        "OPT_STATUS": "Status",
        "OPT_UNLINKED": "Unlinked",
        "OPT_LINKED": "Linked",
        
        # Table Headers
        "TH_FILENAME": "Name",
        "TH_SIZE": "Size",
        "TH_STATUS": "Status",
        "TH_DIR_NAME": "Directory Name",
        "TH_TIME": "Time",
        "TH_CHECK": "All",

        # Action Bar
        "ACT_TITLE": "Execute",
        "LBL_POLICY": "Conflict Policy",
        "OPT_SKIP": "⚠️ Conflict: Skip",
        "OPT_OVERWRITE": "⚠️ Conflict: Overwrite",
        "OPT_RENAME": "⚠️ Conflict: Auto Rename",
        "LBL_NOTE": "Note",
        "PLACEHOLDER_NOTE": "Optional note",
        "BTN_PRECHECK": "🔍 Pre-check",
        "BTN_LINK": "🚀 Start Link",
        
        # Logs Modal
        "LOGS_TITLE": "Logs & Delete",
        "BTN_CLOSE": "Close ✕",
        "OPT_ALL_STATUS": "All Status",
        "OPT_OK": "Success (OK)",
        "OPT_FAIL": "Failed (FAIL)",
        "LBL_INCLUDE_DELETED": "Incl. Deleted",
        "TH_OP": "Op",
        "TH_SRC_INFO": "Source / Info",
        "TH_DST": "Target",
        "LBL_DELETE_OP": "🗑️ Delete Op:",
        "OPT_DEL_TARGET_REC": "Target Only (Recurse)",
        "OPT_DEL_TARGET": "Target Only (Safe)",
        "OPT_DEL_BOTH": "BOTH Source+Target",
        "LBL_CONFIRM_EXEC": "Confirm",
        "BTN_EXEC_DELETE": "Execute",

        # Manage Modal
        "MANAGE_TITLE": "Manage Links (Grouped)",
        "PLACEHOLDER_SEARCH_MANAGE": "Search path / name...",
        "BTN_RESCAN": "🔄 Rescan All",
        "MSG_SCANNING": "Scanning... (may take time)",
        "MSG_FOUND_GROUPS": "Groups Found: {groups} (Files: {scanned})",
        "MSG_NO_MATCH": "No matching groups found",
        "TH_SOURCE_GROUP": "Source (Group)",
        "TH_LINKS_COUNT": "Links",
        "TH_ACTIONS": "Actions",
        "BTN_DELETE_SELECTED": "Delete Selected",
        
        # JS Messages
        "MSG_LOAD_FAIL": "Failed to load list",
        "MSG_DST_LOAD_FAIL": "Failed to load target list",
        "MSG_PRECHECK_NO_SEL": "Please select source files first",
        "MSG_PRECHECK_PASS": "✅ No conflicts found.",
        "MSG_PRECHECK_CONFLICT": "⚠️ Conflicts found:\n",
        "MSG_LINK_CONFIRM": "Create hardlinks for {n} items?",
        "MSG_LINK_STARTED": "🚀 Job started in background",
        "MSG_LINK_FAIL": "Submit failed: ",
        "MSG_DELETE_NO_CONFIRM": "Please check 'Confirm'",
        "MSG_DELETE_NO_SEL": "Please select records to delete",
        "MSG_DELETE_SUCCESS": "✅ Delete completed",
        "MSG_DELETE_FAIL": "❌ Delete failed: ",
        "MSG_SET_SHORTCUT_ROOT": "Shortcut root set",
        "MSG_INIT_ERROR": "Init error",
        "MSG_CANCEL_REQUESTED": "Cancel requested",

        # Manage Modal Alerts
        "MSG_UNLINK_CONFIRM": "Confirm unlink path?\n\n{path}\n\nNote: Only removes this directory entry, other hardlinks remain.",
        "MSG_DELETE_CONFIRM_BATCH": "⚠️ Confirm batch delete {n} items?\n\nThis will unlink these paths.\n(If they are the only copy, files will be permanently deleted!)",
        "MSG_DELETE_BATCH_START": "Batch deleting...",
        "MSG_DELETE_BATCH_PARTIAL": "Partial: deleted {k}, failed {f}.\n\nFirst error: {err}",
        "MSG_DELETE_BATCH_DONE": "✅ Successfully deleted {n} items",
        "MSG_DELETE_BATCH_FAIL": "Batch delete failed: ",
        "MSG_DELETE_REQ_ERR": "Request error: ",

        # Status Labels
        "STATUS_OK": "OK",
        "STATUS_FAIL": "FAIL",
        "STATUS_UNLINKED": "Deleted",
        "STATUS_SKIPPED": "Skip",
        "BADGE_LINKED": "Linked",
        "BADGE_PARTIAL": "Partial",
        "BADGE_DELETED": "Del",
        "BADGE_SOURCE_TYPE": "External/Tool Gen",
        
        # Mobile Nav
        "NAV_SRC": "Source",
        "NAV_DST": "Target",
        "NAV_ACT": "Run",
        
        # Empty States
        "EMPTY_DIR": "Empty Directory",
    }
}
