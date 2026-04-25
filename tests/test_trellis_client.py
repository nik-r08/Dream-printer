import os
import tempfile
import unittest
from pathlib import Path

from backend.trellis_client import TrellisSettings, _first_file_path, _generate_trellis_asset_with_client


class FakeCurrentSpaceClient:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.calls = []

    def predict(self, *args, api_name):
        self.calls.append(api_name)
        if api_name == "/generate_text_to_image":
            return self._write("concept.png", b"image")
        if api_name == "/generate_3d_from_image":
            return {"latent": "state"}, "<div>preview</div>", self._write("processed.png", b"processed")
        if api_name == "/extract_glb":
            return self._write("asset.glb", b"glb"), self._write("asset.glb", b"glb")
        raise AssertionError(f"Unexpected api call: {api_name}")

    def _write(self, name, content):
        path = self.folder / name
        path.write_bytes(content)
        return str(path)


class FakeLegacySpaceClient(FakeCurrentSpaceClient):
    def predict(self, *args, api_name):
        self.calls.append(api_name)
        if api_name == "/generate_text_to_image":
            raise RuntimeError("endpoint not available")
        if api_name == "/generate_txt2img":
            return self._write("legacy_concept.png", b"image")
        if api_name == "/preprocess_image":
            raise RuntimeError("optional endpoint not available")
        if api_name == "/generate_3d":
            return self._write("legacy_asset.glb", b"glb")
        raise AssertionError(f"Unexpected api call: {api_name}")


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

    def test_current_space_flow_extracts_glb(self):
        with tempfile.TemporaryDirectory() as folder:
            client = FakeCurrentSpaceClient(folder)
            result = _generate_trellis_asset_with_client(
                client,
                lambda path: path,
                "a robot toy",
                Path(folder) / "out",
                TrellisSettings(seed=123, randomize_seed=False),
            )

            self.assertEqual(
                client.calls,
                ["/generate_text_to_image", "/generate_3d_from_image", "/extract_glb"],
            )
            self.assertTrue(os.path.exists(result["glb_path"]))
            self.assertEqual(result["seed"], 123)
            self.assertIsNotNone(result["stl_error"])

    def test_legacy_space_flow_is_used_when_current_api_is_missing(self):
        with tempfile.TemporaryDirectory() as folder:
            client = FakeLegacySpaceClient(folder)
            result = _generate_trellis_asset_with_client(
                client,
                lambda path: path,
                "a robot toy",
                Path(folder) / "out",
                TrellisSettings(seed=7, randomize_seed=False),
            )

            self.assertEqual(
                client.calls,
                ["/generate_text_to_image", "/generate_txt2img", "/preprocess_image", "/generate_3d"],
            )
            self.assertTrue(os.path.exists(result["glb_path"]))
            self.assertEqual(result["seed"], 7)


if __name__ == "__main__":
    unittest.main()
