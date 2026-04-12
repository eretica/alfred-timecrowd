import json
import os

BUNDLE_ID = "com.timecrowd.alfred"
WORKFLOW_DATA_DIR = os.path.join(
    os.path.expanduser("~"),
    "Library",
    "Application Support",
    "Alfred",
    "Workflow Data",
    BUNDLE_ID,
)
CONFIG_FILE = os.path.join(WORKFLOW_DATA_DIR, "config.json")
STATE_FILE = os.path.join(WORKFLOW_DATA_DIR, "state.json")


def _ensure_dir():
    os.makedirs(WORKFLOW_DATA_DIR, exist_ok=True)


def load_config() -> dict:
    _ensure_dir()
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save_config(data: dict):
    _ensure_dir()
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_token() -> str:
    # Alfred Workflow Configuration の環境変数を優先、なければconfig.jsonから
    env_token = os.environ.get("access_token", "")
    if env_token:
        return env_token
    return load_config().get("access_token", "")


def get_default_team_id() -> str:
    return str(load_config().get("default_team_id", ""))


def get_default_task_id() -> str:
    return str(load_config().get("default_task_id", ""))


def get_default_category_id() -> str:
    return str(load_config().get("default_category_id", ""))
