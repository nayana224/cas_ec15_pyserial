"""CAS EC-15 안정 중량과 통신 상태를 ROS 2 topic으로 발행한다."""

from __future__ import annotations

import queue
import threading
import time

import rclpy
from rclpy.node import Node
import serial
from serial import SerialException
from std_msgs.msg import Bool, Float64

from cas_ec15_pyserial.protocol import parse_weight


class Ec15WeightNode(Node):
    """EC-15의 안정 중량과 최근 통신 상태를 발행한다."""

    def __init__(self) -> None:
        super().__init__("ec15_weight_node")

        self.declare_parameter("port", "/dev/cas_ec15")
        self.declare_parameter("baudrate", 9600)
        self.declare_parameter("data_timeout_sec", 2.0)

        port = self.get_parameter("port").value
        baudrate = self.get_parameter("baudrate").value
        data_timeout_sec = self.get_parameter("data_timeout_sec").value

        if not isinstance(port, str) or not port:
            raise ValueError("parameter 'port' must be a non-empty string")
        if baudrate not in (2400, 4800, 9600):
            raise ValueError("parameter 'baudrate' must be one of 2400, 4800, 9600")
        if not isinstance(data_timeout_sec, (int, float)) or data_timeout_sec <= 0.0:
            raise ValueError("parameter 'data_timeout_sec' must be greater than 0")

        self._data_timeout_sec = float(data_timeout_sec)
        self._weight_publisher = self.create_publisher(Float64, "weight_g", 10)
        self._health_publisher = self.create_publisher(Bool, "scale_alive", 10)
        self._weights: queue.Queue[float] = queue.Queue(maxsize=1)
        self._stop_event = threading.Event()
        self._state_lock = threading.Lock()
        self._last_rx_time: float | None = None
        self._last_stable_time: float | None = None
        self._scale_alive = False

        self._serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1.0,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
        )
        self._serial.reset_input_buffer()

        self._reader_thread = threading.Thread(
            target=self._read_serial,
            name="ec15_serial_reader",
            daemon=True,
        )
        self._reader_thread.start()
        self._publish_timer = self.create_timer(0.02, self._publish_latest_weight)
        self._health_timer = self.create_timer(0.5, self._update_scale_health)

        self.get_logger().info(
            "EC-15 connected: "
            f"port={port}, baudrate={baudrate}, topic=weight_g, "
            f"data_timeout_sec={self._data_timeout_sec}"
        )

    def _read_serial(self) -> None:
        while not self._stop_event.is_set():
            try:
                data = self._serial.readline()
            except SerialException as error:
                if not self._stop_event.is_set():
                    self.get_logger().error(f"EC-15 serial read failed: {error}")
                return

            if not data:
                continue

            line = data.decode("ascii", errors="replace").strip("\r\n ")
            weight = parse_weight(line)
            if weight is None:
                continue

            received_at = time.monotonic()
            with self._state_lock:
                self._last_rx_time = received_at

            if not weight.stable:
                continue

            with self._state_lock:
                self._last_stable_time = received_at

            value_g = weight.value * 1000.0 if weight.unit == "kg" else weight.value
            self._replace_latest_weight(value_g)

    def _replace_latest_weight(self, value_g: float) -> None:
        try:
            self._weights.put_nowait(value_g)
            return
        except queue.Full:
            pass

        try:
            self._weights.get_nowait()
        except queue.Empty:
            pass
        self._weights.put_nowait(value_g)

    def _publish_latest_weight(self) -> None:
        try:
            value_g = self._weights.get_nowait()
        except queue.Empty:
            return

        message = Float64()
        message.data = value_g
        self._weight_publisher.publish(message)

    def _update_scale_health(self) -> None:
        now = time.monotonic()
        with self._state_lock:
            last_rx_time = self._last_rx_time

        is_alive = (
            last_rx_time is not None
            and now - last_rx_time <= self._data_timeout_sec
        )

        if is_alive != self._scale_alive:
            self._scale_alive = is_alive
            if is_alive:
                self.get_logger().info("EC-15 data reception is active")
            else:
                self.get_logger().error(
                    "EC-15 data timeout: no valid weight frame received within "
                    f"{self._data_timeout_sec:.3f} s"
                )

        message = Bool()
        message.data = is_alive
        self._health_publisher.publish(message)

    def destroy_node(self) -> bool:
        self._stop_event.set()
        if self._serial.is_open:
            self._serial.close()
        self._reader_thread.join(timeout=2.0)
        return super().destroy_node()


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node: Ec15WeightNode | None = None

    try:
        node = Ec15WeightNode()
        rclpy.spin(node)
    except (SerialException, ValueError) as error:
        if node is not None:
            node.get_logger().error(str(error))
        else:
            print(f"EC-15 node startup failed: {error}")
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
