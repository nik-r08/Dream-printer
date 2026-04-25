import os
import tempfile
import unittest

from backend.trellis_client import _first_file_path


class TrellisClientTests(unittest.TestCase):
    def test_first_file_path_finds_nested_glb(self):
        with tempfile.TemporaryDirectory() as folder:
            glb_path = os.path.join(folder, "asset.glb")
            with open(glb_path, "wb") as file:
                file.write(b"glb")

            response = [{"path": os.path.join(folder, "preview.rrd")}, {"path": glb_path}]

            self.assertEqual(str(_first_file_path(response, suffixes=(".glb",))), glb_path)

    def test_first_file_path_returns_none_when_missing(self):
        self.assertIsNone(_first_file_path({"path": "missing.glb"}, suffixes=(".glb",)))


if __name__ == "__main__":
    unittest.main()
