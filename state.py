import json
import os

from config import STATE_FILE, _ensure_dir


def load_state() -> dict:
    _ensure_dir()
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def save_state(data: dict):
    _ensure_dir()
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_previous_task(team_id: str, task_id: str, task_title: str):
    st = load_state()
    st["previous_team_id"] = team_id
    st["previous_task_id"] = task_id
    st["previous_task_title"] = task_title
    save_state(st)


def get_previous_task() -> dict:
    st = load_state()
    tid = st.get("previous_task_id")
    if not tid:
        return {}
    return {
        "team_id": st.get("previous_team_id", ""),
        "task_id": tid,
        "task_title": st.get("previous_task_title", ""),
    }


def save_current_entry(entry_id: str, task_id: str, task_title: str, team_id: str):
    st = load_state()
    st["current_entry_id"] = entry_id
    st["current_task_id"] = task_id
    st["current_task_title"] = task_title
    st["current_team_id"] = team_id
    save_state(st)


def get_current_entry() -> dict:
    st = load_state()
    eid = st.get("current_entry_id")
    if not eid:
        return {}
    return {
        "entry_id": eid,
        "task_id": st.get("current_task_id", ""),
        "task_title": st.get("current_task_title", ""),
        "team_id": st.get("current_team_id", ""),
    }


def clear_current_entry():
    st = load_state()
    for key in ["current_entry_id", "current_task_id", "current_task_title", "current_team_id"]:
        st.pop(key, None)
    save_state(st)
