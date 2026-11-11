import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cv2
import numpy as np
from PIL import Image
from frameveil.engine import Settings, Timeline, compose, probe


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.red = str(self.root / "红色.png")
        self.blue = str(self.root / "蓝色.png")
        Image.new("RGB", (100, 50), (255, 0, 0)).save(self.red)
        Image.new("RGB", (100, 50), (0, 0, 255)).save(self.blue)
        self.timeline = Timeline(Settings(width=100, height=50, interval=1, transition=0))

    def tearDown(self):
        self.timeline.close()
        self.temp.cleanup()

    def test_slideshow_pause_loop_and_end(self):
        t = self.timeline
        t.playlist([self.red, self.blue])
        np.testing.assert_array_equal(t.frame(0)[25, 50], [255, 0, 0])
        t.paused = True
        t.frame(10)
        self.assertEqual(t.index, 0)
        t.paused = False
        np.testing.assert_array_equal(t.frame(1.01)[25, 50], [0, 0, 255])
        t.frame(1.01)
        self.assertEqual(t.index, 0)
        t.settings.loop = False
        t.select(1)
        t.frame(1.01)
        self.assertTrue(t.finished)
        self.assertEqual(t.index, 1)

    def test_blackout_and_resume(self):
        t = self.timeline
        t.playlist([self.red])
        t.black = True
        self.assertFalse(t.frame(0).any())
        t.black = False
        self.assertEqual(int(t.frame(0)[20, 20, 0]), 255)

    def test_crossfade_is_between_source_frames(self):
        t = self.timeline
        t.settings.interval = 5
        t.settings.transition = 1
        t.playlist([self.red, self.blue])
        t.frame(0)
        t.select(1)
        out = t.frame(.5)
        np.testing.assert_allclose(out[25, 50], [128, 0, 128], atol=1)
        np.testing.assert_array_equal(t.frame(.6)[25, 50], [0, 0, 255])

    def test_mirror_and_aspect_ratio(self):
        rgb = np.zeros((100, 50, 3), np.uint8)
        rgb[:, :25] = [255, 0, 0]
        rgb[:, 25:] = [0, 255, 0]
        s = Settings(width=100, height=100, background="#112233")
        out = compose(rgb, s)
        np.testing.assert_array_equal(out[0, 0], [17, 34, 51])
        np.testing.assert_array_equal(out[50, 30], [255, 0, 0])
        s.mirror = True
        out = compose(rgb, s)
        np.testing.assert_array_equal(out[50, 30], [0, 255, 0])
        s.fit = "cover"
        out = compose(rgb, s)
        self.assertEqual(out.shape, (100, 100, 3))
        self.assertTrue(out.flags.c_contiguous)

    def make_video(self):
        path = str(self.root / "测试视频.avi")
        writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"MJPG"), 10, (100, 50))
        self.assertTrue(writer.isOpened())
        for i in range(20):
            bgr = np.full((50, 100, 3), [i * 10, 0, 255 - i * 10], np.uint8)
            writer.write(bgr)
        writer.release()
        return path

    def test_video_unicode_seek_speed_and_loop(self):
        path = self.make_video()
        self.assertAlmostEqual(probe(path)["duration"], 2)
        t = self.timeline
        t.playlist([path])
        first = t.frame(0).copy()
        t.settings.speed = 2
        t.frame(.5)
        self.assertAlmostEqual(t.elapsed, 1)
        self.assertLess(t.video_rgb[25, 50, 0], first[25, 50, 0])
        t.seek(0)
        np.testing.assert_allclose(t.frame(0)[25, 50], first[25, 50], atol=3)
        t.frame(1.1)
        self.assertEqual(t.index, 0)
        self.assertLess(t.elapsed, .1)
        t.settings.loop = False
        t.frame(1.1)
        self.assertTrue(t.finished)
        self.assertGreater(int(t.frame(0)[25, 50, 2]), 170)

    def test_shuffle_and_empty_list(self):
        t = self.timeline
        t.settings.shuffle = True
        t.playlist([self.red, self.blue])
        for _ in range(10):
            before = t.index
            t.frame(1.1)
            self.assertNotEqual(t.index, before)
        t.playlist([])
        self.assertEqual(t.index, -1)
        self.assertFalse(t.frame(0).any())

    def test_paused_selection_shows_new_source(self):
        t = self.timeline
        t.settings.transition = 1
        t.playlist([self.red, self.blue])
        t.frame(0)
        t.paused = True
        t.select(1)
        np.testing.assert_array_equal(t.frame(0)[25, 50], [0, 0, 255])

    def test_shuffle_without_loop_finishes_one_round(self):
        t = self.timeline
        t.settings.shuffle = True
        t.settings.loop = False
        t.playlist([self.red, self.blue])
        t.frame(1.1)
        self.assertEqual(t.index, 1)
        t.frame(1.1)
        self.assertTrue(t.finished)

    def test_corrupt_and_unsupported_media(self):
        invalid = self.root / "bad.mp4"
        invalid.write_bytes(b"invalid")
        with self.assertRaises(ValueError):
            probe(str(invalid))
        with self.assertRaises(ValueError):
            probe(str(self.root / "animation.gif"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
