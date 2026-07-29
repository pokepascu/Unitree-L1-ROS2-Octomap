from glob import glob
from setuptools import find_packages, setup

package_name = "l1_bringup"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
        ("share/" + package_name + "/config", glob("config/*.yaml")),
        ("share/" + package_name + "/config", glob("config/*.rviz")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Unitree L1 project",
    maintainer_email="noreply@example.invalid",
    description="Configurable launch and configuration for the Unitree L1 project.",
    license="MIT",
    tests_require=["pytest"],
)
