# UQR divergence from upstream flir_camera_driver_ros2

This is a UQ Racing fork of `flir_camera_driver_ros2`. This file records how it
diverges from upstream so the changes can be reviewed and, where noted,
upstreamed later. The pre-existing UQR "car config" (commit `ebc563a`) tuned
the launch parameters for our Blackfly S; the entries below are the audit
follow-up fixes (branch `improve/flir_camera_driver_ros2-audit-20260704`).

## Behavioural patches

- **Image buffer is now FIFO (`spinnaker_camera_driver/src/camera.cpp`).**
  `Camera::run()` consumed the frame queue with `back()`/`pop_back()` while the
  producer `push_back()`ed and dropped the newest frame on overflow, making the
  deque a LIFO stack. After the queue filled once, the frames at the front were
  never popped: usable depth collapsed to one, frames could publish out of
  capture order, and the dropped-frame counter over-reported. Now consumed with
  `front()`/`pop_front()` for true FIFO. **Upstream bug, upstreamable.**

- **`frame_rate_continous` typo fixed (`.../launch/driver_node.launch.py`).**
  The `blackfly_s` and `chameleon` launch parameter sets misspelled the key, so
  ROS silently dropped the override and continuous frame-rate mode was never
  set. Corrected to `frame_rate_continuous`, the name the driver declares
  (`config/blackfly_s.yaml`, `config/chameleon.yaml`). **UQR-introduced in the
  car config; the fix is upstreamable spelling.**

- **Dead `frame_rate_auto` overrides removed (`.../launch/driver_node.launch.py`).**
  `frame_rate_auto` is only declared for the `grasshopper` type
  (`config/grasshopper.yaml`); the `blackfly_s` and `blackfly` overrides were
  silently ignored. Removed those two dead keys; the valid `grasshopper` one is
  left in place. **Upstream copy-paste, upstreamable.**

- **Dead `~/control` remap removed (`.../launch/driver_node.launch.py`).**
  The `~/control` subscription is only created when `enable_external_control` is
  true (default false, never set by this launch), so the remap had no effect.
  Removed. **Upstream/UQR launch cruft, upstreamable.**

## Description package

- **Optional mount joint on the Blackfly S xacro macro
  (`flir_camera_description/urdf/flir_blackfly_s.urdf.xacro`).**
  Added `parent` / `mount_xyz` / `mount_rpy` parameters so the camera can be
  welded onto a host robot (e.g. the car URDF). With no `parent` the macro
  behaves exactly as before (standalone root link, used by `demo.urdf.xacro`).
  Also fixed two typos that made the lens link's `<inertial>` a no-op
  (`<intertial>`, `<mass values=...>`). **Additive + bugfix, upstreamable.**

## UQR-specific additions (not for upstream)

- **`spinnaker_camera_driver/launch/uqr_record.launch.py`** — runs the driver
  plus a rosbag2 recorder, parameterised by serial / frame rate, for capturing
  camera data for offline visualisation.
- **`docs/UQR_INTEGRATION.md`** — how to add the camera to the car URDF and how
  to record.

## Not changed (noted for the bench)

- Whether `AcquisitionFrameRateAuto` exists on our Blackfly S is unverified; it
  is not referenced by the Blackfly S config or launch after the cleanup above.
