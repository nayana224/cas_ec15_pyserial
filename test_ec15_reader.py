#!/usr/bin/env python3
"""EC-15 중량 문자열 파서 회귀 테스트."""

import unittest

from cas_ec15_pyserial.protocol import ScaleWeight, parse_weight


class ParseWeightTest(unittest.TestCase):
    def test_stable_weight(self) -> None:
        self.assertEqual(
            parse_weight("NET:       49  g"),
            ScaleWeight(value=49.0, unit="g", stable=True),
        )

    def test_unstable_weight(self) -> None:
        self.assertEqual(
            parse_weight("net:      -10.5 g"),
            ScaleWeight(value=-10.5, unit="g", stable=False),
        )

    def test_default_unit_is_grams(self) -> None:
        self.assertEqual(
            parse_weight("NET: 12"),
            ScaleWeight(value=12.0, unit="g", stable=True),
        )

    def test_non_weight_line_is_ignored(self) -> None:
        self.assertIsNone(parse_weight("U/W:        0  g"))
        self.assertIsNone(parse_weight("PCS:        0"))
        self.assertIsNone(parse_weight("Tare:          g"))


if __name__ == "__main__":
    unittest.main()
