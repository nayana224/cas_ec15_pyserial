#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"

die() {
    echo "오류: $*" >&2
    exit 1
}

command -v "${PYTHON_BIN}" >/dev/null 2>&1 \
    || die "python3를 찾을 수 없습니다."

create_venv() {
    echo "[1/3] Python 가상환경 생성"

    if ! "${PYTHON_BIN}" -m venv "${VENV_DIR}"; then
        cat >&2 <<'EOF'

가상환경 생성에 실패했습니다.
Ubuntu/Jetson에서는 아래 패키지를 설치한 뒤 다시 실행하세요.

  sudo apt update
  sudo apt install -y python3-venv python3-pip

EOF
        exit 1
    fi
}

ensure_pip() {
    local venv_python="${VENV_DIR}/bin/python"

    if "${venv_python}" -m pip --version >/dev/null 2>&1; then
        return
    fi

    echo "가상환경에 pip가 없어 복구를 시도합니다."

    if "${venv_python}" -m ensurepip --upgrade >/dev/null 2>&1; then
        return
    fi

    cat >&2 <<'EOF'

pip 복구에 실패했습니다.
기존 가상환경을 삭제하고 필요한 패키지를 설치하세요.

  rm -rf .venv
  sudo apt update
  sudo apt install -y python3-venv python3-pip
  ./ec15_check.sh --list

EOF
    exit 1
}

if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
    rm -rf "${VENV_DIR}"
    create_venv
fi

ensure_pip

echo "[2/3] pySerial 설치 확인"
"${VENV_DIR}/bin/python" -m pip install --quiet -r "${SCRIPT_DIR}/requirements.txt"

echo "[3/3] CAS EC-15 수신 시작"
exec "${VENV_DIR}/bin/python" "${SCRIPT_DIR}/ec15_reader.py" "$@"
