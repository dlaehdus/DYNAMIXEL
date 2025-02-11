import os
import time
import select

if os.name == 'nt':
    import msvcrt
    def getch():
        return msvcrt.getch().decode()
else:
    import sys, tty, termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    def getch():
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch    
from dynamixel_sdk import *

# 다이나믹셀 기본 설정
PROTOCOL_VERSION = 2.0
BAUDRATE = 57600
DEVICENAME = '/dev/ttyACM0'
DXL_ID = 1

# 다이나믹셀 주소값
ADDR_TORQUE_ENABLE = 64        # 토크 활성화 주소
ADDR_OPERATING_MODE = 11       # 동작 모드 주소
ADDR_GOAL_VELOCITY = 104       # 목표 속도 주소
ADDR_PRESENT_VELOCITY = 128    # 현재 속도 주소

TORQUE_ENABLE = 1
TORQUE_DISABLE = 0
VELOCITY_MODE = 1 

# 포트 및 패킷 핸들러 초기화
portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(PROTOCOL_VERSION)

# 포트 열기
if not portHandler.openPort():
    print("Failed to open the port")
    sys.exit(1)

# 보드레이트 설정
if not portHandler.setBaudRate(BAUDRATE):
    print("Failed to change the baudrate")
    sys.exit(1)

# 다이나믹셀 속도 모드 설정
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)  # 토크 비활성화
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_OPERATING_MODE, VELOCITY_MODE)  # 속도 모드 설정
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)   # 토크 활성화

try:
    while True:
        print("목표 속도를 설정하세요. (-1023: 최저 속도, 0: 정지, 1023: 최고 속도)")
        # 사용자 입력 (속도 설정)
        goal_velocity = input("목표 속도 입력 (-1023 ~ 1023): ")

        # 사용자가 입력한 값을 정수로 변환하고 유효한지 확인
        try:
            goal_velocity = int(goal_velocity)
            # -1023에서 1023 사이의 값으로 제한
            if goal_velocity < -1023 or goal_velocity > 1023:
                print("속도는 -1023에서 1023 사이여야 합니다.")
                continue
        except ValueError:
            print("유효한 숫자를 입력하세요.")
            continue

        # 목표 속도 설정
        packetHandler.write4ByteTxRx(portHandler, DXL_ID, ADDR_GOAL_VELOCITY, goal_velocity)

        print(f"모터가 {goal_velocity} 속도로 회전 중...")

        # 현재 속도 출력 (3초마다)
        while True:
            time.sleep(3)
            dxl_present_velocity, _, _ = packetHandler.read4ByteTxRx(portHandler, DXL_ID, ADDR_PRESENT_VELOCITY)
            print(f"현재 속도: {dxl_present_velocity}")

            # 새로운 속도 입력 대기
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                break  # 새 속도를 입력하면 벗어남

except KeyboardInterrupt:
    print("\n 프로그램 종료!")

# 모터 정지 후 종료
packetHandler.write4ByteTxRx(portHandler, DXL_ID, ADDR_GOAL_VELOCITY, 0)
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
portHandler.closePort()