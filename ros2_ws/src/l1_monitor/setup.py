from setuptools import find_packages, setup

package_name = "l1_monitor"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Unitree L1 project",
    maintainer_email="noreply@example.invalid",
    description="Read-only diagnostics for Unitree L1 point cloud and IMU streams.",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "l1_monitor = l1_monitor.monitor_node:main",
        ],
    },
)
