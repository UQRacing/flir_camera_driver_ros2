# -----------------------------------------------------------------------------
# UQ Racing recording launch for the FLIR Blackfly S.
#
# Brings up the camera driver and a rosbag2 recorder in one shot. It exists so
# the car can capture camera data for offline visualisation while the camera is
# not yet wired into a live perception consumer (see docs/UQR_INTEGRATION.md).
#
# This is a UQR-specific launch file. The camera parameters below intentionally
# mirror the 'blackfly_s' block of driver_node.launch.py (kept separate so that
# file stays a clean, upstreamable example); frame_rate and serial are promoted
# to launch arguments here so a run can be retuned without editing the file.
# -----------------------------------------------------------------------------

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument as LaunchArg
from launch.actions import ExecuteProcess, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration as LaunchConfig
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def blackfly_s_parameters(frame_rate):
    """Return the Blackfly S parameter set with a caller-supplied frame rate."""
    return {
        'debug': False,
        'compute_brightness': False,
        'adjust_timestamp': True,
        'dump_node_map': False,
        'pixel_format': 'BayerRG8',
        'exposure_auto': 'Off',
        'gev_scps_packet_size': 9000,
        'image_width': 1920,
        'image_height': 608,
        'offset_x': 0,
        'offset_y': 0,
        'frame_rate_continuous': True,
        'frame_rate': frame_rate,
        'frame_rate_enable': True,
        'buffer_queue_size': 20,
        'trigger_mode': 'Off',
        'chunk_mode_active': True,
        'chunk_selector_frame_id': 'FrameID',
        'chunk_enable_frame_id': True,
        'chunk_selector_exposure_time': 'ExposureTime',
        'chunk_enable_exposure_time': True,
        'chunk_selector_gain': 'Gain',
        'chunk_enable_gain': True,
        'chunk_selector_timestamp': 'Timestamp',
        'chunk_enable_timestamp': True,
    }


def launch_setup(context, *args, **kwargs):
    camera_name = LaunchConfig('camera_name').perform(context)
    serial = LaunchConfig('serial').perform(context)
    frame_rate = float(LaunchConfig('frame_rate').perform(context))

    parameter_file = PathJoinSubstitution(
        [FindPackageShare('spinnaker_camera_driver'), 'config', 'blackfly_s.yaml']
    )

    driver = Node(
        package='spinnaker_camera_driver',
        executable='camera_driver_node',
        output='screen',
        name=camera_name,
        parameters=[
            blackfly_s_parameters(frame_rate),
            {
                'ffmpeg_image_transport.encoding': 'hevc_nvenc',
                'parameter_file': parameter_file,
                'serial_number': serial,
            },
        ],
    )

    # Record everything the driver publishes under the camera namespace
    # (image_raw + transport variants, camera_info, and meta). To keep bags
    # small, narrow the regex to e.g. '/<camera_name>/image_raw/ffmpeg' and
    # '/<camera_name>/camera_info'.
    recorder = ExecuteProcess(
        cmd=[
            'ros2', 'bag', 'record',
            '--output', LaunchConfig('bag_output'),
            '--regex', '/' + camera_name + '/.*',
        ],
        output='screen',
        condition=IfCondition(LaunchConfig('record')),
    )

    return [driver, recorder]


def generate_launch_description():
    return LaunchDescription(
        [
            LaunchArg(
                'camera_name',
                default_value='flir_camera',
                description='camera name (ros node name and topic namespace)',
            ),
            LaunchArg(
                'serial',
                default_value="'16335749'",
                description='FLIR serial number of camera (in quotes!!)',
            ),
            LaunchArg(
                'frame_rate',
                default_value='20.0',
                description='acquisition frame rate in Hz',
            ),
            LaunchArg(
                'bag_output',
                default_value='flir_record',
                description='rosbag2 output directory',
            ),
            LaunchArg(
                'record',
                default_value='true',
                description='start a rosbag2 recorder alongside the driver',
            ),
            OpaqueFunction(function=launch_setup),
        ]
    )
