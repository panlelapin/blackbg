import io
from pathlib import Path
import runpy
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch


class DependencyAudit(unittest.TestCase):
    def test_empty_page_with_continuation_cannot_pass(self):
        script = Path(__file__).resolve().parents[1] / "tools/audit-dependencies.py"
        graph = "AUDIT build example:plugin:1\nAUDIT runtime example:library:1\n"
        pages = [io.BytesIO(b'{"results":[{}]}'),
                 io.BytesIO(b'{"results":[{"next_page_token":"more"}]}')]
        output = io.StringIO()
        with patch("subprocess.check_output", return_value=graph), \
                patch("urllib.request.urlopen", side_effect=pages), redirect_stdout(output):
            with self.assertRaises(SystemExit) as exit_status:
                runpy.run_path(str(script), run_name="__main__")
        self.assertIn("example:library:1", str(exit_status.exception.code))
        self.assertNotIn("runtime example:library:1 OK", output.getvalue())
