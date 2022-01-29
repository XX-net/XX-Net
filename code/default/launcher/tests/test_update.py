import os.path
import unittest
import tempfile
import os

from launcher.update_from_github import download_file


class UpdateTest(unittest.TestCase):
    def test_download(self):
        tp = tempfile.gettempdir()
        fn = os.path.join(tp, "v4.txt")
        res = download_file("https://raw.githubusercontent.com/XX-net/XX-Net/master/code/default/update_v4.txt", fn)
        self.assertTrue(res)


