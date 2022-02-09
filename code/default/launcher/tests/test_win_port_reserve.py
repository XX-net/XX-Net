from unittest import TestCase
import sys

from launcher.win_compat_suggest import Win10PortReserveSolution

empty_output = [
    b'\r\n',
    b'Protocol tcp Port Exclusion Ranges\r\n',
    b'\r\n',
    b'Start Port    End Port      \r\n',
    b'----------    --------      \r\n',
    b'\r\n',
    b'* - Administered port exclusions.\r\n',
    b'\r\n'
]

valid_output = [
    b'\r\n',
    b'Protocol tcp Port Exclusion Ranges\r\n',
    b'\r\n',
    b'Start Port    End Port      \r\n',
    b'----------    --------      \r\n',
    b'     49795       49894      \r\n',
    b'     49895       49994      \r\n',
    b'     50000       50059     *\r\n',
    b'\r\n',
    b'* - Administered port exclusions.\r\n',
    b'\r\n'
]


class TestW10PortReserve(TestCase):
    def setUp(self):
        if sys.platform == "win32":
            self.s = Win10PortReserveSolution()
        else:
            self.s = None

    def test_detect(self):
        if not self.s:
            return

        res = self.s.is_port_reserve_conflict()
        print(res)

    def test_reset(self):
        if not self.s:
            return

        self.s.change_reserved_port_range()

    def test_resolve(self):
        if not self.s:
            return

        self.s.check_and_resolve()
