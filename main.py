#!/usr/bin/env python3
"""stdin: キャッシュ済みタスクJSON, argv[1]: query, argv[2]: active entry JSONファイルパス"""
import json
import sys
import os


def fmt_dur(sec):
    h, m = int(sec) // 3600, (int(sec) % 3600) // 60
    return f"{h}h {m:02d}m" if h else f"{m}m"


def do_config():
    """config コマンド: キャッシュ済みカテゴリからリスト表示"""
    items = []
    cache_dir = os.environ.get("alfred_workflow_cache", "")
    cats_path = os.path.join(cache_dir, "categories.json") if cache_dir else ""
    if cats_path and os.path.exists(cats_path):
        try:
            with open(cats_path) as f:
                cats = json.loads(f.read())
            for c in cats:
                items.append({
                    "title": c.get("title", ""),
                    "subtitle": "Enterでデフォルトカテゴリに設定",
                    "arg": f"set_category:{c.get('id', '')}:{c.get('title', '')}",
                    "valid": True,
                })
        except (json.JSONDecodeError, ValueError):
            items.append({"title": "カテゴリ取得エラー", "valid": False})
    if not items:
        items.append({"title": "カテゴリが見つかりません", "valid": False})
    print(json.dumps({"items": items}, ensure_ascii=False))


def main():
    query = sys.argv[1].strip() if len(sys.argv) > 1 else ""
    active_path = sys.argv[2] if len(sys.argv) > 2 else ""

    # config コマンドは早期リターン
    if query.lower() == "config":
        do_config()
        return

    raw = sys.stdin.read()
    items = []

    # 打刻中のタスクを常に先頭に表示
    active_loaded = False
    if active_path and os.path.exists(active_path):
        try:
            with open(active_path) as f:
                content = f.read()
            if content.strip():
                user_data = json.loads(content)
                active_loaded = True
                entry = user_data.get("time_entry")
                if entry and entry.get("stopped_at") is None:
                    task = entry.get("task", {})
                    title = task.get("title", "不明")
                    dur = fmt_dur(entry.get("duration", 0))
                    if not query or query.lower() in title.lower() or query.lower() in "終了end":
                        items.append({
                            "title": f"打刻中: {title} ({dur})",
                            "subtitle": "Enterで打刻を停止",
                            "arg": "end",
                            "valid": True,
                        })
                else:
                    if not query:
                        items.append({"title": "打刻なし", "valid": False})
        except (json.JSONDecodeError, ValueError):
            pass

    if not active_loaded and not query:
        items.append({"title": "打刻状態を確認中...", "valid": False})

    # タスク一覧
    tasks = []
    try:
        data = json.loads(raw)
        tasks = data.get("tasks", []) if isinstance(data, dict) else data
    except Exception:
        pass

    q = query.lower()
    for t in tasks:
        title = t.get("title", "")
        cat = (t.get("category") or {}).get("title", "")
        if q and q not in title.lower() and q not in cat.lower():
            continue
        items.append({
            "title": title,
            "subtitle": f"カテゴリ: {cat}" if cat else "",
            "arg": f"switch:{t.get('team_id', '')}:{t.get('id', '')}:{title}",
            "valid": True,
        })

    # 自由入力
    if query:
        exact = any(t.get("title", "").lower() == q for t in tasks)
        if not exact:
            items.append({
                "title": f"「{query}」で新規打刻開始",
                "subtitle": "新しいタスクとして打刻を開始",
                "arg": f"new:{query}",
                "valid": True,
            })

    if not items:
        items.append({"title": "タスクが見つかりません", "valid": False})

    result = {"items": items}

    # active がまだ読めていなければ rerun で再取得
    if not active_loaded and not query:
        result["rerun"] = 1.0

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
