import os

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

#다이나믹셀 기본 설정
PROTOCOL_VERSION = 2.0
BAUDRATE = 1000000
DEVICENAME = '/dev/ttyACM1'
#포트 및 패킷 핸들러 초기화
portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(PROTOCOL_VERSION)

try:
    # 포트 열기
    if not portHandler.openPort():
        print("Failed to open the port")
        sys.exit(1)# 시스템 종료, 1은 오류발생을 이미
    print("Succeeded to open the port")

    # 보드레이트 설정
    if not portHandler.setBaudRate(BAUDRATE):
        print("Failed to change the baudrate")
        sys.exit(1)
    print("Succeeded to change the baudrate")

    # 연결된 다이나믹셀 확인
    dxl_data_list, dxl_comm_result = packetHandler.broadcastPing(portHandler)
    if dxl_comm_result != COMM_SUCCESS:
        print(f"Communication Error: {packetHandler.getTxRxResult(dxl_comm_result)}")
        sys.exit(1)

    # 검색된 다이나믹셀 출력
    print("Detected Dynamixel:")
    for dxl_id, data in dxl_data_list.items():
        model, firmware = data
        print(f" [ID: {dxl_id:03d}] [Model: {model}] [Firmware: {firmware}]")

except Exception as e:
    print(f"Error: {e}")

finally:
    # 포트 닫기 (예외 발생 여부와 상관없이 실행)
    portHandler.closePort()
    print("Port closed")