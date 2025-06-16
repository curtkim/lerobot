
```
nix develop

python lerobot/find_port.py

python -m lerobot.setup_motors --robot.type=so101.leader --robot.port=/dev/ttyACM_leader
python -m lerobot.setup_motors --robot.type=so101_follower --robot.port=/dev/ttyACM_follower

python -m lerobot.calibrate --teleop.type=so101_leader --teleop.port=/dev/ttyACM_leader --teleop.id=boen
python -m lerobot.calibrate --robot.type=so101_follower --robot.port=/dev/ttyACM_follower --robot.id=boen_follower

python -m lerobot.teleoperate \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM_follower \
    --robot.id=boen_follower \
    --teleop.type=so101_leader \
    --teleop.port=/dev/ttyACM_leader \
    --teleop.id=boen

python -m lerobot.teleoperate \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM_follow \
    --robot.id=boen_follower \
    --robot.cameras="{ front: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}}" \
    --teleop.type=so101_leader \
    --teleop.port=/dev/ttyACM_leader \
    --teleop.id=boen \
    --display_data=true

```

## Record
```
HF_USER=$(huggingface-cli whoami | head -n 1)
echo $HF_USER

PYTORCH_ENABLE_MPS_FALLBACK=1 python -m lerobot.record \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM_follower \
    --robot.id=boen_follower \
    --robot.cameras="{ image: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}, image2: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}}" \
    --teleop.type=so101_leader \
    --teleop.port=/dev/ttyACM_leader \
    --teleop.id=boen \
    --dataset.repo_id=sanggyun/so101-pick-move \
    --dataset.num_episodes=0 \
    --dataset.single_task="Grab the black cube" \
    --dataset.push_to_hub=true \
    --display_data=false \
    --play_sounds=true \
    --resume=true



rm -rf /home/curt/.cache/huggingface/lerobot/sanggyun/record-test/

PYTORCH_ENABLE_MPS_FALLBACK=1 python -m lerobot.record \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM_follower \
    --robot.id=boen_follower \
    --robot.cameras="{ image: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}, image2: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}}" \
    --teleop.type=so101_leader \
    --teleop.port=/dev/ttyACM_leader \
    --teleop.id=boen \
    --dataset.repo_id=sanggyun/record-test \
    --dataset.num_episodes=50 \
    --dataset.single_task="Grab the black cube" \
    --dataset.push_to_hub=false \
    --display_data=false \
    --play_sounds=true

    --resume=true



```

## replay
```
python -m lerobot.replay \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM_follower \
    --robot.id=boen_follower \
    --dataset.repo_id=sanggyun/record-test \
    --dataset.episode=0
```

## train
```
python lerobot/scripts/train.py \
  --dataset.repo_id=sanggyun/record-test \
  --policy.type=act \
  --output_dir=outputs/train/record-test \
  --job_name=record-test
```

## Evaluate
```
huggingface-cli download ruanwz/act_so101-record-test-0611
huggingface-cli download --repo-type dataset ruanwz/so101-record-test-0611


# toraise
PYTORCH_ENABLE_MPS_FALLBACK=1 python -m lerobot.record \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM_follower \
    --robot.id=boen_follower \
    --robot.cameras="{ image: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}, image2: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}}" \
    --teleop.type=so101_leader \
    --teleop.port=/dev/ttyACM_leader \
    --teleop.id=boen \
    --dataset.repo_id=sanggyun/eval_record-test \
    --dataset.num_episodes=50 \
    --dataset.single_task="Grab the black cube" \
    --dataset.push_to_hub=false \
    --display_data=false \
    --play_sounds=true \
    --resume=true


# fail
python -m lerobot.record  \
  --robot.type=so101_follower \
  --robot.port=/dev/ttyACM_follower \
  --robot.cameras="{front: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}}"  \
  --robot.id=boen_follower \
  --dataset.repo_id=ruanwz/so101-record-test-0611 \
  --dataset.single_task="Put lego brick into the transparent box" \
  --policy.path=ruanwz/act_so101-record-test-0611 \
    --dataset.repo_id=sanggyun/record-test-eval \
    --dataset.num_episodes=2 \
    --dataset.single_task="Grab the black cube" \
    --dataset.push_to_hub=false \
    --display_data=false \
    --play_sounds=false \



PYTORCH_ENABLE_MPS_FALLBACK=1 python -m lerobot.record \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM_follower \
    --robot.id=boen_follower \
    --robot.cameras="{front: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}}"  \
  --policy.path=ruanwz/act_so101-record-test-0611 \
    --dataset.repo_id=sanggyun/record-test \
    --dataset.num_episodes=2 \
    --dataset.single_task="Grab the black cube" \
    --dataset.push_to_hub=false \
    --display_data=false \
    --play_sounds=false 
```


## smolvla
```
python -m lerobot.record \
    --robot.type=so101_follower \
    --robot.port=/dev/ttyACM_follower \
    --robot.id=boen_follower \
    --robot.cameras="{image: {type: opencv, index_or_path: 0, width: 256, height: 256, fps: 30}, image2: {type: opencv, index_or_path: 2, width: 255, height: 255, fps: 30}, image3: {type: opencv, index_or_path: 2, width: 255, height: 255, fps: 30}}"  \
  --dataset.single_task="Pick up the cube and Place in the box." \
  --dataset.repo_id=sanggyun/eval_DATASET_NAME_test \
  --dataset.episode_time_s=50 \
  --dataset.num_episodes=10 \
  --policy.path=lerobot/smolvla_base

```
