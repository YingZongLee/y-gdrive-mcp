# y-gdrive-mcp

FastMCP (Python) 實作的 MCP server，讓 MCP client（如 Copilot App）透過 Google service account 存取 Google Drive 中的「AI Workflow」資料夾，並建立／編輯 Google Slides、Docs、Sheets。

## 前置需求

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)（管理虛擬環境與依賴）
- Google Cloud service account JSON 金鑰（已啟用 Drive / Slides / Docs / Sheets API）
- Google Drive「AI Workflow」資料夾已以「編輯者」權限分享給 service account 的 email

## 安裝

```bash
uv sync
```

## 設定環境變數

複製範例檔並填入實際值：

```bash
cp .env.example .env
```

| 變數 | 說明 |
|------|------|
| `GOOGLE_SA_KEY_PATH` | service account JSON 金鑰檔的完整路徑 |
| `GDRIVE_FOLDER_ID` | 「AI Workflow」資料夾 ID，即網址 `https://drive.google.com/drive/folders/<這一段>` |

## 本機執行

```bash
export GOOGLE_SA_KEY_PATH=/path/to/service-account-key.json
export GDRIVE_FOLDER_ID=your_folder_id
uv run python server.py
```

Server 使用 **stdio transport**，由 MCP client 啟動並透過標準輸入輸出溝通，不是獨立 HTTP 服務。

## 註冊到 MCP client

在 MCP client 的設定（例如 `mcp.json`）加入：

```json
{
  "mcpServers": {
    "y-gdrive-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "/Users/yung/GithubProjects/y-gdrive-mcp", "python", "server.py"],
      "env": {
        "GOOGLE_SA_KEY_PATH": "/path/to/service-account-key.json",
        "GDRIVE_FOLDER_ID": "your_folder_id"
      }
    }
  }
}
```

## 目前提供的工具（第一階段）

| Tool | 說明 |
|------|------|
| `list_files` | 列出目標資料夾內的檔案（id、name、mimeType、modifiedTime） |
| `create_presentation` | 在資料夾中建立空白 Google Slides 簡報，回傳 id 與網址 |

### Service account 的權限與限制

- `list_files` 使用 `drive.metadata.readonly` 讀取 service account 有權存取的既有檔案中繼資料；僅有 `drive.file` 不足以涵蓋所有手動分享的檔案。此新增 scope 不授予檔案內容的讀寫權限。
- 列檔查詢仍限定 `GDRIVE_FOLDER_ID`，會讀取所有分頁，但不遞迴列出子資料夾內容。scope 本身不是單一資料夾的權限邊界，請僅分享必要資料給 service account。
- 修改 scope 後，請在 MCP client 停止並重新啟動此 server，讓新的憑證設定生效。不需要重新下載 JSON 金鑰。
- 如果仍回傳空清單，請確認資料夾 ID 正確、資料夾直接包含未刪除的檔案，且資料夾與檔案的分享權限允許 service account 存取。
- **個人 My Drive 建立檔案的限制**：將資料夾分享給 service account，不會讓新檔案使用資料夾擁有者的配額。service account 沒有一般使用者的 Drive 儲存配額，建立簡報可能回報 `403 storageQuotaExceeded`；這不代表你的個人 Drive 已滿。本階段保留原有建立工具，但新增列檔 scope 不會解決此限制。
- 要在個人 My Drive 建立新檔案，需另行改用使用者 OAuth；若保留 service account，可另行擴充支援 Workspace 共用雲端硬碟（Shared drive），它與一般分享資料夾不同。

參考：[Google Drive scopes](https://developers.google.com/workspace/drive/api/guides/api-specific-auth)、[檔案擁有權](https://developers.google.com/workspace/drive/api/guides/create-file#file_ownership)。

### 不使用金鑰的列檔測試

```bash
uv run python -m unittest discover -s tests
```

## 下一步可擴充的工具

- `add_slide`：在簡報中新增投影片（Slides API `presentations.batchUpdate`）
- `insert_text`：在投影片文字框插入文字
- `create_doc`：建立 Google Doc（mimeType `application/vnd.google-apps.document`）
- `append_text`：在 Doc 末尾附加文字（Docs API `documents.batchUpdate`）
- `create_sheet`：建立 Google Sheet（mimeType `application/vnd.google-apps.spreadsheet`）
- `read_range`：讀取 Sheet 範圍（Sheets API `spreadsheets.values.get`）
- `update_range`：寫入 Sheet 範圍（Sheets API `spreadsheets.values.update`）
