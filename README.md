# CAS EC-15 Serial Reader

<p align="center">
  <img
    src="assets/cas_ec15.jpg"
    alt="CAS EC-15 전자저울"
    width="500"
  />
</p>

CAS **EC-15 전자저울**의 RS-232 데이터를 USB-RS232 변환기를 통해 읽는 Python / ROS 2 도구입니다.
이 repository 하나에서 단독 serial 확인, ROS 2 build, udev 별칭 설정, ROS 2 topic 발행까지 테스트합니다.

- Ubuntu / Jetson Linux
- pySerial 기반 원본 수신 확인
- `NET` / `net` 안정 상태 구분
- ROS 2 `std_msgs/msg/Float64` 중량 발행
- USB serial 고정 별칭 `/dev/cas_ec15` 설정

## 1. 설치

```bash
cd ~/inpyo_ws/cas_ec15_pyserial

sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

`ec15_check.sh`를 처음 사용할 때 실행 권한이 없다면 한 번만 설정합니다.

```bash
chmod +x ec15_check.sh
```

## 2. 단독 serial 확인

연결된 serial port를 확인합니다.

```bash
./ec15_check.sh --list
```

원본 데이터를 포함해 확인합니다.

```bash
./ec15_check.sh /dev/ttyUSB0 --raw
```

중량값 위주로 확인합니다.

```bash
./ec15_check.sh /dev/ttyUSB0
```

USB serial 장치가 하나만 감지되면 port를 생략할 수 있습니다.

```bash
./ec15_check.sh --raw
```

종료는 `Ctrl+C`를 사용합니다.

정상 예시:

```text
RAW  | NET:        9  g
WEIGHT | 9.000 g | 안정
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

ROS 2 adapter는 대문자 `NET`으로 수신된 안정 중량만 발행합니다.

## 3. ROS 2 build

이 repository 루트에서 직접 build합니다. 다른 ROS 2 workspace의 `src/`로 복사하거나 symlink할 필요가 없습니다.

```bash
cd ~/inpyo_ws/cas_ec15_pyserial
source /opt/ros/humble/setup.bash

colcon build --symlink-install
source install/setup.bash
```

설치된 executable을 확인합니다.

```bash
ros2 pkg executables cas_ec15_pyserial
```

정상 예시:

```text
cas_ec15_pyserial ec15_reader
cas_ec15_pyserial ec15_udev_setup
cas_ec15_pyserial ec15_weight_node
```

`build/`, `install/`, `log/`는 colcon이 생성하는 로컬 산출물이며 Git에는 포함하지 않습니다.

## 4. EC-15 장치 이름 고정

`/dev/ttyUSB0`는 USB 연결 순서에 따라 달라질 수 있으므로 ROS 2에서는 `/dev/cas_ec15` 별칭을 사용합니다.

udev 설정 도구는 지정한 현재 serial 장치에서 `vendor`, `product`, `serial` 정보를 읽어 rule을 생성합니다. 실제 장치 식별자를 코드에 하드코딩하지 않습니다.

먼저 설치될 rule만 확인합니다.

```bash
ros2 run cas_ec15_pyserial ec15_udev_setup show \
  --device /dev/ttyUSB0
```

현재 사용 중인 FTDI 변환기에서는 다음 식별자가 확인되었습니다.

```text
ID_VENDOR_ID=0403
ID_MODEL_ID=6001
ID_SERIAL_SHORT=FTSIU2PV
```

따라서 예상 rule은 다음 형태입니다.

```text
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", ATTRS{serial}=="FTSIU2PV", SYMLINK+="cas_ec15"
```

내용이 맞으면 한 번만 설치합니다.

```bash
ros2 run cas_ec15_pyserial ec15_udev_setup install \
  --device /dev/ttyUSB0
```

이 명령은 `/etc/udev/rules.d/99-cas-ec15.rules`를 설치하므로 `sudo` 비밀번호를 요청할 수 있습니다. 설치 후 USB-RS232 변환기를 한 번 분리했다가 다시 연결합니다.

확인:

```bash
ls -l /dev/cas_ec15
```

`/dev/cas_ec15`이 실제 `ttyUSB*` 장치를 가리키면 정상입니다.

## 5. ROS 2 실행

### Interface

| 항목 | 기본값 | 의미 |
|---|---|---|
| topic | `weight_g` | 안정 중량 [g], `std_msgs/msg/Float64` |
| parameter `port` | `/dev/cas_ec15` | EC-15 serial port |
| parameter `baudrate` | `9600` | `2400`, `4800`, `9600` 중 하나 |

udev 별칭 설정 후에는 별도 port 인자 없이 실행합니다.

```bash
cd ~/inpyo_ws/cas_ec15_pyserial
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 run cas_ec15_pyserial ec15_weight_node
```

다른 terminal에서 확인합니다.

```bash
cd ~/inpyo_ws/cas_ec15_pyserial
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 topic echo /weight_g
```

예상 출력:

```text
data: 9.0
---
```

`weight_g`는 relative topic입니다. 나중에 다른 시스템과 통합할 때는 node 코드를 수정하지 않고 ROS namespace와 remap을 사용합니다.

```bash
ros2 run cas_ec15_pyserial ec15_weight_node \
  --ros-args \
  -r __ns:=/target_mass \
  -r weight_g:=scale_weight_g
```

이 경우 topic은 `/target_mass/scale_weight_g`입니다.

## 6. 테스트

parser와 udev rule 생성 로직은 hardware 없이 확인할 수 있습니다.

```bash
cd ~/inpyo_ws/cas_ec15_pyserial
./ec15_check.sh --list
.venv/bin/python -m unittest -v test_ec15_reader.py test_udev_setup.py
```

ROS 2 package 전체 흐름은 다음 순서로 확인합니다.

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
ros2 pkg executables cas_ec15_pyserial
```

## 7. EC-15 설정

저울의 사용자 설정에서 다음 값을 확인합니다.

| 항목 | 설정값 |
|---|---|
| Baud rate | `9600` |
| Data bits | `8` |
| Parity | `None` |
| Stop bits | `1` |
| Flow control | `None` |
| 전송 방법 | `2` — 연속 전송 |

Baud rate 메뉴 표시값:

| 저울 설정값 | 속도 |
|---:|---:|
| `0` | 2400 bps |
| `1` | 4800 bps |
| `2` | 9600 bps |

설정을 변경한 뒤에는 저울 전원을 껐다가 다시 켜는 것이 좋습니다.

## 8. RS-232 연결

```text
CAS EC-15
   │ RS-232
   ▼
USB-RS232 변환기
   │ USB
   ▼
Ubuntu PC / Jetson
```

EC-15 DB9:

| 핀 | 기능 |
|---:|---|
| 2 | RX |
| 3 | TX |
| 5 | GND |

```text
EC-15 Pin 2 ↔ 변환기 TX
EC-15 Pin 3 ↔ 변환기 RX
EC-15 Pin 5 ↔ 변환기 GND
```

통신이 되지 않으면 TX/RX 크로스 연결을 확인합니다.

## 9. 문제 해결

### `/dev/cas_ec15`이 보이지 않음

```bash
ls -l /dev/cas_ec15
udevadm info --query=property --name=/dev/ttyUSB0
```

필요하면 rule을 다시 확인합니다.

```bash
ros2 run cas_ec15_pyserial ec15_udev_setup show --device /dev/ttyUSB0
```

rule 설치 후에는 USB-RS232 변환기를 분리했다가 다시 연결합니다.

### serial port 권한 오류

```bash
sudo usermod -aG dialout "$USER"
```

실행 후 로그아웃하고 다시 로그인합니다.

### USB serial port가 보이지 않음

```bash
ls -l /dev/ttyUSB*
dmesg | tail -30
```

### 프로그램은 실행되지만 데이터가 없음

다음을 확인합니다.

1. EC-15 전송 방법이 `2`인지 확인
2. 저울 설정 후 전원을 다시 켰는지 확인
3. Baud rate가 프로그램과 같은지 확인
4. TX/RX 크로스 배선 확인
5. `/dev/cas_ec15`가 실제 EC-15 USB-RS232 변환기를 가리키는지 확인

### `No module named pip`

```bash
rm -rf .venv
sudo apt update
sudo apt install -y python3-venv python3-pip
./ec15_check.sh --list
```

### 깨진 문자가 출력됨

Baud rate가 불확실할 때만 시험합니다.

```bash
./ec15_check.sh /dev/ttyUSB0 --baudrate 2400 --raw
./ec15_check.sh /dev/ttyUSB0 --baudrate 4800 --raw
./ec15_check.sh /dev/ttyUSB0 --baudrate 9600 --raw
```

## 10. 프로젝트 구조

```text
cas_ec15_pyserial/
├── assets/
│   └── cas_ec15.jpg
├── cas_ec15_pyserial/
│   ├── __init__.py
│   ├── protocol.py
│   ├── ros2_node.py
│   └── udev_setup.py
├── resource/
│   └── cas_ec15_pyserial
├── .gitignore
├── EC_KOR_UM.pdf
├── README.md
├── ec15_check.sh
├── ec15_reader.py
├── package.xml
├── requirements.txt
├── setup.cfg
├── setup.py
├── test_ec15_reader.py
└── test_udev_setup.py
```

| 파일 | 역할 |
|---|---|
| `cas_ec15_pyserial/protocol.py` | CLI와 ROS 2가 공유하는 EC-15 중량 parser |
| `cas_ec15_pyserial/ros2_node.py` | 안정 중량 ROS 2 publisher |
| `cas_ec15_pyserial/udev_setup.py` | `/dev/cas_ec15` udev rule 설정 |
| `ec15_check.sh` | `.venv` 생성, pySerial 설치, 단독 reader 실행 |
| `ec15_reader.py` | serial 데이터 수신 확인용 CLI |
| `test_ec15_reader.py` | parser 회귀 테스트 |
| `test_udev_setup.py` | udev rule 생성 및 입력 검증 테스트 |
| `package.xml`, `setup.py`, `setup.cfg` | ROS 2 `ament_python` package metadata |
| `EC_KOR_UM.pdf` | CAS EC 시리즈 사용자 매뉴얼 |

## 요구 환경

- Python 3.10 이상 권장
- pySerial 3.5 이상
- ROS 2 Humble (ROS 2 adapter 사용 시)
- Ubuntu / Jetson Linux
- CAS EC-15
- USB-RS232 변환기
