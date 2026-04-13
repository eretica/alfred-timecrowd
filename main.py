#!/usr/bin/env python3
"""stdin: キャッシュ済みタスクJSON, argv[1]: query, argv[2]: active entry JSONパス, argv[3]: 検索結果JSONパス"""
import json
import sys
import os


def fmt_dur(sec):
    h, m = int(sec) // 3600, (int(sec) % 3600) // 60
    return f"{h}h {m:02d}m" if h else f"{m}m"


def parse_tasks(data):
    """APIレスポンスからタスクリストを抽出（形式差異を吸収）"""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("tasks", "results", "data"):
            if key in data and isinstance(data[key], list):
                return data[key]
    return []


def task_to_item(t):
    """タスクオブジェクトからAlfred itemを生成（フラット/ネスト両対応）"""
    tid = str(t.get("id", ""))
    title = t.get("title", "")
    team_id = t.get("team_id", "") or (t.get("team") or {}).get("id", "")
    cat = (t.get("category") or {}).get("title", "")
    return tid, {
        "title": title,
        "subtitle": f"カテゴリ: {cat}" if cat else "",
        "arg": f"switch:{team_id}:{tid}:{title}",
        "valid": True,
    }


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
    search_path = sys.argv[3] if len(sys.argv) > 3 else ""

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

    # キャッシュ済みタスク一覧
    cached_tasks = []
    try:
        cached_tasks = parse_tasks(json.loads(raw))
    except Exception:
        pass

    # API検索結果
    search_results = []
    if query and search_path and os.path.exists(search_path):
        try:
            with open(search_path) as f:
                search_results = parse_tasks(json.loads(f.read()))
        except (json.JSONDecodeError, ValueError):
            pass

    q = query.lower()
    seen_ids = set()

    # 検索結果を優先表示
    for t in search_results:
        tid, item = task_to_item(t)
        if tid:
            seen_ids.add(tid)
        items.append(item)

    # キャッシュからフィルタ（検索結果と重複しないもの）
    for t in cached_tasks:
        tid, item = task_to_item(t)
        if tid in seen_ids:
            continue
        title = t.get("title", "")
        cat = (t.get("category") or {}).get("title", "")
        if q and q not in title.lower() and q not in cat.lower():
            continue
        seen_ids.add(tid)
        items.append(item)

    # 自由入力
    if query:
        all_tasks = cached_tasks + search_results
        exact = any(t.get("title", "").lower() == q for t in all_tasks)
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
