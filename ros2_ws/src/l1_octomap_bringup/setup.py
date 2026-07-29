from glob import glob

from setuptools import find_packages, setup

package_name = "l1_octomap_bringup"

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
    maintainer="Pascual Asio Serrano",
    maintainer_email="103388150+pokepascu@users.noreply.github.com",
    description="Project-owned OctoMap bringup for Unitree L1 point clouds.",
    license="MIT",
    url="https://github.com/pokepascu/Unitree-L1-ROS2-Octomap",
    tests_require=["pytest"],
)
