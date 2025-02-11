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
DXL_ID = 0

# 다이나믹셀 주소값
ADDR_TORQUE_ENABLE = 64        # 토크 활성화 주소
ADDR_OPERATING_MODE = 11       # 동작 모드 주소
ADDR_GOAL_CURRENT = 102        # 목표 전류 주소
ADDR_PRESENT_POSITION = 132    # 현재 위치 주소

TORQUE_ENABLE = 1
TORQUE_DISABLE = 0
CURRENT_MODE = 5              # 전류 기반 위치 모드 설정

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

# 다이나믹셀 전류 모드 설정
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)  # 토크 비활성화
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_OPERATING_MODE, CURRENT_MODE)  # 전류 모드 설정
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)   # 토크 활성화

# 0도를 유지하는 전류 값 계산
def calculate_current_for_angle(angle):
    # 0도에 대한 전류 값을 설정
    # 예를 들어, 0도에 대해 전류 10을 설정
    if angle == 0:
        return 5  # 전류 10을 사용하여 0도를 유지

    return 0  # 다른 각도에서는 전류 0으로 설정

# 현재 각도를 확인하는 함수
def get_current_angle():
    dxl_present_position, _, _ = packetHandler.read2ByteTxRx(portHandler, DXL_ID, ADDR_PRESENT_POSITION)
    # 0~4095 값을 0~90도로 변환
    current_angle = (dxl_present_position / 4095.0) * 90
    return current_angle

try:
    while True:
        # 목표 전류 값 계산 (0도에서 전류 10으로 고정)
        goal_current = calculate_current_for_angle(0)

        # 목표 전류 설정
        packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_GOAL_CURRENT, goal_current)

        # 3초마다 현재 각도 출력
        time.sleep(3)
        
        # 현재 각도 읽기
        current_angle = get_current_angle()

        print(f"현재 각도: {current_angle:.2f}도")

except KeyboardInterrupt:
    print("\n 프로그램 종료!")

# 모터 정지 후 종료
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
portHandler.closePort()