#!/usr/bin/env python3
"""EC-15 udev rule 생성 로직 테스트."""

import unittest

from cas_ec15_pyserial.udev_setup import build_rule


class UdevRuleTest(unittest.TestCase):
    def test_build_rule_uses_usb_identity(self) -> None:
        properties = {
            "ID_VENDOR_ID": "0403",
            "ID_MODEL_ID": "6001",
            "ID_SERIAL_SHORT": "FTSIU2PV",
        }

        self.assertEqual(
            build_rule(properties),
            'SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", '
            'ATTRS{idProduct}=="6001", ATTRS{serial}=="FTSIU2PV", '
            'SYMLINK+="cas_ec15"\n',
        )

    def test_build_rule_rejects_missing_serial(self) -> None:
        with self.assertRaises(ValueError):
            build_rule({"ID_VENDOR_ID": "0403", "ID_MODEL_ID": "6001"})


if __name__ == "__main__":
    unittest.main()
