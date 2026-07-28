# CAS EC-15 Serial Reader

<p align="center">
  <img
    src="assets/cas_ec15.jpg"
    alt="CAS EC-15 전자저울"
    width="500"
  />
</p>

CAS **EC-15 전자저울**의 RS-232 데이터를 USB-RS232 변환기를 통해 읽는 간단한 Python 도구입니다.

- Ubuntu 에서 바로 실행
- 시리얼 포트 목록 확인
- `NET`과 `net`을 구분해 안정 상태 표시
- EC-15 원본 출력 전체 확인 가능
- 별도의 시스템 Python 패키지 오염 없이 `.venv` 사용

---

### 1. 필수 패키지 설치

Ubuntu에서 한 번만 실행합니다.

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

### 2. 실행 권한 설정

```bash
cd ~/inpyo_ws/cas_ec15_pyserial
chmod +x ec15_check.sh
```

### 3. 연결된 포트 확인

```bash
./ec15_check.sh --list
```

예상 출력:

```text
사용 가능한 시리얼 포트:
  - /dev/ttyUSB0: USB Serial
```

### 4. 저울 데이터 확인

원본 데이터까지 모두 확인:

```bash
./ec15_check.sh /dev/ttyUSB0 --raw
```

중량값 위주로 확인:

```bash
./ec15_check.sh /dev/ttyUSB0
```

종료:

```text
Ctrl+C
```

---

## EC-15 설정

저울의 사용자 설정에서 다음 값을 확인합니다.

| 항목 | 설정값 |
|---|---|
| Baud rate | `9600` |
| Data bits | `8` |
| Parity | `None` |
| Stop bits | `1` |
| Flow control | `None` |
| 전송 방법 | `2` — 연속 전송 |

Baud rate 메뉴의 숫자 표시는 다음과 같습니다.

| 저울 설정값 | 속도 |
|---:|---:|
| `0` | 2400 bps |
| `1` | 4800 bps |
| `2` | 9600 bps |

설정을 바꾼 뒤에는 저울 전원을 껐다가 다시 켜는 것이 좋습니다.

---

## 연결 구성

```text
CAS EC-15
   │
   │ RS-232
   ▼
USB-RS232 변환기
   │
   │ USB
   ▼
Ubuntu PC / Jetson
```

EC-15 통신 핀:

| EC-15 DB9 핀 | 기능 |
|---:|---|
| 2 | RX |
| 3 | TX |
| 5 | GND |

통신이 되지 않는다면 TX/RX가 교차된 크로스 연결인지 확인합니다.

```text
EC-15 Pin 2 ↔ 변환기 TX
EC-15 Pin 3 ↔ 변환기 RX
EC-15 Pin 5 ↔ 변환기 GND
```

---

## 출력 해석

예시:

```text
RAW  | NET:       49  g
WEIGHT | 49.000 g | 안정
RAW  | U/W:        0  g
RAW  | PCS:        0
RAW  | Tare:          g
```

| 출력 | 의미 |
|---|---|
| `NET` | 안정된 순중량 |
| `net` | 불안정한 순중량 |
| `U/W` | 단위 중량 |
| `PCS` / `pcs` | 개수 |
| `Tare` | 용기 중량 |
| `WEIGHT ... 안정` | 실제 로봇 제어 등에 사용하기 좋은 안정값 |
| `WEIGHT ... 불안정` | 저울값이 아직 흔들리는 상태 |

실제 제어 로직에서는 보통 **대문자 `NET` 값만 사용**합니다.

---

## 명령어 모음

### 시리얼 포트 목록

```bash
./ec15_check.sh --list
```

### 기본 수신

```bash
./ec15_check.sh /dev/ttyUSB0
```

### 원본 데이터 포함

```bash
./ec15_check.sh /dev/ttyUSB0 --raw
```

### 다른 Baud rate 시험

```bash
./ec15_check.sh /dev/ttyUSB0 --baudrate 2400 --raw
./ec15_check.sh /dev/ttyUSB0 --baudrate 4800 --raw
./ec15_check.sh /dev/ttyUSB0 --baudrate 9600 --raw
```

USB 시리얼 장치가 하나만 감지되면 포트를 생략할 수도 있습니다.

```bash
./ec15_check.sh --raw
```

---

## 문제 해결

### `No module named pip`

기존 가상환경을 삭제하고 필수 패키지를 설치합니다.

```bash
rm -rf .venv
sudo apt update
sudo apt install -y python3-venv python3-pip
./ec15_check.sh --list
```

### `/dev/ttyUSB0` 권한 오류

현재 사용자를 `dialout` 그룹에 추가합니다.

```bash
sudo usermod -aG dialout "$USER"
```

그다음 **로그아웃 후 다시 로그인**합니다.

현재 터미널에서만 임시 확인하려면:

```bash
sudo chmod a+rw /dev/ttyUSB0
```

### 포트가 보이지 않음

USB-RS232 변환기를 다시 연결한 뒤 확인합니다.

```bash
ls -l /dev/ttyUSB*
dmesg | tail -30
```

### 프로그램은 실행되지만 아무 데이터도 나오지 않음

다음을 순서대로 확인합니다.

1. EC-15 전송 방법이 `2`인지 확인
2. 저울 설정 후 전원을 다시 켰는지 확인
3. Baud rate가 프로그램과 같은지 확인
4. TX/RX 크로스 배선 확인
5. `/dev/ttyUSB0`가 실제 변환기 포트인지 확인

### 깨진 문자만 출력됨

Baud rate 불일치 가능성이 큽니다.

```bash
./ec15_check.sh /dev/ttyUSB0 --baudrate 2400 --raw
./ec15_check.sh /dev/ttyUSB0 --baudrate 4800 --raw
./ec15_check.sh /dev/ttyUSB0 --baudrate 9600 --raw
```

---

## 프로젝트 구조

```text
cas_ec15_pyserial/
├── .gitignore
├── README.md
├── ec15_check.sh
├── ec15_reader.py
└── requirements.txt
```

| 파일 | 역할 |
|---|---|
| `ec15_check.sh` | 가상환경 생성, pySerial 설치, 프로그램 실행 |
| `ec15_reader.py` | 시리얼 데이터 수신 및 안정 중량 파싱 |
| `requirements.txt` | Python 의존성 |
| `.gitignore` | 가상환경·캐시·로그 등 Git 제외 |

---

## 직접 Python으로 실행

가상환경을 활성화한 뒤 실행할 수도 있습니다.

```bash
source .venv/bin/activate
python ec15_reader.py --list
python ec15_reader.py /dev/ttyUSB0 --raw
```

가상환경 종료:

```bash
deactivate
```


## 요구 환경

- Python 3.10 이상 권장
- pySerial 3.5 이상
- Ubuntu / Jetson Linux
- CAS EC-15
- USB-RS232 변환기
