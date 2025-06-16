#!/usr/bin/env python3

from lerobot.common.motors.feetech import FeetechMotorsBus
from lerobot.common.motors import Motor, MotorNormMode

# SO101 Leader의 모터 설정
motors = {
    "shoulder_pan": Motor(1, "sts3215", MotorNormMode.RANGE_M100_100),
    "shoulder_lift": Motor(2, "sts3215", MotorNormMode.RANGE_M100_100),
    "elbow_flex": Motor(3, "sts3215", MotorNormMode.RANGE_M100_100),
    "wrist_flex": Motor(4, "sts3215", MotorNormMode.RANGE_M100_100),
    "wrist_roll": Motor(5, "sts3215", MotorNormMode.RANGE_M100_100),
    "gripper": Motor(6, "sts3215", MotorNormMode.RANGE_0_100),
}

# 포트 설정
PORT = '/dev/ttyACM_follower'

# FeetechMotorsBus 생성
bus = FeetechMotorsBus(
    port=PORT,
    motors=motors,
    protocol_version=0
)

try:
    # 연결
    bus.connect()
    print("Connected to motors\n")
    
    # 각 모터의 현재 위치 읽기
    print("Motor positions:")
    print("-" * 50)
    
    for motor_name, motor_obj in motors.items():
        try:
            # Present Position 읽기 (정규화되지 않은 raw 값)
            position = bus.read("Present_Position", motor_name, normalize=False)
            
            # 한 바퀴는 4096
            full_turns = position // 4096
            within_turn = position % 4096
            
            # Homing offset 계산 시 문제가 될 수 있는지 확인
            # 중간 위치(2048)에서의 offset
            potential_offset = position - 2048
            
            print(f"{motor_name} (ID {motor_obj.id}):")
            print(f"  Raw position: {position}")
            print(f"  Full turns: {full_turns}, Position within turn: {within_turn}")
            print(f"  Potential homing offset: {potential_offset}")
            
            if abs(potential_offset) > 2047:
                print(f"  ⚠️  WARNING: This motor will cause calibration error!")
                print(f"     (Offset {potential_offset} exceeds ±2047 limit)")
            
            print()
            
        except Exception as e:
            print(f"{motor_name} (ID {motor_obj.id}): Error reading position - {e}")
            print()
    
    # 연결 해제
    bus.disconnect()
    
except Exception as e:
    print(f"Error: {e}")
