import time
import threading
from unittest import TestCase
# from simple_queue import Queue
from  queue import Queue


class TestSimpleQueue(TestCase):

    @staticmethod
    def pub(q, x):
        time.sleep(2)
        print("put x")
        q.put(x)

    def test_basic(self):
        q1 = Queue()
        q1.put("a")
        v = q1.get()
        self.assertEqual(v, "a")

        threading.Thread(target=self.pub, args=(q1, "b")).start()
        v = q1.get(5)
        self.assertEqual(v, "b")
