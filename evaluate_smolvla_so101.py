#!/usr/bin/env python3

"""
Evaluate SmolVLA policy on SO101 follower robot.

SmolVLA is a Vision-Language-Action model that can understand instructions
and perform robotic tasks. This script loads the pretrained SmolVLA model
and runs it on a real SO101 follower robot.
"""

from lerobot.common.datasets.utils import build_dataset_frame, hw_to_dataset_features
from lerobot.common.policies.smolvla.modeling_smolvla import SmolVLAPolicy
from lerobot.common.robots.so101_follower import SO101Follower, SO101FollowerConfig
from lerobot.common.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.common.utils.control_utils import predict_action
from lerobot.common.utils.utils import get_safe_torch_device
import torch
import torch.nn.functional as F
import numpy as np
import cv2

# Configuration
NB_EVALUATION_CYCLES = 1  # Number of control cycles to run
POLICY_PATH = "lerobot/smolvla_base"  # SmolVLA pretrained model
ROBOT_PORT = "/dev/ttyACM1"  # Your robot's USB port
ROBOT_ID = "boen_follower"
TASK_INSTRUCTION = "Pick up the cube and Place in the box."  # Task instruction

def main():
    # Configure robot with cameras (SmolVLA needs visual input)
    robot_config = SO101FollowerConfig(
        port=ROBOT_PORT,
        id=ROBOT_ID,
        cameras={
            "image": OpenCVCameraConfig(
                index_or_path=0,
                width=640,
                height=480,
                fps=30
            ),
            "image2": OpenCVCameraConfig(
                index_or_path=2, 
                width=640,
                height=480,
                fps=30
            )
        }
    )
    
    # Initialize robot
    print("Connecting to SO101 follower robot...")
    robot = SO101Follower(robot_config)
    robot.connect(calibrate=False)  # Set to True if you need calibration
    
    # Load SmolVLA policy
    print(f"Loading SmolVLA policy from {POLICY_PATH}...")
    try:
        policy = SmolVLAPolicy.from_pretrained(POLICY_PATH)
        policy.reset()
        print("SmolVLA policy loaded successfully!")
    except Exception as e:
        print(f"Error loading SmolVLA policy: {e}")
        print("Make sure you have installed smolvla dependencies: pip install -e '.[smolvla]'")
        robot.disconnect()
        return
    
    # Prepare observation features for policy input
    obs_features = hw_to_dataset_features(robot.observation_features, "observation")
    
    print("Starting SmolVLA policy evaluation...")
    print(f"Task instruction: '{TASK_INSTRUCTION}'")
    print(f"Running {NB_EVALUATION_CYCLES} control cycles")
    print("Press Ctrl+C to stop early")
    
    try:
        for i in range(NB_EVALUATION_CYCLES):
            # Get current observation from robot (includes camera images)
            obs = robot.get_observation()
            
            # Convert observation to format expected by policy
            observation_frame = build_dataset_frame(obs_features, obs, prefix="observation")
            
            # Add task instruction to the observation (SmolVLA needs language input)
            # Note: The exact key name may vary depending on SmolVLA's expected input format
            observation_frame["observation.language_instruction"] = TASK_INSTRUCTION

            print(observation_frame)
            print("==")
            
            # Resize images to 256x256 before processing
            for key in ['observation.images.image', 'observation.images.image2']:
                if key in observation_frame and isinstance(observation_frame[key], np.ndarray):
                    # Assuming image is in shape [H, W, C] numpy array
                    img = observation_frame[key]
                    print(f"{key} shape: {img.shape}")
                    
                    # Resize numpy array using cv2
                    # cv2.resize expects (width, height), not (height, width)
                    img_resized = cv2.resize(img, (256, 256), interpolation=cv2.INTER_LINEAR)
                    print(f"{key} shape: {img_resized.shape}")
                    
                    # Keep as numpy array
                    observation_frame[key] = img_resized

            observation_frame["observation.images.image3"] = observation_frame["observation.images.image2"]

            observation_frame["observation.image"] = observation_frame["observation.images.image"].transpose(2,0,1)
            observation_frame["observation.image2"] = observation_frame["observation.images.image2"].transpose(2,0,1)
            observation_frame["observation.image3"] = observation_frame["observation.images.image3"].transpose(2,0,1)
            print(observation_frame.keys())

            
            # Predict next action using SmolVLA policy
            try:
                # SmolVLA uses select_action method for inference
                with torch.no_grad():
                    # Convert to tensors and add batch dimension if needed
                    for key, value in observation_frame.items():
                        if isinstance(value, torch.Tensor):
                            if value.dim() == 3 and "image" in key:  # Image tensor [H,W,C] -> [1,C,H,W]
                                observation_frame[key] = value.permute(2, 0, 1).unsqueeze(0)
                            elif value.dim() == 1:  # State vector -> [1, state_dim]
                                observation_frame[key] = value.unsqueeze(0)
                    
                    # Get action from SmolVLA
                    #print(observation_frame)
                    action_tensor = policy.select_action(observation_frame)
                    
                    # Convert tensor to dict format expected by robot
                    if isinstance(action_tensor, torch.Tensor):
                        action_values = action_tensor.squeeze(0).cpu().numpy()
                        action = {key: float(action_values[j]) for j, key in enumerate(robot.action_features)}
                    else:
                        # Handle case where select_action returns a dict
                        action = {key: value.item() if torch.is_tensor(value) else value 
                                 for key, value in action_tensor.items()}
                
            except Exception as e:
                print(f"Error in policy inference at step {i}: {e}")
                print("Skipping this step...")
                continue
            
            # Send action to robot
            try:
                robot.send_action(action)
            except Exception as e:
                print(f"Error sending action to robot at step {i}: {e}")
                continue
            
            # Print progress every 50 cycles
            if (i + 1) % 50 == 0:
                print(f"Completed {i + 1}/{NB_EVALUATION_CYCLES} cycles")
                
    except KeyboardInterrupt:
        print("\nEvaluation stopped by user")
    except Exception as e:
        print(f"Error during evaluation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Always disconnect robot
        print("Disconnecting robot...")
        robot.disconnect()
        print("SmolVLA evaluation completed!")

if __name__ == "__main__":
    main()
