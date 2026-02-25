# プロジェクト依存関係一覧

## プロジェクト概要

| 項目 | 内容 |
|------|------|
| プロジェクト名 | timetable |
| バージョン | 0.1.0 |
| 説明 | Time Table for NCN 2025 |
| Python バージョン | >= 3.13 |

---

## 1. Python 依存パッケージ（バックエンド）

### 直接依存（pyproject.toml で定義）

| パッケージ | バージョン | 用途 |
|-----------|-----------|------|
| pandas | >= 2.2.3 | Excel データの読み込み・加工・変換 |
| openpyxl | >= 3.1.5 | Excel (.xlsx) ファイルの読み書き |

### 間接依存（requirements.txt に記載・pandas/openpyxl の依存先）

| パッケージ | バージョン | 用途 |
|-----------|-----------|------|
| numpy | 2.2.4 | pandas の数値計算基盤 |
| python-dateutil | 2.9.0.post0 | 日付・時間の解析処理 |
| pytz | 2025.2 | タイムゾーン情報 |
| tzdata | 2025.2 | IANA タイムゾーンデータベース |
| six | 1.17.0 | Python 2/3 互換ユーティリティ（python-dateutil の依存） |
| et-xmlfile | 2.0.0 | openpyxl の XML ファイル処理用 |

### CI/CD 専用依存（ワークフロー内で pip install）

| パッケージ | 使用ワークフロー | 用途 |
|-----------|-----------------|------|
| azure-identity | download_commit.yml | SharePoint へのAzure AD認証 |
| requests | download_commit.yml | SharePoint API への HTTP リクエスト |
| python-dotenv | download_commit.yml, run_on_excel_update.yml | 環境変数管理 |

---

## 2. フロントエンド依存（CDN経由）

| ライブラリ | バージョン | CDN URL | 用途 |
|-----------|-----------|---------|------|
| jQuery | 3.7.1 | cdnjs.cloudflare.com/ajax/libs/jquery/3.7.1/jquery.min.js | DOM操作・イベント処理 |
| Font Awesome | 6.4.0 | cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css | アイコン表示 |

---

## 3. GitHub Actions 依存

| アクション | バージョン | 使用ワークフロー | 用途 |
|-----------|-----------|-----------------|------|
| actions/checkout | v3, v4 | 全ワークフロー | リポジトリのチェックアウト |
| actions/setup-python | v4 | 全ワークフロー | Python 環境構築 |

---

## 4. 外部サービス依存

| サービス | 用途 | 認証方式 |
|---------|------|---------|
| SharePoint (ncnj.sharepoint.com) | Excel ファイルのダウンロード元 | Azure AD (Client Credentials) |
| GitHub Pages | Web サイトのホスティング | - |
| GitHub Actions | CI/CD 自動化 | GitHub Secrets |
| cdnjs (Cloudflare) | フロントエンドライブラリ配信 | - |

---

## 5. GitHub Secrets（環境変数）

| シークレット名 | 用途 |
|---------------|------|
| TENANT_ID | Azure AD テナント ID |
| CLIENT_ID | Azure AD アプリケーション ID |
| CLIENT_SECRET | Azure AD クライアントシークレット |

---

## 6. 依存関係図

```
timetable (Python 3.13)
│
├── excel2json.py（Excel → JSON 変換）
│   ├── pandas >= 2.2.3
│   │   ├── numpy
│   │   ├── python-dateutil
│   │   │   └── six
│   │   ├── pytz
│   │   └── tzdata
│   └── openpyxl >= 3.1.5
│       └── et-xmlfile
│
├── download_commit.py（SharePoint ダウンロード）
│   ├── azure-identity
│   ├── requests
│   └── python-dotenv
│
├── docs/（フロントエンド - GitHub Pages）
│   ├── jQuery 3.7.1 (CDN)
│   └── Font Awesome 6.4.0 (CDN)
│
└── .github/workflows/（CI/CD）
    ├── actions/checkout@v3-v4
    └── actions/setup-python@v4
```

---

## 7. パッケージマネージャ

| ツール | ファイル | 用途 |
|-------|---------|------|
| uv | uv.lock | ロックファイルによる再現可能なインストール |
| pip | requirements.txt | CI/CD での依存インストール |

---

## 8. 注意事項

- `pyproject.toml` と `requirements.txt` で管理される依存は **excel2json.py** 用
- `download_commit.py` の依存（azure-identity, requests）は `requirements.txt` に含まれず、ワークフロー内で直接 pip install される
- フロントエンドライブラリは CDN から配信されるため、ローカルインストール不要
- `run_on_excel_update.yml` では Python 3.12、`download_commit.yml` では Python 3.9 が使用されており、`pyproject.toml` の要件（>= 3.13）と不一致がある
