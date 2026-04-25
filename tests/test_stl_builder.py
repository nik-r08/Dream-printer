import os
import tempfile
import unittest

from backend.stl_builder import compile_prompt_to_spec, generate_stl_from_prompt


class StlBuilderTests(unittest.TestCase):
    def test_prompt_compiles_to_expected_object(self):
        spec = compile_prompt_to_spec("a cute robot toy with arms and legs, 85 mm", detail="fast", target_size_mm=70)

        self.assertEqual(spec["object_type"], "robot")
        self.assertEqual(spec["target_size_mm"], 85)
        self.assertIn("arms", spec["features"])
        self.assertIn("legs", spec["features"])

    def test_prompt_generates_stl_file(self):
        with tempfile.TemporaryDirectory() as folder:
            output_path = os.path.join(folder, "model.stl")
            result = generate_stl_from_prompt("a dragon sculpture with wings and spikes", output_path, detail="fast", target_size_mm=60)

            self.assertTrue(os.path.exists(output_path))
            self.assertGreater(result["triangle_count"], 0)
            with open(output_path, "r", encoding="utf-8") as file:
                content = file.read(128)
            self.assertTrue(content.startswith("solid dream_printer_model"))


if __name__ == "__main__":
    unittest.main()
