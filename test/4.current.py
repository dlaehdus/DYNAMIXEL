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
ADDR_PRESENT_CURRENT = 126     # 현재 전류 주소

TORQUE_ENABLE = 1
TORQUE_DISABLE = 0
CURRENT_MODE = 0               # 전류 모드 설정

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

try:
    while True:
        print("목표 전류를 설정하세요. (-1193 ~ 1193 범위)")

        # 사용자 입력 (전류 설정)
        goal_current = input("목표 전류 입력 (-1193 ~ 1193): ")

        # 사용자가 입력한 값을 정수로 변환하고 유효한지 확인
        try:
            goal_current = int(goal_current)
            # -1193에서 1193 사이의 값으로 제한
            if goal_current < -1193 or goal_current > 1193:
                print("전류는 -1193에서 1193 사이여야 합니다.")
                continue
        except ValueError:
            print("유효한 숫자를 입력하세요.")
            continue

        # 전류를 -1193 ~ 1193 범위로 매핑하여 -32767 ~ 32767로 변환
        goal_current_value = int((goal_current / 1193.0) * 32767)  # 32767은 INT16 최대값

        # 목표 전류 설정
        packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_GOAL_CURRENT, goal_current_value)
        print(f"모터가 목표 전류 {goal_current_value}로 동작 중...")

        # 3초마다 현재 전류 출력
        while True:
            time.sleep(3)
            dxl_present_current, _, _ = packetHandler.read2ByteTxRx(portHandler, DXL_ID, ADDR_PRESENT_CURRENT)
            present_current = (dxl_present_current / 32767.0) * 1193  # -1193 ~ 1193 범위로 변환
            print(f"현재 전류: {present_current:.2f}A")

            # 새로운 전류 입력 대기
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                break  # 새 전류 값을 입력하면 벗어남

except KeyboardInterrupt:
    print("\n 프로그램 종료!")

# 모터 정지 후 종료
packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_GOAL_CURRENT, 0)  # 전류 0으로 설정하여 정지
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
portHandler.closePort()
