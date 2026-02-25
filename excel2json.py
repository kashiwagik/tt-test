# excel2json.py — 自動フォールバック対応版
import os
import json
from datetime import datetime, timedelta, timezone
import pandas as pd
from collections import defaultdict
import warnings
import yaml

warnings.filterwarnings("ignore", category=UserWarning)
pd.set_option("future.no_silent_downcasting", True)

# =========================================
# 設定読み込み
# =========================================
with open(os.path.join(os.path.dirname(__file__), "config.yaml"), encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

# --------- TEST_DATE (テスト時にここを編集) ----------
TEST_DATE = None
# TEST_DATE = "2026-03-22"
# TEST_DATE = "2026-04-10"
# ------------------------------------------------------

def get_today():
    if TEST_DATE:
        try:
            return datetime.strptime(TEST_DATE, "%Y-%m-%d")
        except Exception:
            pass
    return datetime.now()

# -------------------------
# Excel シート読み込み（1シート）
# -------------------------
def load_sheet(file_path, sheet_name, grade):
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl")
    except Exception as e:
        print(f"⚠ シート読み込みエラー：{file_path} / {sheet_name} → {e}")
        return []

    df = df[pd.to_datetime(df.iloc[:, 1], format="%Y-%m-%d", errors="coerce").notnull()]
    df = df.fillna("").infer_objects(copy=False)

    timetable = []
    for _, row in df.iterrows():
        date = pd.to_datetime(row.iloc[1]).strftime("%Y-%m-%d")
        comment = row.iloc[13] if len(row) > 13 else ""

        if comment:
            timetable.append({
                "grade": grade,
                "date": date,
                "period": 0,
                "courses": "",
                "room": "",
                "comment": comment
            })

        for p in range(1, 6):
            col_c = p * 2 + 1
            col_r = p * 2 + 2
            if col_r >= len(row):
                continue
            cname = row.iloc[col_c]
            room = row.iloc[col_r]
            if not cname:
                continue
            timetable.append({
                "grade": grade,
                "date": date,
                "period": p,
                "courses": cname,
                "room": room,
                "comment": ""
            })
    return timetable

# -------------------------
# 指定ファイル内のシート（全部）ロード
# -------------------------
def load_year_term(file_path, sheet_map):
    """
    sheet_map : { Excelシート名 : grade名 }
    """
    result = []
    for sheet, grade in sheet_map.items():
        part = load_sheet(file_path, sheet, grade)
        result.extend(part)
    return result

# -------------------------
# 助産統合（4年→4年助産補完）
# -------------------------
def add_schedule_to_josan(timetable):
    josan_cfg = CONFIG["josan"]
    source_grade = josan_cfg["source_grade"]
    target_grade = josan_cfg["target_grade"]

    source = {}
    target = {}
    for c in timetable:
        key = c["date"] + str(c["period"])
        if c["grade"] == source_grade:
            source[key] = c
        elif c["grade"] == target_grade:
            target[key] = c
    for key, c in source.items():
        if key in target:
            continue
        new_c = c.copy()
        new_c["grade"] = target_grade
        timetable.append(new_c)
    return timetable

# -------------------------
# JSON / info 保存
# -------------------------
def save_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✓ {path} を生成（{len(data)} 件）")

def save_info_json(file_path, out_path):
    if not os.path.exists(file_path):
        print(f"⚠ {file_path} がありません（空の info を作成）")
        save_json({"file_path": file_path, "last_modified": None}, out_path)
        return
    jst = timezone(timedelta(hours=9))
    ts = datetime.fromtimestamp(os.stat(file_path).st_mtime, tz=jst)
    save_json({"file_path": file_path, "last_modified": ts.strftime("%Y-%m-%d %H:%M:%S")}, out_path)

# -------------------------
# シート名マップ（config.yaml から構築）
# -------------------------
def sheet_names_for_year(year, term):
    yyyy = f"{year}年度"
    sheets_cfg = CONFIG["sheets"][term]
    return {
        entry["sheet"].format(yyyy=yyyy): entry["grade"]
        for entry in sheets_cfg
    }

# -------------------------
# ファイルに対象シートが存在するか確認
# -------------------------
def excel_has_any_sheet(file_path, sheet_map):
    if not os.path.exists(file_path):
        return False
    try:
        x = pd.ExcelFile(file_path)
        names = x.sheet_names
        return any(s in names for s in sheet_map.keys())
    except Exception:
        return False

# -------------------------
# 年度候補から最適な年度を探す
# -------------------------
def find_year_for_file(file_path, candidates, term):
    for y in candidates:
        smap = sheet_names_for_year(y, term)
        if excel_has_any_sheet(file_path, smap):
            return y
    return None

# -------------------------
# 自動年度フォールバック読み込み
# -------------------------
def load_for_term_with_fallback(file_path, preferred_year, term):
    candidates = [preferred_year, preferred_year - 1]
    found_year = find_year_for_file(file_path, candidates, term)
    if found_year is None:
        print(f"⚠ {file_path} に {preferred_year}/{preferred_year-1} の {term} シートが見つかりません（スキップ）")
        return []
    smap = sheet_names_for_year(found_year, term)
    print(f"→ {file_path} : 使用する{term}年度 = {found_year}年度")
    return load_year_term(file_path, smap)

# -------------------------
# 日付範囲フィルタ
# -------------------------
def filter_by_date_range(timetable, start_date, end_date):
    result = []
    for c in timetable:
        try:
            d = datetime.strptime(c["date"], "%Y-%m-%d")
        except Exception:
            continue
        if start_date <= d <= end_date:
            result.append(c)
    return result

# -------------------------
# 表示期間を算出
# -------------------------
def calc_date_range(today):
    nendo_start = CONFIG.get("nendo_start_month", 4)
    transition = CONFIG["transition"]
    t_month = transition["month"]
    t_day = transition["start_day"]

    if today.month < nendo_start:
        current_year = today.year - 1
    else:
        current_year = today.year

    if today.month == t_month and today.day >= t_day:
        # 切替期: 3/21 ～ 翌年度末 (翌年3/31)
        start_date = datetime(today.year, t_month, t_day)
        end_date = datetime(today.year + 1, 3, 31)
    else:
        # 通常期: 年度開始 (4/1) ～ 切替日前日 (3/20)
        start_date = datetime(current_year, nendo_start, 1)
        end_date = datetime(current_year + 1, t_month, t_day - 1)

    return current_year, start_date, end_date

# -------------------------
# メイン
# -------------------------
if __name__ == "__main__":
    today = get_today()
    print(f"◆ Today: {today.strftime('%Y-%m-%d')}")

    current_year, start_date, end_date = calc_date_range(today)
    next_year = current_year + 1
    print(f"◆ current_year={current_year}, next_year={next_year}")
    print(f"◆ 表示期間: {start_date.strftime('%Y-%m-%d')} ～ {end_date.strftime('%Y-%m-%d')}")

    # 全ファイル読み込み・連結
    TERM_MAP = {"spring": "前期", "fall": "後期"}
    SCOPE_YEAR = {"current": current_year, "next": next_year}
    all_timetable = []

    for entry in CONFIG["files"]:
        jp_term = TERM_MAP[entry["term"]]
        year = SCOPE_YEAR[entry["scope"]]
        all_timetable.extend(load_for_term_with_fallback(entry["save_name"], year, jp_term))

    all_timetable = add_schedule_to_josan(all_timetable)

    # 日付範囲でフィルタ
    filtered = filter_by_date_range(all_timetable, start_date, end_date)
    print(f"◆ フィルタ前: {len(all_timetable)} 件 → フィルタ後: {len(filtered)} 件")

    save_json(filtered, CONFIG["output"]["schedule_json"])
    for entry in CONFIG["files"]:
        save_info_json(entry["save_name"], entry["info_json"])
