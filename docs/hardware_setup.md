# 하드웨어 설정

이 문서는 CAS EC-15과 USB-RS232 변환기를 연결할 때 필요한 **저울 통신 설정, RS-232 배선, USB serial 확인** 절차의 기준 문서입니다.

소프트웨어 설치와 ROS 2 실행은 [설치 및 실행](setup_and_run.md)을 참고합니다.

## 1. 연결 구성

```text
CAS EC-15
   │ RS-232
   ▼
USB-RS232 변환기
   │ USB
   ▼
Ubuntu PC / Jetson
```

EC-15과 PC는 USB로 직접 연결하지 않고 RS-232 신호를 USB-RS232 변환기를 통해 연결합니다.

## 2. EC-15 통신 설정

현재 프로젝트에서 사용하는 기본 통신 조건은 다음과 같습니다.

| 항목 | 설정값 |
|---|---|
| Baud rate | `9600` |
| Data bits | `8` |
| Parity | `None` |
| Stop bits | `1` |
| Flow control | `None` |
| 전송 방법 | `2` — 연속 전송 |

Baud rate 메뉴의 표시값은 다음과 같이 사용합니다.

| 저울 설정값 | 속도 |
|---:|---:|
| `0` | 2400 bps |
| `1` | 4800 bps |
| `2` | 9600 bps |

설정을 변경한 뒤에는 EC-15 전원을 다시 켜고 통신을 확인합니다.

프로젝트에 포함된 제조사 사용자 매뉴얼은 [`EC_KOR_UM.pdf`](../EC_KOR_UM.pdf)입니다.

## 3. RS-232 DB9 배선

EC-15 DB9 통신 핀은 다음과 같습니다.

| 핀 | 기능 |
|---:|---|
| 2 | RX |
| 3 | TX |
| 5 | GND |

USB-RS232 변환기와 연결할 때는 송신과 수신이 서로 연결되어야 합니다.

```text
EC-15 Pin 2 (RX)  ↔ 변환기 TX
EC-15 Pin 3 (TX)  ↔ 변환기 RX
EC-15 Pin 5 (GND) ↔ 변환기 GND
```

통신 데이터가 전혀 들어오지 않으면 baud rate를 바꾸기 전에 TX/RX 배선을 먼저 확인합니다.

## 4. USB-RS232 장치 확인

USB-RS232 변환기를 연결한 뒤 Linux에서 장치가 생성되었는지 확인합니다.

```bash
ls -l /dev/ttyUSB*
```

udev property 확인:

```bash
udevadm info --query=property --name=/dev/ttyUSB0
```

현재 개발 장비에서 확인된 FTDI USB-RS232 변환기의 예시는 다음과 같습니다.

```text
ID_VENDOR_ID=0403
ID_MODEL_ID=6001
ID_SERIAL_SHORT=FTSIU2PV
```

이 값은 **현재 개발 장비의 예시**이며 다른 USB-RS232 변환기를 사용하면 달라질 수 있습니다. 소스 코드에는 이 serial 값을 고정하지 않습니다.

## 5. `/dev/cas_ec15` 별칭

ROS 2에서는 USB 연결 순서에 따라 달라질 수 있는 `/dev/ttyUSB0` 대신 `/dev/cas_ec15`을 기본 장치 이름으로 사용합니다.

설정 도구는 현재 지정한 USB serial 장치의 `vendor`, `product`, `serial`을 읽어서 udev rule을 생성합니다.

먼저 rule을 확인합니다.

```bash
ros2 run cas_ec15_pyserial ec15_udev_setup show \
  --device /dev/ttyUSB0
```

현재 개발 장비 예시에서 생성되는 rule은 다음 형태입니다.

```text
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", ATTRS{serial}=="FTSIU2PV", SYMLINK+="cas_ec15"
```

실제 설치와 검증 절차는 [설치 및 실행](setup_and_run.md)의 udev 설정 절차를 따릅니다.

## 6. 수신 데이터 확인

ROS 2를 사용하기 전에 standalone reader에서 실제 EC-15 출력이 들어오는지 확인합니다.

```bash
cd ~/inpyo_ws/cas_ec15_pyserial
./ec15_check.sh /dev/ttyUSB0 --raw
```

정상 예시:

```text
RAW  | PCS:        0
RAW  | Tare:          g
RAW  | NET:        9  g
WEIGHT | 9.000 g | 안정
RAW  | U/W:        0  g
```

중량 상태는 다음처럼 구분합니다.

| 출력 | 의미 |
|---|---|
| `NET` | 안정된 순중량 |
| `net` | 불안정한 순중량 |

ROS 2 publisher는 안정 상태인 `NET`만 사용합니다.

## 7. 확인 순서

통신이 되지 않을 때는 아래 순서로 확인합니다.

1. USB-RS232 변환기가 `/dev/ttyUSB*`로 인식되는지 확인
2. EC-15 DB9 TX/RX/GND 배선 확인
3. EC-15 전송 방법이 연속 전송인지 확인
4. EC-15 baud rate와 reader 설정이 같은지 확인
5. standalone reader에서 원본 데이터 확인
6. standalone 통신이 정상인 뒤 ROS 2 node 실행

이 순서를 지키면 하드웨어 통신 문제와 ROS 2 문제를 분리해서 확인할 수 있습니다.
