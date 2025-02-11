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
ADDR_GOAL_POSITION = 116        # 목표 위치 주소
ADDR_PRESENT_POSITION = 132     # 현재 위치 주소

TORQUE_ENABLE = 1
TORQUE_DISABLE = 0
POSITION_MODE = 3               # 위치 모드

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

# 다이나믹셀 위치 모드 설정
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)  # 토크 비활성화
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_OPERATING_MODE, POSITION_MODE)  # 위치 모드 설정
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)   # 토크 활성화

try:
    while True:
        print("목표 각도를 설정하세요. (0 ~ 360 범위)")
        # 사용자 입력 (각도 설정)
        goal_angle = input("목표 각도 입력 (0 ~ 360): ")

        # 사용자가 입력한 값을 정수로 변환하고 유효한지 확인
        try:
            goal_angle = float(goal_angle)
            # 0에서 360 사이의 값으로 제한
            if goal_angle < 0 or goal_angle > 360:
                print("각도는 0에서 360 사이여야 합니다.")
                continue
        except ValueError:
            print("유효한 숫자를 입력하세요.")
            continue

        # 각도를 4095로 매핑 (0도 -> 0, 360도 -> 4095)
        goal_position = int((goal_angle / 360.0) * 4095)

        # 목표 위치 설정
        packetHandler.write4ByteTxRx(portHandler, DXL_ID, ADDR_GOAL_POSITION, goal_position)
        print(f"모터가 목표 위치 {goal_position} (각도 {goal_angle}°)으로 이동 중...")

        # 3초마다 현재 위치 출력
        while True:
            time.sleep(3)
            dxl_present_position, _, _ = packetHandler.read4ByteTxRx(portHandler, DXL_ID, ADDR_PRESENT_POSITION)
            print(f"현재 위치: {dxl_present_position} (각도: {dxl_present_position * 360.0 / 4095:.2f}°)")

            # 새로운 위치 입력 대기
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                break  # 새 속도를 입력하면 벗어남
        
except KeyboardInterrupt:
    print("\n 프로그램 종료!")

# 모터 정지 후 종료
packetHandler.write4ByteTxRx(portHandler, DXL_ID, ADDR_GOAL_POSITION, 0)  # 위치 0으로 설정하여 정지
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
portHandler.closePort()