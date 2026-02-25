# 年度移行に関する処理まとめ

## 概要

このシステムでは「年度」を **4月〜翌3月** の区切りで扱う。
年度移行は主に **3月下旬（21日〜31日）** に発生し、旧年度の後期データと新年度のデータを混合表示する。

年度判定ロジックは `download_commit.py` と `excel2json.py` の2箇所に存在する。

---

## 1. 年度の判定ロジック

### 共通ルール（download_commit.py:24-35 / excel2json.py:213-217）

```
1月〜3月に実行 → current_year = 前年, next_year = 当年
4月〜12月に実行 → current_year = 当年, next_year = 翌年
```

| 実行日 | current_year | next_year |
|--------|-------------|-----------|
| 2025年11月 | 2025 | 2026 |
| 2026年2月 | 2025 | 2026 |
| 2026年4月 | 2026 | 2027 |

### 例：2026年3月1日に実行した場合

- `current_year = 2025`（2025年度 = 現在進行中の年度）
- `next_year = 2026`（2026年度 = 次に始まる年度）

---

## 2. Excelファイルの管理（download_commit.py）

### ダウンロードされるファイル

SharePoint から4つの Excel ファイルをダウンロードし、固定名で保存する。

| ローカルファイル名 | 意味 | SharePoint のソース例（2025年度の場合） |
|-------------------|------|----------------------------------------|
| `schedule_spring_CURRENT.xlsx` | 当年度・前期 | `【2025・04～09月 前期】全学年時間割.xlsx` |
| `schedule_fall_CURRENT.xlsx` | 当年度・後期 | `【2025・10～03月 後期】全学年時間割.xlsx` |
| `schedule_spring_NEXT.xlsx` | 次年度・前期 | `【2026・04～09月 前期】全学年時間割.xlsx` |
| `schedule_fall_NEXT.xlsx` | 次年度・後期 | `【2026・10～03月 後期】全学年時間割.xlsx` |

### SharePoint URL の構成（download_commit.py:41-53）

```
https://ncnj.sharepoint.com/:x:/s/staff_sharedfolders/{year}(R{year-2018})年度時間割/{ファイル名}
```

- `R{year-2018}` は令和年号への変換（例：2025 → R7）

---

## 3. Excel → JSON 変換時の年度処理（excel2json.py）

### 3.1 モード判定（excel2json.py:219-223）

実行日によって2つのモードに分岐する。

```python
if today.month == 3 and 21 <= today.day <= 31:
    mode = "mix"         # 年度移行期間
else:
    mode = "current_only" # 通常期間
```

| 期間 | モード | 説明 |
|------|--------|------|
| 4月1日〜3月20日 | `current_only` | 当年度のデータのみ表示 |
| 3月21日〜3月31日 | `mix` | 旧年度の残りと新年度を混合表示 |

### 3.2 current_only モード（通常）

当年度の前期・後期データをそのまま読み込む。

```
読み込み対象：
  ├── schedule_spring_CURRENT.xlsx → current_year の前期シート
  └── schedule_fall_CURRENT.xlsx   → current_year の後期シート
```

### 3.3 mix モード（年度移行期：3/21〜3/31）

旧年度の後期データから **3月21日〜31日の分だけ** を抽出し、新年度のデータと結合する。

```
読み込み対象：
  ├── schedule_fall_CURRENT.xlsx   → current_year の後期シート → 3/21〜3/31 のみ抽出
  ├── schedule_spring_NEXT.xlsx    → next_year の前期シート
  └── schedule_fall_NEXT.xlsx      → next_year の後期シート
```

#### 3月データのフィルタ処理（excel2json.py:193-204）

```python
def filter_last_march_only(timetable, year):
    start = datetime(year, 3, 21)
    end = datetime(year, 3, 31)
    # start <= date <= end のデータのみ残す
```

- `year` には `current_year`（= 実行年 - 1）が渡される
- 例：2026年3月25日に実行 → `current_year=2025` → 2025年度の後期ファイルから 2026-03-21〜2026-03-31 を抽出
  - **注意**: `filter_last_march_only` に渡される `year` は `current_year`（2025）だが、フィルタの `datetime(year, 3, 21)` は `datetime(2025, 3, 21)` になる。旧年度の後期は翌年3月のデータを含むはずなので、ここに **不整合の可能性** がある（後述）。

### 3.4 年度フォールバック機能（excel2json.py:170-188）

Excel ファイル内のシート名で年度を自動判別する仕組み。

```python
def load_for_term_with_fallback(file_path, preferred_year, term):
    candidates = [preferred_year, preferred_year - 1]
    # preferred_year のシートが見つからなければ、1年前のシートを試す
```

- シート名の形式：`{year}年度(1年前期)` など
- `preferred_year` のシートがなければ `preferred_year - 1` で再試行
- 年度移行期に新年度のシートがまだ存在しないケースに対応

### 3.5 シート名と年度の対応（excel2json.py:127-152）

```
例：2025年度・前期の場合
  "2025年度(1年前期)" → "1年生"
  "2025年度(2年前期)" → "2年生"
  "2025年度(3年前期)" → "3年生"
  "2025年度(4年前期)" → "4年生"
  "2025年度(助産前期)" → "4年助産"
  "2025年度(M1前期)" → "M1"
  "2025年度(M2前期)" → "M2"
  "2025年度(D1前期)" → "D1"
  "2025年度(D23前期)" → "D2/D3"
```

---

## 4. GitHub Actions ワークフローとの関連

### download_commit.yml（Excel ダウンロード）

- **スケジュール**: 平日 JST 6:00〜21:00（1時間ごと）
- 年度判定は `download_commit.py` の `guess_years()` で自動実行
- 4つのファイル（CURRENT前期/後期 + NEXT前期/後期）を毎回ダウンロード

### run_on_excel_update.yml（JSON 変換）

- **トリガー**: Excel ファイル（`schedule_*_CURRENT.xlsx`, `schedule_*_NEXT.xlsx`）が push されたとき
- `excel2json.py` を実行し、モード判定に基づいて `schedule.json` を生成

---

## 5. フロントエンド（script.js）

フロントエンド側には **年度判定のロジックは存在しない**。

- `schedule.json` を読み込んで表示するのみ
- 年度の切り替えはバックエンド（`excel2json.py`）が `schedule.json` の内容で制御
- ユーザーは日付ナビゲーションで任意の日を表示できるが、データが存在する範囲のみ表示される

---

## 6. 年度移行のタイムライン

```
        3/20            3/21                     4/1
─────────┼───────────────┼────────────────────────┼──────────
 current_only           mix モード               current_only
 (旧年度のみ)          (旧年度3/21-31          (新年度のみ)
                        + 新年度 前期/後期)
```

### 具体例：2025年度 → 2026年度の移行

| 日付 | current_year | next_year | モード | schedule.json の内容 |
|------|-------------|-----------|--------|---------------------|
| 2026-03-01 | 2025 | 2026 | current_only | 2025年度の前期＋後期 |
| 2026-03-21 | 2025 | 2026 | mix | 2025年度後期の3/21-31 + 2026年度の前期＋後期 |
| 2026-03-31 | 2025 | 2026 | mix | 同上 |
| 2026-04-01 | 2026 | 2027 | current_only | 2026年度の前期＋後期 |

---

## 7. 潜在的な問題点・注意事項

### 7.1 filter_last_march_only の year パラメータ

`excel2json.py:242` で `filter_last_march_only(curr_fall_all, current_year)` が呼ばれる。

```python
curr_march = filter_last_march_only(curr_fall_all, current_year)
```

- `current_year` が例えば `2025` の場合、フィルタ範囲は `2025-03-21〜2025-03-31`
- しかし、2025年度の後期ファイルに含まれる3月データは `2026-03-21〜2026-03-31` のはず
- **`current_year + 1`（= 2026）が正しい可能性がある**

### 7.2 NEXT ファイルの存在タイミング

- 新年度のファイルが SharePoint にアップロードされるタイミングによっては、`schedule_spring_NEXT.xlsx` 等が存在しない・空の場合がある
- フォールバック機能（`preferred_year - 1` を試行）で対処されているが、完全にカバーできるかは SharePoint 側の運用次第

### 7.3 CI/CD の Python バージョン不一致

- `download_commit.yml`: Python 3.9
- `run_on_excel_update.yml`: Python 3.12
- `pyproject.toml`: `requires-python = ">=3.13"`
- ワークフローで使用するバージョンが `pyproject.toml` の要件を満たしていない
