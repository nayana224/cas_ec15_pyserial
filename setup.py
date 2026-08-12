from setuptools import setup


package_name = "cas_ec15_pyserial"


setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    py_modules=["ec15_reader"],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools", "pyserial>=3.5,<4.0"],
    zip_safe=True,
    maintainer="nayana224",
    maintainer_email="nayana224@users.noreply.github.com",
    description="CAS EC-15 RS-232 reader and ROS 2 weight publisher.",
    license="TODO",
    entry_points={
        "console_scripts": [
            "ec15_reader = ec15_reader:main",
            "ec15_udev_setup = cas_ec15_pyserial.udev_setup:main",
            "ec15_weight_node = cas_ec15_pyserial.ros2_node:main",
        ],
    },
)
