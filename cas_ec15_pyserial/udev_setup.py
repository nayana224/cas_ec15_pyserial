"""EC-15 USB-RS232 장치의 udev symlink를 설정한다."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import tempfile


RULE_PATH = Path("/etc/udev/rules.d/99-cas-ec15.rules")
SYMLINK_NAME = "cas_ec15"
USB_ID_PATTERN = re.compile(r"^[0-9A-Fa-f]{4}$")
SERIAL_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


def read_udev_properties(device: str) -> dict[str, str]:
    """지정 장치의 udev property를 읽는다."""
    result = subprocess.run(
        ["udevadm", "info", "--query=property", f"--name={device}"],
        check=True,
        capture_output=True,
        text=True,
    )

    properties: dict[str, str] = {}
    for line in result.stdout.splitlines():
        key, separator, value = line.partition("=")
        if separator:
            properties[key] = value
    return properties


def build_rule(properties: dict[str, str]) -> str:
    """USB serial 장치를 고유 serial 기반 symlink rule로 만든다."""
    vendor_id = properties.get("ID_VENDOR_ID", "")
    model_id = properties.get("ID_MODEL_ID", "")
    serial = properties.get("ID_SERIAL_SHORT", "")

    missing = [
        key
        for key, value in (
            ("ID_VENDOR_ID", vendor_id),
            ("ID_MODEL_ID", model_id),
            ("ID_SERIAL_SHORT", serial),
        )
        if not value
    ]
    if missing:
        raise ValueError(f"udev property missing: {', '.join(missing)}")

    if not USB_ID_PATTERN.fullmatch(vendor_id):
        raise ValueError("invalid ID_VENDOR_ID")
    if not USB_ID_PATTERN.fullmatch(model_id):
        raise ValueError("invalid ID_MODEL_ID")
    if not SERIAL_PATTERN.fullmatch(serial):
        raise ValueError("invalid ID_SERIAL_SHORT")

    return (
        'SUBSYSTEM=="tty", '
        f'ATTRS{{idVendor}}=="{vendor_id}", '
        f'ATTRS{{idProduct}}=="{model_id}", '
        f'ATTRS{{serial}}=="{serial}", '
        f'SYMLINK+="{SYMLINK_NAME}"\n'
    )


def install_rule(rule: str) -> None:
    """생성한 rule을 설치하고 udev rule을 다시 읽는다."""
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as file:
        file.write(rule)
        temporary_path = Path(file.name)

    try:
        subprocess.run(
            ["sudo", "install", "-m", "0644", str(temporary_path), str(RULE_PATH)],
            check=True,
        )
        subprocess.run(["sudo", "udevadm", "control", "--reload-rules"], check=True)
    finally:
        temporary_path.unlink(missing_ok=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CAS EC-15 USB-RS232 장치에 /dev/cas_ec15 symlink를 설정"
    )
    parser.add_argument("action", choices=("show", "install"))
    parser.add_argument(
        "--device",
        default="/dev/ttyUSB0",
        help="현재 EC-15 USB-RS232 장치. 기본값: /dev/ttyUSB0",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        properties = read_udev_properties(args.device)
        rule = build_rule(properties)
    except (subprocess.CalledProcessError, ValueError) as error:
        print(f"udev rule 생성 실패: {error}")
        return 1

    print(rule, end="")

    if args.action == "show":
        return 0

    try:
        install_rule(rule)
    except subprocess.CalledProcessError as error:
        print(f"udev rule 설치 실패: {error}")
        return 2

    print(f"설치 완료: {RULE_PATH}")
    print("USB-RS232 변환기를 분리했다가 다시 연결하세요.")
    print(f"장치 별칭: /dev/{SYMLINK_NAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
