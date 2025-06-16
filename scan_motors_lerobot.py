#!/usr/bin/env python3

from lerobot.common.motors.feetech import FeetechMotorsBus
from lerobot.common.motors import Motor, MotorNormMode

# 더미 모터 설정 (스캔용)
dummy_motors = {
    "dummy": Motor(1, "sts3215", MotorNormMode.RANGE_M100_100)
}

# 포트 설정
#PORT = '/dev/ttyACM_follower'
PORT = '/dev/ttyACM_leader'

# FeetechMotorsBus 생성
bus = FeetechMotorsBus(
    port=PORT,
    motors=dummy_motors,
    protocol_version=0  # SO101은 protocol 0 사용
)

try:
    # 포트 연결
    bus.port_handler.openPort()
    print(f"Successfully opened port: {PORT}")
    
    # 가능한 baudrate들로 스캔
    baudrates = [
        #38400, 57600, 115200, 
        1000000]
    
    for baudrate in baudrates:
        print(f"\nScanning at {baudrate} bps...")
        bus.set_baudrate(baudrate)
        
        # broadcast ping 시도
        try:
            found_motors = bus.broadcast_ping()
            if found_motors:
                print(f"Found motors at {baudrate} bps:")
                for motor_id, model_number in found_motors.items():
                    print(f"  ID: {motor_id}, Model: {model_number}")
        except Exception as e:
            print(f"  Error during scan: {e}")
    
    # 포트 닫기
    bus.port_handler.closePort()
    
except Exception as e:
    print(f"Error: {e}")

print("\nScan complete!")
