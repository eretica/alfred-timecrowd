# TimeCrowd Alfred Workflow

Alfred から [TimeCrowd](https://timecrowd.net) の打刻をワンアクションで操作できるワークフロー。

<img width="1536" height="1024" alt="検索結果と操作インターフェース" src="https://github.com/user-attachments/assets/9b171b0b-79ed-42ad-a06f-5ce4427ebbf8" />

## 機能

- タスク一覧をサジェスト表示し、選択するだけで打刻開始
- 自由入力で新規タスクを作成して打刻開始
- 打刻中のタスクを先頭に表示、Enter で停止
- デフォルトカテゴリの設定

## インストール

### Releases からインストール

1. [Releases](../../releases) から `TimeCrowd.alfredworkflow` をダウンロード
2. ダブルクリックで Alfred にインストール

### 手動インストール

```bash
git clone https://github.com/eretica/alfred-timecrowd.git
cd alfred-timecrowd
./build.sh
open TimeCrowd.alfredworkflow
```

## セットアップ

1. [TimeCrowd OAuth アプリケーション設定](https://timecrowd.net/oauth/applications) でアプリを登録し、「新しいトークン」でアクセストークンを発行
2. Alfred Preferences → Workflows → TimeCrowd → `Configure Workflow...` でアクセストークンを入力
3. `tc config` でデフォルトカテゴリを設定

## 使い方

| 入力 | 動作 |
|------|------|
| `tc` | タスク一覧を表示（打刻中なら先頭に表示） |
| `tc [検索]` | タスク名でフィルタ |
| `tc [自由入力]` | 新規タスクとして打刻開始 |
| `tc config` | デフォルトカテゴリを設定 |

## 技術仕様

- Python 3（macOS 標準の 3.9+ 対応）、外部依存なし
- TimeCrowd API v1 / v2
- タスク一覧は 60 秒キャッシュ
- 打刻中状態はバックグラウンドで非同期取得
