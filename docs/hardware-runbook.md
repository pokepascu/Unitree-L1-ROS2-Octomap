# Connecting and validating the Unitree L1

This procedure covers connection, validation, and recording with an L1 and its
Unitree adapter. Software preparation, building, and data-independent tests can
still be completed without the sensor.

## 1. Safety before applying power

- Secure the L1 and clear its mechanical operating area.
- Disconnect power before changing any wiring.
- Use the Unitree cable and adapter described in the manual.
- Observe the separate 12 V / 1 A supply requirement and its polarity.
- Do not power the L1 from 5 V USB.
- Never connect 3.3 V TTL directly to USB or RS-232.
- The driver uses 2,000,000 baud; do not change this value without evidence.

The expected connection is L1 to Unitree serial adapter, adapter to the PC's USB
port, and a separate 12 V supply. The mechanism may start moving; keep hands,
cables, and objects outside its operating area.

## 2. Identify the new port without modifying the host

Run this before connection, then again after connecting USB and applying power:

```bash
# From the repository root
./scripts/check-lidar.sh
```

The script requires `udev` and reports USB devices, `/dev/serial/by-id`, the
resolved `ttyUSB*` or `ttyACM*` device, VID/PID, serial number, group, and any
process using the port. It changes no permissions, services, or `udev` rules.

If several adapters are present, explicitly select the stable link and resolve
its actual device:

```bash
export LIDAR_DEVICE="$(readlink -e /dev/serial/by-id/<identified-adapter>)"
test -c "$LIDAR_DEVICE"
export LIDAR_GID="$(stat -Lc '%g' "$LIDAR_DEVICE")"
```

Do not use `chmod 777`. `group_add` passes only the tty GID into the container.
ModemManager is active on the validated host; do not disable it pre-emptively.
If `check-lidar.sh` proves that it persistently opens this specific adapter,
record the VID, PID, and serial number first, then consider a targeted
`ID_MM_DEVICE_IGNORE` rule. Do not kill a process based on an assumption.

## 3. First launch without RViz

The first run minimises the number of variables:

```bash
START_RVIZ=false ./scripts/lidar-launch.sh
```

The script:

1. rejects a missing, ambiguous, unexpected, or busy port;
2. calculates the GID of the resolved device;
3. tests read and write access in an ephemeral, unprivileged container;
4. starts `unitree_lidar_ros2_node` and `l1_monitor` in the named
   `unitree_l1_runtime` container.

The mere presence of the node or publishers is not a success condition: the
vendor driver ignores the return value of `initialize()` and can remain alive
without publishing data.

In a second terminal, require actual messages and non-zero rates:

```bash
# From the repository root
./scripts/lidar-validate.sh
```

The output is also retained locally under the Git-ignored `logs/tests/`
directory. A `LIDAR_DATA_VALIDATION_PASS` verdict requires one PointCloud2
message, one Imu message, a measured rate for each, and one `/diagnostics`
message.

If the port opens but no data appears, stop cleanly with `Ctrl-C`. The vendor
ROS 2 driver does not explicitly request `NORMAL` mode; check the L1 state before
making any adaptation. A necessary correction must remain in project code,
check the initialisation result, and be tested and documented. Never apply it
silently to the pinned vendor tree.

## 4. RViz2 visualisation

After validating the streams:

```bash
START_RVIZ=true ./scripts/lidar-launch.sh
```

The project profile uses `/unilidar/cloud`, Reliable/Volatile QoS, and the
`unilidar_lidar` fixed frame. The driver publishes no TF, so this frame is
intentional for raw visualisation. The GUI overlay mounts only the read-only X11
cookie and `/dev/dri` devices, without `xhost +` or privileged mode.

## 5. Record a short bag

While `lidar-launch.sh` is running, execute this in a second terminal:

```bash
BAG_LABEL=validation BAG_DURATION_SEC=30 ./scripts/record-bag.sh
```

The script refuses to start unless both cloud and IMU messages arrive. It always
records `/unilidar/cloud` and `/unilidar/imu`, then adds `/diagnostics`, `/tf`,
and `/tf_static` only when they exist. A bounded recording receives `SIGINT` so
rosbag2 can finalise `metadata.yaml`.

Inspect the result:

```bash
./scripts/bag-info.sh bags/l1_validation_<timestamp>
```

A bag is valid only when its cloud and IMU message counts are both greater than
zero.

## 6. Replay without the LiDAR

After stopping the hardware runtime with `Ctrl-C` and disconnecting it if
desired:

```bash
START_RVIZ=true ./scripts/replay-bag.sh bags/l1_validation_<timestamp>
```

Replay starts the monitor and RViz in the same container as `ros2 bag play`.
Compare types, rates, timestamps, frames, fields, and point counts with the live
test. Keep the short validation bag separate from a future mapping run.

## 7. Shutdown and reconnection

- Stop the launch process and every recording with `Ctrl-C`.
- Check `docker ps`; no project runtime should remain active.
- After disconnecting and reconnecting USB, rerun `./scripts/check-lidar.sh` and
  recreate the container. Do not assume `/dev/ttyUSB0` still refers to the same
  device.
- Keep raw data and logs outside Git. Update `docs/validation-matrix.md` whenever
  a reproducible check changes status.

Point-LIO integration remains pending. Its selection and tuning must use the
validated real messages, including PointCloud2 fields, timestamps, units, and
LiDAR-to-IMU extrinsics.
