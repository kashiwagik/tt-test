#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
from azure.identity import ClientSecretCredential
from datetime import datetime
import dotenv

dotenv.load_dotenv()

# =========================================
# SharePoint 設定（環境変数から取得）
# =========================================
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

SITE_HOST = "ncnj.sharepoint.com"
SITE_PATH = "/sites/staff_sharedfolders"
GRAPH_BASE = "https://graph.microsoft.com/v1.0"

# 保存名は excel2json.py と一致させる
nendo = datetime.now().year if datetime.now().month > 3 else datetime.now().year - 1
wareki = nendo - 2018
FILES = [
    (
        "spring",
        f"140.スケジュール・時間割/{nendo}(R{wareki})年度 時間割/【{nendo}・04～09月 前期】全学年時間割.xlsx",
        "schedule_spring_CURRENT.xlsx",
    ),
    (
        "fall",
        f"140.スケジュール・時間割/{nendo}(R{wareki})年度 時間割/【{nendo}・10～03月 後期】全学年時間割.xlsx",
        "schedule_fall_CURRENT.xlsx",
    ),
    (
        "spring",
        f"140.スケジュール・時間割/{nendo + 1}R({wareki + 1})年度 時間割/【{nendo + 1}・04～09月 前期】全学年時間割.xlsx",
        "schedule_spring_NEXT.xlsx",
    ),
    (
        "fall",
        f"140.スケジュール・時間割/{nendo + 1}R({wareki + 1})年度 時間割/【{nendo + 1}・10～03月 後期】全学年時間割.xlsx",
        "schedule_fall_NEXT.xlsx",
    ),
]


# =========================================
# SharePoint authentication
# =========================================
def get_token():
    credential = ClientSecretCredential(
        tenant_id=TENANT_ID, client_id=CLIENT_ID, client_secret=CLIENT_SECRET
    )
    token = credential.get_token("https://graph.microsoft.com/.default")
    return token.token


# =========================================
# Graph API: サイトID取得
# =========================================
def get_site_id(token):
    url = f"{GRAPH_BASE}/sites/{SITE_HOST}:{SITE_PATH}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"✗ サイトID取得失敗: {resp.status_code}")
        print(resp.text[:500])
        raise SystemExit(1)
    site_id = resp.json()["id"]
    print(f"✓ サイトID: {site_id}")
    return site_id


# =========================================
# ダウンロード（Graph API パスベース）
# =========================================
def download_file(site_id, file_path, save_path, token):
    url = f"{GRAPH_BASE}/sites/{site_id}/drive/root:/{file_path}:/content"
    headers = {"Authorization": f"Bearer {token}"}
    print(f"→ Downloading: {file_path}")

    resp = requests.get(url, headers=headers)

    if resp.status_code != 200:
        print(f"  ✗ Failed: {resp.status_code}")
        print(f"  {resp.text[:300]}")
        return False

    with open(save_path, "wb") as f:
        f.write(resp.content)

    print(f"  ✓ Saved to {save_path}")
    return True


# =========================================
# メイン処理
# =========================================
def main():
    token = get_token()
    site_id = get_site_id(token)

    for term, file_path, save_name in FILES:
        print(f"=== {term} {save_name} ===")
        download_file(site_id, file_path, save_name, token)


if __name__ == "__main__":
    main()
