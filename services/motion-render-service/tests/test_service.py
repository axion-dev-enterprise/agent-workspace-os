"""Unit tests for Motion Render Service API."""
import unittest
from pathlib import Path
import sys

SERVICE_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = Path("C:/workspace")
sys.path.insert(0, str(WORKSPACE_ROOT / "packages" / "motion-engine" / "src"))
sys.path.insert(0, str(SERVICE_ROOT / "src"))

from fastapi.testclient import TestClient
from main import app


class TestMotionRenderService(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["ffmpeg_detected"])
        self.assertIn("autonomous-core", data["available_scenes"])

    def test_scenes_endpoint(self):
        res = self.client.get("/scenes")
        self.assertEqual(res.status_code, 200)
        scenes = res.json()
        self.assertTrue(len(scenes) >= 1)
        self.assertEqual(scenes[0]["id"], "autonomous-core")

    def test_videos_endpoint(self):
        res = self.client.get("/videos")
        self.assertEqual(res.status_code, 200)
        videos = res.json()
        self.assertIsInstance(videos, list)
        # Should list our preserved videos
        filenames = [v["name"] for v in videos]
        self.assertIn("axion-the-autonomous-core.mp4", filenames)

    def test_index_html_endpoint(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("AXION MOTION STUDIO", res.text)


if __name__ == "__main__":
    unittest.main()
