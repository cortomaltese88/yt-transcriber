import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import transcriber_backend as backend


class BackendDetectionTests(unittest.TestCase):
    def _executable(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        path.chmod(path.stat().st_mode | 0o111)
        return path

    def test_app_managed_cpu_only_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            app_bin = self._executable(root / "build/bin/whisper-cli")
            model = root / "models/ggml-base.bin"
            model.parent.mkdir(parents=True, exist_ok=True)
            model.write_text("mock", encoding="utf-8")

            with patch.object(backend, "WHISPER_BINS", {
                "vulkan": root / "missing-vulkan",
                "cuda": root / "missing-cuda",
                "cpu": root / "missing-cpu",
            }), patch.object(backend, "APP_WHISPER_CPP_BIN", app_bin), patch.object(
                backend, "_discover_available_whisper_model", return_value=model
            ), patch.object(backend, "_test_whisper_bin", return_value=True), patch.object(
                backend, "_ldd_mentions_vulkan", return_value=False
            ):
                detected = backend.detect_backend()

        self.assertEqual(detected["type"], "whisper_app_cpu")
        self.assertFalse(detected["fast"])
        self.assertEqual(detected["info"], "whisper.cpp (gestito dall'app) (CPU)")

    def test_app_managed_vulkan_capable_status_from_build_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            app_bin = self._executable(root / "build/bin/whisper-cli")
            vulkan_lib = root / "build/src/libggml-vulkan.so.0"
            vulkan_lib.parent.mkdir(parents=True, exist_ok=True)
            vulkan_lib.write_text("mock", encoding="utf-8")

            with patch.object(backend, "WHISPER_BINS", {
                "vulkan": root / "missing-vulkan",
                "cuda": root / "missing-cuda",
                "cpu": root / "missing-cpu",
            }), patch.object(backend, "APP_WHISPER_CPP_BIN", app_bin), patch.object(
                backend, "_discover_available_whisper_model", return_value=None
            ), patch.object(backend, "_test_whisper_bin", return_value=True), patch.object(
                backend, "_ldd_mentions_vulkan", return_value=False
            ):
                detected = backend.detect_backend()

        self.assertEqual(detected["type"], "whisper_app_vulkan")
        self.assertTrue(detected["fast"])
        self.assertEqual(detected["info"], "whisper.cpp (gestito dall'app) (GPU/Vulkan)")

    def test_gui_backend_status_label_does_not_add_cpu_to_vulkan_info(self):
        label = backend.backend_status_label({
            "info": "whisper.cpp (gestito dall'app) (GPU/Vulkan)",
            "fast": False,
        })

        self.assertEqual(label, "whisper.cpp (gestito dall'app) (GPU/Vulkan)")
        self.assertNotIn("(CPU)", label)

    def test_vulkan_candidate_falls_back_to_cpu_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vulkan_bin = self._executable(root / "build-vulkan/bin/whisper-cli")
            cpu_bin = self._executable(root / "build/bin/whisper-cli")

            def test_bin(path):
                return Path(path) == cpu_bin

            with patch.object(backend, "WHISPER_BINS", {
                "vulkan": vulkan_bin,
                "cuda": root / "missing-cuda",
                "cpu": cpu_bin,
            }), patch.object(backend, "APP_WHISPER_CPP_BIN", root / "missing-app"), patch.object(
                backend, "_discover_available_whisper_model", return_value=None
            ), patch.object(backend, "_test_whisper_bin", side_effect=test_bin):
                detected = backend.detect_backend()

        self.assertEqual(detected["type"], "whisper_cpu")
        self.assertEqual(detected["bin"], cpu_bin)
        self.assertFalse(detected["fast"])


if __name__ == "__main__":
    unittest.main()
