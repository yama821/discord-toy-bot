# Repository Guidelines

## ユーザーからの依頼事項

**この項目はユーザーが記述するため変更しないこと**

### リポジトリの説明
- wathematica_discord_bot という bot のための

## エージェント作業用
### プロジェクト構成とモジュール
- `src/app.py` が Bot のエントリーポイントで、`Cogs/` にはコマンドやリスナーごとの拡張を分割配置します。UI 関連は `src/UI/`、共通チェックは `checks.py`、例外は `exceptions.py`、SQLite と SQLAlchemy を扱う層は `database.py` と `model.py` に集約されています。
- 環境変数は `.env` で管理し、開発用コンテナ設定は `dev/docker-compose.yml` にまとまっています。SQLite ファイル (`src/database.db`) は永続ストレージなので、スキーマ変更時は必ずマイグレーション手順を共有してください。

### ビルド・テスト・開発コマンド
- `uv sync` : uv のロックファイルに従って依存関係を同期します。初回セットアップや依存追加後に必ず実行してください。
- `uv run app.py` : ローカルホストで Bot を起動します。`.env` に `DISCORD_TOKEN` が設定されていることを確認してください。
- `docker compose -f dev/docker-compose.yml up --build` : 開発コンテナをビルド・起動し、コンテナ内の `/app_root` で `uv run app.py` を実行します。
- `uv run ruff check` : フォーマットと静的解析の一次防衛線です。Push 前に必ず通すこと。

### コーディングスタイルと命名
- Python 3.12 / Ruff を前提に PEP 8 (4 スペース、120 文字以内を目安) を維持します。意図が曖昧になりやすい箇所には型ヒントを追加し、async 処理は `asyncio` のベストプラクティスを参照してください。
- ファイル名と関数名は `snake_case`、クラスと Cog は `PascalCase`、Discord のスラッシュコマンド名は短い英語動詞を推奨します。設定値は `config.py` に集約し、魔法値は避けてください。

### テストガイドライン
- 現在自動テストは未導入ですが、ロジック単体は pytest ベースで `tests/` ディレクトリを作成し `test_*.py` 形式で追加する方針です。導入後は `uv run pytest -q` を標準コマンドとし、重要機能は 80% 以上のカバレッジを維持してください。
- Bot 変更時は Staging サーバーで `/ping` など既存コマンドを手動確認し、DB を書き換える操作は SQLite のバックアップ (`cp src/database.db src/database.db.bak`) を取ってから試験してください。

### コミットとプルリクエスト
- Git 履歴は `feat: ...` 形式の Conventional Commits を採用しています。範囲を絞った論理的単位でコミットし、Breaking change を含む場合は `feat!:` などの表現にしてください。
- プルリクエストでは概要、動機、テスト結果、関連 Issue のリンクをテンプレート化して記載します。UI 変更や新しい Cog の追加時はスクリーンショットやコマンドのログを添付し、レビューアが `.env` なしでも挙動をイメージできるように書き残してください。

### セキュリティと設定メモ
- `DISCORD_TOKEN` や DB 接続文字列は必ず `.env` のみで管理し、リポジトリに含めないこと。コンテナ内では `UV_PROJECT_ENVIRONMENT=/venv` で仮想環境が固定されるため、手動で `python -m venv` を作らないでください。
- Discord 側の権限スコープを更新した場合は README とこのガイドも同時に更新し、Bot の Intent 設定 (`app.py` 内 `discord.Intents`) を忘れずに反映させましょう。環境変数のローテーション履歴も Issue で共有すると監査が容易になります。
