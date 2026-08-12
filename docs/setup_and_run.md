# 설치 및 실행

이 문서는 `cas_ec15_pyserial`의 **설치, standalone serial 확인, ROS 2 build, udev 설정, 실행, 테스트, troubleshooting** 절차의 기준 문서입니다.

처음 사용하는 장비에서는 아래 순서로 진행합니다.

```text
필수 패키지 설치
→ standalone serial 확인
→ ROS 2 build
→ /dev/cas_ec15 설정
→ ROS 2 실행
→ topic 확인
```

하드웨어 통신 설정과 RS-232 배선은 [하드웨어 설정](hardware_setup.md)을 참고합니다.

## 1. 필수 패키지 설치

repository 루트에서 작업합니다.

```bash
cd ~/inpyo_ws/cas_ec15_pyserial

sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

`ec15_check.sh` 실행 권한이 없다면 한 번만 설정합니다.

```bash
chmod +x ec15_check.sh
```

## 2. Standalone serial 확인

ROS 2를 실행하기 전에 EC-15과 USB-RS232 통신 자체가 정상인지 먼저 확인합니다.

연결된 serial port 목록을 확인합니다.

```bash
./ec15_check.sh --list
```

예를 들어 장치가 `/dev/ttyUSB0`로 보인다면 원본 데이터를 확인합니다.

```bash
./ec15_check.sh /dev/ttyUSB0 --raw
```

중량값 위주로 보려면 `--raw`를 생략합니다.

```bash
./ec15_check.sh /dev/ttyUSB0
```

USB serial 장치가 하나만 감지되면 port를 생략할 수도 있습니다.

```bash
./ec15_check.sh --raw
```

종료는 `Ctrl+C`를 사용합니다.

정상 수신 예시는 다음과 같습니다.

```text
RAW  | NET:        9  g
WEIGHT | 9.000 g | 안정
RAW  | U/W:        0  g
RAW  | PCS:        0
RAW  | Tare:          g
```

주요 출력 의미:

| 출력 | 의미 |
|---|---|
| `NET` | 안정된 순중량 |
| `net` | 불안정한 순중량 |
| `U/W` | 단위 중량 |
| `PCS` / `pcs` | 개수 |
| `Tare` | 용기 중량 |

ROS 2 adapter는 대문자 `NET`으로 수신된 안정 중량만 발행합니다.

## 3. ROS 2 build

이 repository 루트에서 직접 build합니다. 별도 ROS 2 workspace의 `src/`로 복사하거나 symlink할 필요가 없습니다.

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

정상이라면 다음 executable이 표시됩니다.

```text
cas_ec15_pyserial ec15_reader
cas_ec15_pyserial ec15_udev_setup
cas_ec15_pyserial ec15_weight_node
```

`build/`, `install/`, `log/`는 colcon이 생성하는 로컬 산출물이며 Git에는 포함하지 않습니다.

## 4. `/dev/cas_ec15` udev 별칭 설정

`/dev/ttyUSB0` 같은 이름은 USB 연결 순서에 따라 바뀔 수 있으므로 ROS 2 node의 기본 port는 `/dev/cas_ec15`입니다.

먼저 실제로 생성될 udev rule을 확인합니다.

```bash
ros2 run cas_ec15_pyserial ec15_udev_setup show \
  --device /dev/ttyUSB0
```

`show`는 system file을 변경하지 않습니다. 출력된 `vendor`, `product`, `serial`이 실제 EC-15에 연결된 USB-RS232 변환기인지 확인합니다.

확인 후 rule을 설치합니다.

```bash
ros2 run cas_ec15_pyserial ec15_udev_setup install \
  --device /dev/ttyUSB0
```

이 명령은 `/etc/udev/rules.d/99-cas-ec15.rules`를 설치하므로 `sudo` 비밀번호를 요청할 수 있습니다.

설치 후 USB-RS232 변환기를 분리했다가 다시 연결합니다.

```bash
ls -l /dev/cas_ec15
readlink -f /dev/cas_ec15
```

`/dev/cas_ec15`이 실제 `ttyUSB*` 장치를 가리키면 정상입니다.

다른 USB-RS232 변환기로 교체한 경우에는 새 장치의 현재 `ttyUSB*` 이름으로 `show`와 `install`을 다시 실행합니다.

## 5. ROS 2 실행

현재 terminal에서 ROS 2 환경과 이 package를 source합니다.

```bash
cd ~/inpyo_ws/cas_ec15_pyserial
source /opt/ros/humble/setup.bash
source install/setup.bash
```

node를 실행합니다.

```bash
ros2 run cas_ec15_pyserial ec15_weight_node
```

기본 interface:

| 항목 | 기본값 |
|---|---|
| node | `ec15_weight_node` |
| topic | `weight_g` |
| message | `std_msgs/msg/Float64` |
| unit | `g` |
| parameter `port` | `/dev/cas_ec15` |
| parameter `baudrate` | `9600` |

다른 terminal에서 topic을 확인합니다.

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

저울이 불안정하여 `net`을 출력하는 동안에는 새 message를 발행하지 않습니다.

## 6. Parameter 변경

기본 port 대신 다른 장치를 임시로 사용할 때는 parameter를 override합니다.

```bash
ros2 run cas_ec15_pyserial ec15_weight_node \
  --ros-args \
  -p port:=/dev/ttyUSB0
```

Baud rate가 기본값과 다른 경우:

```bash
ros2 run cas_ec15_pyserial ec15_weight_node \
  --ros-args \
  -p baudrate:=4800
```

지원 baud rate는 `2400`, `4800`, `9600`입니다.

## 7. Namespace와 remap

`weight_g`는 relative topic입니다. 다른 시스템과 통합할 때 node 코드를 수정하지 않고 namespace와 remap을 사용합니다.

```bash
ros2 run cas_ec15_pyserial ec15_weight_node \
  --ros-args \
  -r __ns:=/target_mass \
  -r weight_g:=scale_weight_g
```

이 경우 topic은 다음과 같습니다.

```text
/target_mass/scale_weight_g
```

## 8. 테스트

### Hardware 없이

parser와 udev rule 생성 로직을 확인합니다.

```bash
cd ~/inpyo_ws/cas_ec15_pyserial

./ec15_check.sh --list
.venv/bin/python -m unittest -v \
  test_ec15_reader.py \
  test_udev_setup.py
```

### ROS 2 package

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
ros2 pkg executables cas_ec15_pyserial
```

### 실제 EC-15

1. `./ec15_check.sh /dev/ttyUSB0 --raw`로 `NET` 수신 확인
2. `/dev/cas_ec15` symlink 확인
3. `ec15_weight_node` 실행
4. `/weight_g`에서 값 확인

## 9. Troubleshooting

### `/dev/cas_ec15`이 보이지 않음

현재 USB serial 장치와 설치된 rule을 확인합니다.

```bash
ls -l /dev/ttyUSB*
cat /etc/udev/rules.d/99-cas-ec15.rules
```

장치 property 확인:

```bash
udevadm info --query=property --name=/dev/ttyUSB0
```

rule 설치 후에는 USB-RS232 변환기를 분리했다가 다시 연결합니다.

### Serial port 권한 오류

현재 사용자를 `dialout` 그룹에 추가합니다.

```bash
sudo usermod -aG dialout "$USER"
```

그다음 로그아웃 후 다시 로그인합니다.

임시 해결을 위해 `chmod 666`을 상시 설정하는 방식은 사용하지 않습니다.

### USB serial port가 보이지 않음

```bash
ls -l /dev/ttyUSB*
dmesg | tail -30
```

USB-RS232 변환기 자체가 인식되는지 먼저 확인합니다.

### 프로그램은 실행되지만 데이터가 없음

다음을 순서대로 확인합니다.

1. [하드웨어 설정](hardware_setup.md)의 EC-15 통신 설정
2. EC-15 전송 방법이 연속 전송인지 확인
3. Baud rate가 프로그램과 동일한지 확인
4. RS-232 TX/RX 배선 확인
5. `/dev/cas_ec15`이 실제 EC-15 변환기를 가리키는지 확인
6. ROS 2 전에 standalone reader에서 데이터가 나오는지 확인

### 깨진 문자가 출력됨

Baud rate가 불확실할 때만 아래 값을 순서대로 시험합니다.

```bash
./ec15_check.sh /dev/ttyUSB0 --baudrate 2400 --raw
./ec15_check.sh /dev/ttyUSB0 --baudrate 4800 --raw
./ec15_check.sh /dev/ttyUSB0 --baudrate 9600 --raw
```

### `No module named pip`

기존 virtual environment를 지우고 필요한 system package를 설치합니다.

```bash
rm -rf .venv
sudo apt update
sudo apt install -y python3-venv python3-pip
./ec15_check.sh --list
```
