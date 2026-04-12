# TimeCrowd Alfred Workflow

## Alfred Workflow 開発ガイド

### info.plist — Script Filter 設定

#### scriptargtype（最重要）
- `0`: `{query}` が **Alfred によって展開される**。こちらを使う
- `1`: `{query}` は **リテラル文字列のまま渡される**。使ってはいけない

#### alfredfiltersresults
- `true`: スクリプト1回実行、Alfred がローカルフィルタ。**`{query}` は `(null)` として渡る**
- `false`: キーストロークごとにスクリプト再実行。`{query}` が展開される

`true` は API呼び出しなしの静的リストに最適。`false` は動的フィルタやサブコマンドが必要な場合に使う。

**パフォーマンス注意**: `false` でスクリプト内にAPI呼び出しがあると、毎キーストロークでリクエストが発生する。API結果はファイルにキャッシュし、スクリプトではキャッシュを読むだけにすること。

#### queuemode
- `1` (Wait): 前のスクリプト完了を待つ → 遅いスクリプトだと詰まる
- `2` (Terminate): 前のスクリプトを強制終了して最新の引数で再実行。API呼び出しがある場合はこちら

#### API呼び出しのベストプラクティス
bash の Script で curl を使い、Python にはパイプで渡す。Python 内で urllib を使うとタイムアウトや環境差異で問題が起きやすい。

```bash
# キャッシュ付き API 呼び出しパターン
cache="$alfred_workflow_cache/data.json"
mkdir -p "$alfred_workflow_cache"
if [ ! -f "$cache" ] || [ $(($(date +%s) - $(stat -f %m "$cache" 2>/dev/null || echo 0))) -gt 60 ]; then
  curl -s -m 5 -H "Authorization: Bearer $access_token" "https://api.example.com/data" > "$cache"
fi
/usr/bin/python3 "$PWD/main.py" "{query}" < "$cache"
```

### Post Notification
- `title`: 通知のタイトル（固定文字列）
- `text`: 通知の本文。`{query}`（Run Script の stdout）を設定すること。**未設定だとタイトルのみ表示される**
- macOS のシステム設定 → 通知 → Alfred で「バナー」に設定すると自動で消える

### スクリプト実行

#### パス指定
Alfred はスクリプトを Workflow ディレクトリを CWD として実行するが、`main.py` を直接参照できない場合がある。**絶対パス形式が安定**：

```bash
export PYTHONPATH="$PWD"
/usr/bin/python3 "$PWD/main.py" "{query}"
```

#### 環境変数
- `userconfigurationconfig` で定義した変数は環境変数として渡される
- `$access_token`（bash）/ `os.environ.get("access_token")`（Python）で取得
- `$alfred_workflow_cache`: Alfred 管理のキャッシュディレクトリ

#### Python 互換性
- macOS 標準: `/usr/bin/python3`（3.9.6）
- `dict | None` 等の Union 構文は 3.10+ → `from __future__ import annotations` で対応
- 外部パッケージは使わない（`urllib.request`, `json`, `os`, `sys` のみ）

### デプロイ

#### シンボリックリンクは使えない
`ln -s` で Workflow ディレクトリにリンクしても、Alfred がスクリプトを正しく実行できない場合がある。**`cp -R` で実ファイルをコピー**すること。

```bash
cp -R ~/workspace/me/timecrowd-alfred \
  ~/Library/Application\ Support/Alfred/Alfred.alfredpreferences/workflows/timecrowd-alfred
```

#### __pycache__ のクリア
スクリプト変更後は必ず `__pycache__` を削除。古いバイトコードが使われると変更が反映されない。

```bash
rm -rf ~/Library/Application\ Support/Alfred/Alfred.alfredpreferences/workflows/timecrowd-alfred/__pycache__
```

### デバッグ

1. Alfred Preferences → Workflows → 右上の虫アイコンでデバッグパネルを開く
2. ログで確認できること:
   - `Queuing argument '...'` — Script Filter に渡された引数
   - `Script with argv '...' finished` — スクリプト完了
   - JSON出力 — Script Filter の結果
   - `Passing output '...' to Run Script` — 選択されたアイテムの arg
   - `Passing output '...' to Post Notification` — 通知テキスト
3. ファイルログを書く場合、`tempfile.gettempdir()` は `/tmp` ではなく `/var/folders/.../T/` を返す

### ディレクトリ構成

| パス | 用途 |
|------|------|
| `~/Library/Application Support/Alfred/Alfred.alfredpreferences/workflows/{name}/` | Workflow 本体（info.plist, スクリプト等） |
| `~/Library/Application Support/Alfred/Workflow Data/{bundle_id}/` | 永続データ（config.json 等） |
| `$alfred_workflow_cache` | キャッシュ（Alfred 管理、自動クリーンアップ対象） |
| `prefs.plist` | Configure Workflow の入力値（**トークン含むため .gitignore 必須**） |

---

## TimeCrowd API

### v1（公式・ドキュメントあり）
- **Base URL**: `https://timecrowd.net/api/v1`
- **認証**: `Authorization: Bearer {access_token}`
- **ドキュメント**: https://timecrowd.net/apidoc
- **トークン発行**: https://timecrowd.net/oauth/applications → 「新しいトークン」ボタン

| 用途 | メソッド | パス |
|------|---------|------|
| タスク一覧 | GET | `/tasks?sort=user_usage&limit=25` |
| 打刻開始 | POST | `/teams/:team_id/tasks/:task_id/start` (body: `{}`) |
| 打刻停止 | PATCH | `/time_entries/:id/stop` |
| タスク作成+打刻 | POST | `/time_entries` (body: `{task: {key, team_id, title, url}}`) |
| チーム一覧 | GET | `/teams` |

**注意**: `GET /time_entries?stopped_at=0` は **タイムアウトする。使用不可。**

### v2（非公開・内部API）
- **Base URL**: `https://timecrowd.net/api/v2`
- **ドキュメントなし**（Web版が使用する内部API）
- 打刻中タスクの取得に必要

| 用途 | メソッド | パス | レスポンス |
|------|---------|------|-----------|
| 打刻中取得 | GET | `/user` | `time_entry` フィールド（`stopped_at` が `null` なら打刻中） |
