"""y-gdrive-mcp：FastMCP server，透過 Google service account 操作 Drive 資料夾。

第一階段最小骨架，提供兩個 MCP tool：
- list_files：列出目標資料夾內的檔案
- create_presentation：建立空白 Google Slides 簡報

啟動方式（stdio transport，給 MCP client 用）：
    uv run python server.py
"""

from __future__ import annotations

import os

from fastmcp import FastMCP
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ---------------------------------------------------------------------------
# 環境變數設定
# ---------------------------------------------------------------------------
# GOOGLE_SA_KEY_PATH：service account JSON 金鑰檔的完整路徑
# GDRIVE_FOLDER_ID：Google Drive「AI Workflow」資料夾的 ID（網址最後一段）
SA_KEY_PATH = os.environ.get("GOOGLE_SA_KEY_PATH", "")
FOLDER_ID = os.environ.get("GDRIVE_FOLDER_ID", "")

# drive.file 不涵蓋所有手動分享的既有檔案；metadata.readonly 讓列檔能讀取
# service account 有權存取的檔案中繼資料，不授予檔案內容的讀寫權限。
SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]

# 建立 MCP server 實例，名稱會顯示在 MCP client 上
mcp = FastMCP("y-gdrive-mcp")


def _drive_service():
    """建立 Google Drive API client（每次呼叫時才初始化，避免啟動時就要求金鑰存在）。

    這樣設計的原因：MCP client 啟動 server 時若金鑰路徑還沒設好，
    至少 server 能正常註冊 tool 清單，錯誤延後到真正呼叫 tool 時才發生。
    """
    if not SA_KEY_PATH or not FOLDER_ID:
        raise RuntimeError(
            "請先設定環境變數 GOOGLE_SA_KEY_PATH（金鑰路徑）與 GDRIVE_FOLDER_ID（資料夾 ID）"
        )
    # 用 service account 金鑰產生憑證，JWT flow，不需使用者互動授權
    creds = service_account.Credentials.from_service_account_file(
        SA_KEY_PATH, scopes=SCOPES
    )
    # cache_discovery=False：避免在本機快取 API discovery 文件造成警告
    return build("drive", "v3", credentials=creds, cache_discovery=False)


# ---------------------------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------------------------
@mcp.tool
def list_files() -> list[dict]:
    """列出目標資料夾（AI Workflow）直接包含的所有未刪除檔案。

    回傳每個檔案的 id、name、mimeType、modifiedTime。
    """
    drive = _drive_service()
    # Drive API 的查詢語法：parents 限定資料夾，trashed=false 排除垃圾桶
    folder_id = FOLDER_ID.replace("\\", "\\\\").replace("'", "\\'")
    query = f"'{folder_id}' in parents and trashed = false"
    files: list[dict] = []
    page_token: str | None = None
    # Drive 每次只回傳一頁；持續讀取 nextPageToken 才不會漏列檔案。
    while True:
        results = (
            drive.files()
            .list(
                q=query,
                fields="nextPageToken,files(id,name,mimeType,modifiedTime)",
                orderBy="modifiedTime desc",
                pageSize=100,
                pageToken=page_token,
            )
            .execute()
        )
        files.extend(results.get("files", []))
        page_token = results.get("nextPageToken")
        if not page_token:
            return files


@mcp.tool
def create_presentation(title: str) -> dict:
    """在目標資料夾中建立一份空白 Google Slides 簡報。

    參數：
        title：簡報標題
    回傳：
        簡報的 id 與瀏覽器網址（webViewLink）
    """
    drive = _drive_service()
    # 關鍵技巧：指定 mimeType 為 slides，Drive 就會建立成 Google 簡報而非一般檔案
    file_metadata = {
        "name": title,
        "mimeType": "application/vnd.google-apps.presentation",
        "parents": [FOLDER_ID],
    }
    file = (
        drive.files()
        .create(body=file_metadata, fields="id,name,webViewLink")
        .execute()
    )
    return {
        "id": file["id"],
        "name": file["name"],
        "url": file.get("webViewLink", ""),
    }


def main() -> None:
    # stdio transport：MCP client（如 Copilot App）透過標準輸入輸出與 server 溝通
    mcp.run()


if __name__ == "__main__":
    main()
