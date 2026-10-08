import unittest
from unittest.mock import Mock, patch

import server


class ListFilesTests(unittest.TestCase):
    def test_metadata_scope_is_enabled(self):
        self.assertIn(
            "https://www.googleapis.com/auth/drive.metadata.readonly", server.SCOPES
        )
        self.assertIn("https://www.googleapis.com/auth/drive.file", server.SCOPES)
        self.assertNotIn("https://www.googleapis.com/auth/drive", server.SCOPES)

    def test_lists_all_pages_in_target_folder(self):
        files = [
            {
                "id": str(index),
                "name": f"File {index}",
                "mimeType": "application/vnd.google-apps.presentation",
                "modifiedTime": "2026-10-08T00:00:00Z",
            }
            for index in range(101)
        ]
        drive = Mock()
        request = drive.files.return_value.list.return_value
        request.execute.side_effect = [
            {"files": files[:100], "nextPageToken": "next"},
            {"files": files[100:]},
        ]
        with patch.object(server, "_drive_service", return_value=drive), patch.object(
            server, "FOLDER_ID", "target-folder"
        ):
            self.assertEqual(server.list_files(), files)

        calls = drive.files.return_value.list.call_args_list
        self.assertEqual(len(calls), 2)
        self.assertIsNone(calls[0].kwargs["pageToken"])
        self.assertEqual(calls[1].kwargs["pageToken"], "next")
        for call in calls:
            self.assertEqual(
                call.kwargs["q"], "'target-folder' in parents and trashed = false"
            )
            self.assertEqual(
                call.kwargs["fields"],
                "nextPageToken,files(id,name,mimeType,modifiedTime)",
            )

    def test_empty_folder(self):
        drive = Mock()
        drive.files.return_value.list.return_value.execute.return_value = {}
        with patch.object(server, "_drive_service", return_value=drive):
            self.assertEqual(server.list_files(), [])

    def test_api_errors_are_not_hidden(self):
        drive = Mock()
        drive.files.return_value.list.return_value.execute.side_effect = RuntimeError(
            "API request failed"
        )
        with patch.object(server, "_drive_service", return_value=drive):
            with self.assertRaisesRegex(RuntimeError, "API request failed"):
                server.list_files()


if __name__ == "__main__":
    unittest.main()
