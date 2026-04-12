#!/usr/bin/env python3
"""アクション実行スクリプト。Alfred Run Scriptから呼ばれる。"""

import sys

from config import get_token, get_default_team_id, get_default_category_id, load_config, save_config
from state import (
    save_previous_task,
    save_current_entry,
    clear_current_entry,
)
from timecrowd import TimeCrowdAPI


def output(message: str):
    print(message)


def do_end(api: TimeCrowdAPI):
    active = api.get_active_entry()
    if not active:
        output("打刻中のタスクはありません")
        return

    entry = api.stop_entry(str(active["id"]))
    task_title = entry.get("task", {}).get("title", "不明")
    clear_current_entry()
    output(f"打刻停止: {task_title}")


def do_switch(api: TimeCrowdAPI, team_id: str, task_id: str, task_title: str):
    active = api.get_active_entry()
    if active:
        cur_task = active.get("task", {})
        cur_team_id = str(active.get("team", {}).get("id", active.get("team_id", "")))
        save_previous_task(cur_team_id, str(cur_task.get("id", "")), cur_task.get("title", ""))
        api.stop_entry(str(active["id"]))

    entry = api.start_task(team_id, task_id)
    save_current_entry(str(entry["id"]), task_id, task_title, team_id)
    output(f"打刻開始: {task_title}")


def do_new_task(api: TimeCrowdAPI, task_title: str):
    team_id = get_default_team_id()
    if not team_id:
        teams = api.get_teams()
        if not teams:
            output("エラー: チームが見つかりません")
            return
        team_id = str(teams[0].get("id", ""))

    active = api.get_active_entry()
    if active:
        cur_task = active.get("task", {})
        cur_team_id = str(active.get("team", {}).get("id", active.get("team_id", "")))
        save_previous_task(cur_team_id, str(cur_task.get("id", "")), cur_task.get("title", ""))
        api.stop_entry(str(active["id"]))

    task_data = {
        "key": task_title,
        "team_id": team_id,
        "title": task_title,
        "url": "",
    }
    category_id = get_default_category_id()
    if category_id:
        task_data["parent_id"] = category_id

    entry = api._request("POST", "/time_entries", {"task": task_data})
    save_current_entry(str(entry["id"]), str(entry.get("time_trackable_id", "")), task_title, team_id)
    output(f"打刻開始: {task_title}")


def main():
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        output("エラー: コマンドが指定されていません")
        return

    arg = sys.argv[1].strip()
    token = get_token()

    if not token:
        output("エラー: トークンが未設定です")
        return

    api = TimeCrowdAPI(token)

    try:
        if arg == "end":
            do_end(api)
        elif arg.startswith("switch:"):
            parts = arg.split(":", 3)
            if len(parts) >= 4:
                do_switch(api, parts[1], parts[2], parts[3])
            else:
                output("エラー: タスク情報が不正です")
        elif arg.startswith("new:"):
            do_new_task(api, arg[4:])
        elif arg.startswith("set_category:"):
            parts = arg.split(":", 2)
            if len(parts) >= 3:
                cfg = load_config()
                cfg["default_category_id"] = parts[1]
                cfg["default_category_name"] = parts[2]
                save_config(cfg)
                output(f"デフォルトカテゴリ設定: {parts[2]}")
            else:
                output("エラー: カテゴリ情報が不正です")
        else:
            output(f"エラー: 不明なコマンド")
    except Exception as e:
        output(f"エラー: {e}")


if __name__ == "__main__":
    main()
