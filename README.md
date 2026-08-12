# CAS EC-15 Serial Reader

<p align="center">
  <img
    src="assets/cas_ec15.jpg"
    alt="CAS EC-15 전자저울"
    width="500"
  />
</p>

CAS **EC-15 전자저울**의 RS-232 데이터를 USB-RS232 변환기를 통해 읽는 Python 도구입니다.
단독 pySerial 확인 도구와 ROS 2용 얇은 adapter를 함께 제공합니다.

- Ubuntu / Jetson Linux에서 실행
- 시리얼 포트 목록 확인
- `NET`과 `net`을 구분해 안정 상태 표시
- EC-15 원본 출력 확인
- ROS 2에서 안정 중량을 `std_msgs/msg/Float64`로 발행

---

## 빠른 시작

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

원본 데이터를 포함해 확인:

```bash
./ec15_check.sh /dev/ttyUSB0 --raw
```

중량값 위주로 확인:

```bash
./ec15_check.sh /dev/ttyUSB0
```

USB 시리얼 장치가 하나만 감지되면 포트를 생략할 수 있습니다.

```bash
./ec15_check.sh --raw
```

종료는 `Ctrl+C`를 사용합니다.

---

## ROS 2 adapter

ROS 2 package 이름은 `cas_ec15_pyserial`, executable은 `ec15_weight_node`입니다.
기존 pySerial 확인 도구와 동일한 parser를 사용하며, 대문자 `NET`으로 수신된 **안정 중량만** 발행합니다.

### Interface

| 항목 | 기본값 | 의미 |
|---|---|---|
| topic | `weight_g` | 안정 중량 [g], `std_msgs/msg/Float64` |
| parameter `port` | `/dev/ttyUSB0` | EC-15가 연결된 serial port |
| parameter `baudrate` | `9600` | `2400`, `4800`, `9600` 중 하나 |
| parameter `topic_name` | `weight_g` | 발행할 relative topic 이름 |

`weight_g`는 relative topic이므로 namespace 없이 실행하면 `/weight_g`가 됩니다.
저울이 불안정하여 `net`을 출력하는 동안에는 새 중량 message를 발행하지 않습니다.

### 기존 ROS 2 workspace에 넣기

이 repository를 사용할 workspace의 `src/` 아래에 둡니다.

```bash
cd ~/inpyo_ws/<workspace>/src
git clone https://github.com/nayana224/cas_ec15_pyserial.git

cd ~/inpyo_ws/<workspace>
source /opt/ros/humble/setup.bash
rosdep install -i --from-paths src --rosdistro humble -y
colcon build --packages-select cas_ec15_pyserial
source install/setup.bash
```

ROS 2 Humble의 `ament_python` package 구조와 `console_scripts` entry point 방식을 사용합니다.

### 실행

```bash
ros2 run cas_ec15_pyserial ec15_weight_node \
  --ros-args \
  -p port:=/dev/ttyUSB0 \
  -p baudrate:=9600
```

다른 terminal에서 확인:

```bash
source /opt/ros/humble/setup.bash
source ~/inpyo_ws/<workspace>/install/setup.bash
ros2 topic echo /weight_g
```

예상 출력:

```text
data: 9.0
---
```

다른 시스템과 합칠 때는 node 코드를 수정하지 않고 namespace 또는 `topic_name` parameter로 topic을 정합니다.

```bash
ros2 run cas_ec15_pyserial ec15_weight_node \
  --ros-args \
  -r __ns:=/target_mass \
  -p topic_name:=scale_weight_g
```

이 경우 topic은 `/target_mass/scale_weight_g`가 됩니다.

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

EC-15 DB9 핀:

| 핀 | 기능 |
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
| `WEIGHT ... 안정` | 안정 상태로 파싱된 중량값 |
| `WEIGHT ... 불안정` | 아직 안정되지 않은 중량값 |

ROS 2 adapter는 대문자 `NET` 값만 발행합니다.

---

## 다른 Baud rate 시험

깨진 문자가 출력되거나 통신 설정이 불확실할 때만 시험합니다.

```bash
./ec15_check.sh /dev/ttyUSB0 --baudrate 2400 --raw
./ec15_check.sh /dev/ttyUSB0 --baudrate 4800 --raw
./ec15_check.sh /dev/ttyUSB0 --baudrate 9600 --raw
```

---

## 테스트

하드웨어 없이 중량 문자열 parser를 확인할 수 있습니다.

```bash
./ec15_check.sh --list
.venv/bin/python -m unittest -v test_ec15_reader.py
```

ROS 2 package는 workspace에서 다음 순서로 확인합니다.

```bash
source /opt/ros/humble/setup.bash
colcon build --packages-select cas_ec15_pyserial
source install/setup.bash
ros2 pkg executables cas_ec15_pyserial
```

정상이라면 `cas_ec15_pyserial ec15_weight_node`가 표시됩니다.

---

## 문제 해결

### `/dev/ttyUSB0` 권한 오류

현재 사용자를 `dialout` 그룹에 추가합니다.

```bash
sudo usermod -aG dialout "$USER"
```

그다음 로그아웃 후 다시 로그인합니다.

현재 terminal에서만 임시 확인하려면:

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

### `No module named pip`

기존 가상환경을 삭제하고 필수 패키지를 설치합니다.

```bash
rm -rf .venv
sudo apt update
sudo apt install -y python3-venv python3-pip
./ec15_check.sh --list
```

---

## 프로젝트 구조

```text
cas_ec15_pyserial/
├── assets/
│   └── cas_ec15.jpg
├── cas_ec15_pyserial/
│   ├── __init__.py
│   ├── protocol.py
│   └── ros2_node.py
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
└── test_ec15_reader.py
```

| 파일 | 역할 |
|---|---|
| `cas_ec15_pyserial/protocol.py` | CLI와 ROS 2가 공유하는 EC-15 중량 parser |
| `cas_ec15_pyserial/ros2_node.py` | 안정 중량 ROS 2 publisher |
| `ec15_check.sh` | `.venv` 생성, pySerial 설치, 단독 reader 실행 |
| `ec15_reader.py` | 시리얼 데이터 수신 확인용 CLI |
| `test_ec15_reader.py` | 중량 문자열 parser 회귀 테스트 |
| `package.xml`, `setup.py`, `setup.cfg` | ROS 2 `ament_python` package metadata |
| `EC_KOR_UM.pdf` | CAS EC 시리즈 사용자 매뉴얼 |

---

## 요구 환경

- Python 3.10 이상 권장
- pySerial 3.5 이상
- ROS 2 Humble (ROS 2 adapter 사용 시)
- Ubuntu / Jetson Linux
- CAS EC-15
- USB-RS232 변환기
