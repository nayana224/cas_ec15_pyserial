#!/usr/bin/env python3
"""CAS EC-15 RS-232 수신 확인용 간단한 pySerial 프로그램."""

from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass

import serial
from serial import SerialException
from serial.tools import list_ports


WEIGHT_PATTERN = re.compile(
    r"^(?P<label>NET|net)\s*:?\s*(?P<value>[+-]?\d+(?:\.\d+)?)\s*(?P<unit>g|kg)?\s*$"
)


@dataclass(frozen=True)
class ScaleWeight:
    value: float
    unit: str
    stable: bool


def available_ports() -> list[str]:
    return [port.device for port in list_ports.comports()]


def choose_default_port() -> str | None:
    ports = available_ports()

    preferred = [
        port
        for port in ports
        if "ttyUSB" in port or "ttyACM" in port or port.upper().startswith("COM")
    ]

    if len(preferred) == 1:
        return preferred[0]

    return None


def parse_weight(line: str) -> ScaleWeight | None:
    match = WEIGHT_PATTERN.match(line.strip())
    if match is None:
        return None

    return ScaleWeight(
        value=float(match.group("value")),
        unit=match.group("unit") or "g",
        stable=match.group("label") == "NET",
    )


def print_ports() -> None:
    ports = list_ports.comports()

    if not ports:
        print("사용 가능한 시리얼 포트를 찾지 못했습니다.")
        return

    print("사용 가능한 시리얼 포트:")
    for port in ports:
        description = port.description or "설명 없음"
        print(f"  - {port.device}: {description}")


def read_scale(port: str, baudrate: int, raw: bool) -> int:
    print(f"연결 시도: {port}, {baudrate} bps, 8N1")
    print("종료하려면 Ctrl+C를 누르세요.\n")

    try:
        with serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1.0,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
        ) as scale:
            scale.reset_input_buffer()

            while True:
                data = scale.readline()
                if not data:
                    continue

                line = data.decode("ascii", errors="replace").strip("\r\n ")
                if not line:
                    continue

                if raw:
                    print(f"RAW  | {line}")

                weight = parse_weight(line)
                if weight is None:
                    if not raw:
                        print(f"DATA | {line}")
                    continue

                state = "안정" if weight.stable else "불안정"
                print(f"WEIGHT | {weight.value:.3f} {weight.unit} | {state}")

    except KeyboardInterrupt:
        print("\n수신을 종료합니다.")
        return 0
    except PermissionError:
        print(
            f"권한 오류: {port}에 접근할 수 없습니다.\n"
            '다음 명령 실행 후 로그아웃/로그인하세요:\n'
            '  sudo usermod -aG dialout "$USER"',
            file=sys.stderr,
        )
        return 2
    except SerialException as error:
        print(f"시리얼 통신 오류: {error}", file=sys.stderr)
        return 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CAS EC-15 RS-232 출력 확인용 pySerial 프로그램"
    )
    parser.add_argument(
        "port",
        nargs="?",
        help="시리얼 포트. 예: /dev/ttyUSB0 또는 COM3",
    )
    parser.add_argument(
        "--baudrate",
        type=int,
        default=9600,
        choices=(2400, 4800, 9600),
        help="통신 속도. 기본값: 9600",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="사용 가능한 시리얼 포트 목록만 출력",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="수신된 모든 ASCII 줄을 그대로 출력",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.list:
        print_ports()
        return 0

    port = args.port or choose_default_port()
    if port is None:
        print_ports()
        print(
            "\n포트를 자동으로 하나만 선택할 수 없습니다.\n"
            "아래처럼 포트를 직접 지정하세요:\n"
            "  ./ec15_check.sh /dev/ttyUSB0\n"
            "  python3 ec15_reader.py COM3",
            file=sys.stderr,
        )
        return 1

    return read_scale(port=port, baudrate=args.baudrate, raw=args.raw)


if __name__ == "__main__":
    raise SystemExit(main())
