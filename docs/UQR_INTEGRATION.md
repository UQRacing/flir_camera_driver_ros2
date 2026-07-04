# UQ Racing integration notes — FLIR Blackfly S

Status: **recording only.** The camera is wired into the vehicle model so its
frame is published on TF and its data can be recorded for offline
visualisation. There is no live perception consumer of the camera topics yet.

This document covers the two integration touch points:

1. Adding the camera to the car URDF (so `camera_frame*` appears on TF).
2. Running the driver and recording its topics.

---

## 1. URDF wiring

The camera model is a xacro macro:
`flir_camera_description/urdf/flir_blackfly_s.urdf.xacro`. It now takes an
optional mount: pass a `parent` link plus `mount_xyz` / `mount_rpy` and the
macro welds the camera onto that link with a fixed joint. Passing no `parent`
(the default) leaves `${frame}` as a root link, which is how
`demo.urdf.xacro` still uses it.

### The car URDF today

The vehicle description lives **outside this repository** at
`mission_launchers/urdf/AV25 Spider.urdf` and is a plain (non-xacro) URDF:

```xml
<robot name="uqr_static_frames">
  <link name="base_footprint"/>
  <link name="laser_link"/>
  <link name="imu_link_ned"/>
  ...
</robot>
```

It is loaded verbatim by `mission_launchers/launch/components/tf.launch.py`
(`robot_description = open(urdf_path).read()`). To pull in a xacro macro that
file must be processed by xacro first. That change lives in the
`mission_launchers` package and is not made here.

### The snippet to add (mission_launchers side)

Rename the vehicle description to `AV25 Spider.urdf.xacro`, add the xacro
namespace and the `dark_grey` material (the macro references it), include the
macro, and instantiate it against `base_footprint`:

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="uqr_static_frames">

  <!-- the macro's visuals reference this material by name -->
  <material name="dark_grey">
    <color rgba="0.5 0.5 0.5 1.0"/>
  </material>

  <link name="base_footprint"/>
  <link name="laser_link"/>
  <link name="imu_link_ned"/>
  <!-- ... existing joints ... -->

  <xacro:include
    filename="$(find flir_camera_description)/urdf/flir_blackfly_s.urdf.xacro"/>

  <!-- TODO(measure): mount_xyz / mount_rpy are placeholders. Replace with the
       camera pose relative to base_footprint from CAD or a bench measurement. -->
  <xacro:flir_blackfly_s
    frame="camera_frame"
    name="flir_blackfly_s"
    parent="base_footprint"
    mount_xyz="0.3 0.0 1.10"
    mount_rpy="0 0 0"/>

</robot>
```

Then, in `tf.launch.py`, process the file with xacro instead of reading it
raw, e.g.:

```python
from launch.substitutions import Command
robot_description = Command(['xacro', ' ', urdf_path])
# parameters=[{'robot_description': robot_description}]
```

This adds `camera_frame`, `camera_frame_lens` and `camera_frame_optical` to
the TF tree under `base_footprint`.

### Frame id

The driver stamps images with `header.frame_id` equal to the node name by
default. For TF-consistent recordings set the driver's `frame_id` parameter to
the optical link, `camera_frame_optical`, so recorded images line up with the
published camera frame.

---

## 2. Recording launch

`spinnaker_camera_driver/launch/uqr_record.launch.py` starts the Blackfly S
driver and a rosbag2 recorder in one shot. It is parameterised by serial and
frame rate:

```bash
ros2 launch spinnaker_camera_driver uqr_record.launch.py \
  serial:="'16335749'" \
  frame_rate:=20.0 \
  camera_name:=flir_camera \
  bag_output:=flir_record_$(date +%Y%m%d_%H%M%S)
```

Arguments:

| arg          | default        | meaning                                        |
|--------------|----------------|------------------------------------------------|
| `camera_name`| `flir_camera`  | node name and topic namespace                  |
| `serial`     | `'16335749'`   | FLIR serial number (keep the inner quotes)     |
| `frame_rate` | `20.0`         | acquisition frame rate (Hz)                    |
| `bag_output` | `flir_record`  | rosbag2 output directory                       |
| `record`     | `true`         | set `false` to run the driver without recording|

By default it records everything under `/<camera_name>/` (raw image and its
transport variants, `camera_info`, and `meta`). Raw Bayer frames are large; to
keep bags small, narrow the record regex in the launch file to just the
FFmpeg-encoded image and camera info, e.g. `/<camera_name>/image_raw/ffmpeg`
and `/<camera_name>/camera_info` (the driver is configured for
`hevc_nvenc`, so the FFmpeg topic is hardware-encoded).

The camera parameters in this launch mirror the `blackfly_s` block of
`driver_node.launch.py`; they are duplicated deliberately so that file stays a
clean, upstreamable example while UQR-specific tuning lives here.
