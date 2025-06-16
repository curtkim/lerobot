#!/usr/bin/env python3
"""
Test script to create a RecordConfig from CLI arguments.

This demonstrates how lerobot.record parses CLI arguments to create a RecordConfig object.

Example usage:
    python test_record_config.py \
        --robot.type=so100_follower \
        --robot.port=/dev/tty.usbmodem58760431541 \
        --robot.cameras="{laptop: {type: opencv, camera_index: 0, width: 640, height: 480}}" \
        --robot.id=black \
        --teleop.type=so100_leader \
        --teleop.port=/dev/tty.usbmodem58760431551 \
        --teleop.id=blue \
        --dataset.repo_id=test/my-dataset \
        --dataset.num_episodes=2 \
        --dataset.single_task="Grab the cube"
"""

import sys
from dataclasses import asdict
from pprint import pprint

# Add lerobot to path if needed
sys.path.insert(0, '/home/curt/projects/lerobot')

from lerobot.record import RecordConfig, DatasetRecordConfig
from lerobot.common.robots import RobotConfig, so100_follower
from lerobot.common.teleoperators import TeleoperatorConfig, so100_leader
from lerobot.configs.policies import PreTrainedConfig
from lerobot.common.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.configs import parser


def create_record_config_from_cli():
    """
    Create a RecordConfig object from CLI arguments using the same approach as lerobot.record.
    
    This uses the @parser.wrap() decorator internally to parse CLI arguments.
    """
    # The parser.wrap() decorator handles CLI argument parsing
    @parser.wrap()
    def _parse_config(cfg: RecordConfig) -> RecordConfig:
        return cfg
    
    # Call the wrapped function which will parse sys.argv
    config = _parse_config()
    return config


def create_record_config_manually():
    """
    Example of creating a RecordConfig manually without CLI arguments.
    
    This shows the structure of the config object.

    python -m lerobot.record  \
      --robot.type=so101_follower \
      --robot.port=/dev/ttyACM1 \
      --robot.cameras="{ image: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}, image2: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}}" \
      --robot.id=boen_follower \
      --dataset.repo_id=sanggyun/record-test \
      --dataset.single_task="Grab the black cube" \
      --policy.path=toraise/act_so101_test
    """
    # Create robot config
    robot_config = so100_follower.SO100FollowerConfig(
        port="/dev/ttyACM1",
        id="so101_follower",
        cameras={
            "image": OpenCVCameraConfig(
                index_or_path=0,  # camera_index
                fps=30,
                width=640,
                height=480
            )
        }
    )
    
    # Create teleop config
    teleop_config = so100_leader.SO100LeaderConfig(
        port="/dev/tty.usbmodem58760431551",
        id="blue"
    )

    # policy_config = PreTrainedConfig(
    #     pretrained_path="toraise/act_so101_test",
    # )
    policy_config = PreTrainedConfig.from_pretrained("toraise/act_so101_test")
    
    # Create dataset config
    dataset_config = DatasetRecordConfig(
        repo_id="test/my-dataset",
        single_task="Grab the cube",
        num_episodes=2,
        fps=30,
        episode_time_s=60,
        reset_time_s=60,
        video=True,
        push_to_hub=False,
        private=False,
        num_image_writer_processes=0,
        num_image_writer_threads_per_camera=4
    )
    
    # Create the main record config
    record_config = RecordConfig(
        robot=robot_config,
        #teleop=teleop_config,
        policy = policy_config,
        dataset=dataset_config,
        display_data=False,
        play_sounds=True,
        resume=False
    )
    
    return record_config


def main():
    print("=== Creating RecordConfig from CLI arguments ===\n")
    
    if len(sys.argv) > 1:
        # Parse from CLI arguments
        try:
            config = create_record_config_from_cli()
            print("Successfully created RecordConfig from CLI arguments:")
            pprint(asdict(config))
        except Exception as e:
            print(f"Error parsing CLI arguments: {e}")
            print("\nShowing example of manual config creation instead...")
            config = create_record_config_manually()
            pprint(asdict(config))
    else:
        # Show example usage
        print("No CLI arguments provided. Showing example usage:\n")
        print(__doc__)
        
        print("\n=== Creating RecordConfig manually ===\n")
        config = create_record_config_manually()
        print("Example RecordConfig structure:")
        pprint(asdict(config))


if __name__ == "__main__":
    main()
