import tempfile
import unittest
from pathlib import Path
import struct
import sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from frameveil.native_camera import FrameTransport, HEADER_SIZE, CAPACITY, MAGIC


class NativeTransportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'frame.dat'
        with self.path.open('wb') as f:
            f.truncate(HEADER_SIZE + CAPACITY)
        self.transport = FrameTransport(self.path)

    def tearDown(self):
        self.transport.close()
        self.temp.cleanup()

    def test_packet_layout_color_and_sequence(self):
        rgb = np.full((16, 20, 3), [23, 87, 192], np.uint8)
        self.transport.write(rgb)
        header = struct.unpack_from('<6IQI', self.transport.mapping)
        self.assertEqual(header[:6], (MAGIC, 1, 20, 16, 80, 1280))
        self.assertGreater(header[6], 0)
        self.assertEqual(header[7] % 2, 0)
        self.assertEqual(self.transport.mapping[HEADER_SIZE:HEADER_SIZE+4], bytes([192,87,23,255]))
        sequence = header[7]
        self.transport.write(rgb)
        self.assertEqual(struct.unpack_from('<I', self.transport.mapping, 32)[0], sequence + 2)

    def test_reject_oversize(self):
        with self.assertRaises(ValueError):
            self.transport.write(np.zeros((1081, 1920, 3), np.uint8))

    def test_close_invalidates_and_erases_frame(self):
        self.transport.write(np.full((16, 16, 3), 255, np.uint8))
        self.transport.close()
        data = self.path.read_bytes()
        self.assertEqual(struct.unpack_from('<Q', data, 24)[0], 0)
        self.assertFalse(any(data[HEADER_SIZE:]))

    def test_single_producer(self):
        with self.assertRaises(RuntimeError):
            FrameTransport(self.path)


if __name__ == '__main__':
    unittest.main(verbosity=2)
