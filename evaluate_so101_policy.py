#!/usr/bin/env python3

"""
Evaluate a trained imitation learning policy on SO101 follower robot.
"""

from lerobot.common.datasets.utils import build_dataset_frame, hw_to_dataset_features
from lerobot.common.policies.act.modeling_act import ACTPolicy
from lerobot.common.robots.so101_follower import SO101Follower, SO101FollowerConfig
from lerobot.common.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.common.utils.control_utils import predict_action
from lerobot.common.utils.utils import get_safe_torch_device
import torch
import torch.nn.functional as F

# Configuration
NB_EVALUATION_CYCLES = 1000  # Number of control cycles to run
POLICY_PATH = "ruanwz/act_so101-record-test-0611"  # Your trained policy
ROBOT_PORT = "/dev/ttyACM1"  # Your robot's USB port
ROBOT_ID = "boen_follower"

def main():
    # Configure robot
    robot_config = SO101FollowerConfig(
        port=ROBOT_PORT,
        id=ROBOT_ID,
        cameras={
            "image": OpenCVCameraConfig(
                index_or_path=0,
                width=256,
                height=256,
                fps=30
            ),
            "image2": OpenCVCameraConfig(
                index_or_path=2,
                width=256,
                height=256,
                fps=30
            ),
            "image3": OpenCVCameraConfig(
                index_or_path=2,
                width=256,
                height=256,
                fps=30
            )
        }
    )
    
    # Initialize robot
    print("Connecting to SO101 follower robot...")
    robot = SO101Follower(robot_config)
    robot.connect(calibrate=False)  # Set to True if you need calibration
    
    # Load trained policy
    print(f"Loading policy from {POLICY_PATH}...")
    policy = ACTPolicy.from_pretrained(POLICY_PATH)
    policy.reset()
    
    # Prepare observation features for policy input
    obs_features = hw_to_dataset_features(robot.observation_features, "observation")
    
    print("Starting policy evaluation...")
    print(f"Running {NB_EVALUATION_CYCLES} control cycles")
    print("Press Ctrl+C to stop early")
    
    try:
        for i in range(NB_EVALUATION_CYCLES):
            # Get current observation from robot
            obs = robot.get_observation()
            
            # Convert observation to format expected by policy
            observation_frame = build_dataset_frame(obs_features, obs, prefix="observation")
            
            # Resize images to 256x256
            for key in ['observation.images.image', 'observation.images.image2']:
                if key in observation_frame and isinstance(observation_frame[key], torch.Tensor):
                    # Assuming image is in shape [H, W, C], convert to [C, H, W] for interpolation
                    img = observation_frame[key]
                    if img.dim() == 3 and img.shape[-1] == 3:  # [H, W, C]
                        img = img.permute(2, 0, 1).unsqueeze(0)  # [1, C, H, W]
                    elif img.dim() == 3 and img.shape[0] == 3:  # [C, H, W]
                        img = img.unsqueeze(0)  # [1, C, H, W]
                    
                    # Resize to 256x256
                    img_resized = F.interpolate(img, size=(256, 256), mode='bilinear', align_corners=False)
                    
                    # Convert back to original format
                    img_resized = img_resized.squeeze(0).permute(1, 2, 0)  # [256, 256, C]
                    observation_frame[key] = img_resized
            
            print(observation_frame)
            # Predict next action using the policy
            action_values = predict_action(
                observation_frame, 
                policy, 
                get_safe_torch_device(policy.config.device), 
                policy.config.use_amp
            )
            print(i)
            
            # Convert action values to robot action format
            action = {key: action_values[j].item() for j, key in enumerate(robot.action_features)}
            
            # Send action to robot
            robot.send_action(action)
            
            # Print progress every 100 cycles
            if (i + 1) % 100 == 0:
                print(f"Completed {i + 1}/{NB_EVALUATION_CYCLES} cycles")
                
    except KeyboardInterrupt:
        print("\nEvaluation stopped by user")
    except Exception as e:
        print(f"Error during evaluation: {e}")
    finally:
        # Always disconnect robot
        print("Disconnecting robot...")
        robot.disconnect()
        print("Evaluation completed!")

if __name__ == "__main__":
    main()
