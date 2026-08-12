"""CAS EC-15 안정 중량을 ROS 2 topic으로 발행한다."""

from __future__ import annotations

import queue
import threading

import rclpy
from rclpy.node import Node
import serial
from serial import SerialException
from std_msgs.msg import Float64

from cas_ec15_pyserial.protocol import parse_weight


class Ec15WeightNode(Node):
    """EC-15의 안정된 순중량만 g 단위로 발행한다."""

    def __init__(self) -> None:
        super().__init__("ec15_weight_node")

        self.declare_parameter("port", "/dev/ttyUSB0")
        self.declare_parameter("baudrate", 9600)
        self.declare_parameter("topic_name", "weight_g")

        port = self.get_parameter("port").value
        baudrate = self.get_parameter("baudrate").value
        topic_name = self.get_parameter("topic_name").value

        if not isinstance(port, str) or not port:
            raise ValueError("parameter 'port' must be a non-empty string")
        if baudrate not in (2400, 4800, 9600):
            raise ValueError("parameter 'baudrate' must be one of 2400, 4800, 9600")
        if not isinstance(topic_name, str) or not topic_name:
            raise ValueError("parameter 'topic_name' must be a non-empty string")

        self._publisher = self.create_publisher(Float64, topic_name, 10)
        self._weights: queue.Queue[float] = queue.Queue(maxsize=1)
        self._stop_event = threading.Event()

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

        self.get_logger().info(
            f"EC-15 connected: port={port}, baudrate={baudrate}, topic={topic_name}"
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
            if weight is None or not weight.stable:
                continue

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
        self._publisher.publish(message)

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
