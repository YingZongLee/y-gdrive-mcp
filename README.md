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

## 下一步可擴充的工具

- `add_slide`：在簡報中新增投影片（Slides API `presentations.batchUpdate`）
- `insert_text`：在投影片文字框插入文字
- `create_doc`：建立 Google Doc（mimeType `application/vnd.google-apps.document`）
- `append_text`：在 Doc 末尾附加文字（Docs API `documents.batchUpdate`）
- `create_sheet`：建立 Google Sheet（mimeType `application/vnd.google-apps.spreadsheet`）
- `read_range`：讀取 Sheet 範圍（Sheets API `spreadsheets.values.get`）
- `update_range`：寫入 Sheet 範圍（Sheets API `spreadsheets.values.update`）
