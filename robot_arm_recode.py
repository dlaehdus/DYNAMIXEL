import os
import json
import time
from pynput import keyboard  # root 권한 없이 키 입력 감지 가능
from dynamixel_sdk import *  # Dynamixel SDK 라이브러리 import

# Dynamixel 설정 상수
PROTOCOL_VERSION = 2.0
BAUDRATE = 57600
DEVICENAME = '/dev/ttyACM0'
ADDR_TORQUE_ENABLE = 64
ADDR_PRESENT_POSITION = 132
TORQUE_ENABLE = 1
TORQUE_DISABLE = 0

# 모터 ID 리스트
DXL_ID_LIST = [10, 11, 12, 13, 14, 15]

# 전역 상태 변수
recording = False
positions = []
start_time = 0
stop_flag = False  # 's' 눌렀을 때 종료 신호ㅎㄴ

def on_press(key):
    global recording, start_time, stop_flag
    try:
        if key.char == 'g' and not recording:
            print("기록 시작")
            recording = True
            start_time = time.time()
        elif key.char == 's' and recording:
            print("기록 중지")
            recording = False
            stop_flag = True
            return False  # 리스너 종료
    except AttributeError:
        pass  # 특수키는 무시

def main():
    global recording, positions, start_time, stop_flag

    # 포트 핸들러 초기화
    portHandler = PortHandler(DEVICENAME)
    packetHandler = PacketHandler(PROTOCOL_VERSION)

    if portHandler.openPort():
        print("포트 열기 성공")
    else:
        print("포트 열기 실패")
        return

    if portHandler.setBaudRate(BAUDRATE):
        print("Baudrate 설정 성공")
    else:
        print("Baudrate 설정 실패")
        return

    # 그룹 동기 읽기 객체
    groupSyncRead = GroupSyncRead(portHandler, packetHandler, ADDR_PRESENT_POSITION, 4)

    # 모든 모터 토크 비활성화
    for dxl_id in DXL_ID_LIST:
        dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
        if dxl_comm_result != COMM_SUCCESS:
            print(f"ID {dxl_id} 토크 비활성화 실패: {packetHandler.getTxRxResult(dxl_comm_result)}")
        elif dxl_error != 0:
            print(f"ID {dxl_id} 토크 비활성화 오류: {packetHandler.getRxPacketError(dxl_error)}")
        else:
            print(f"ID {dxl_id} 토크 비활성화 성공")

    # 그룹 동기 읽기 파라미터 추가
    for dxl_id in DXL_ID_LIST:
        if not groupSyncRead.addParam(dxl_id):
            print(f"ID {dxl_id} 그룹 동기 읽기 파라미터 추가 실패")
            return

    print("키 입력 대기: 'g'로 기록 시작, 's'로 기록 중지")

    # 키 입력 리스너 시작 (비동기)
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    # 메인 루프
    while not stop_flag:
        if recording:
            current_time = time.time()
            if current_time - start_time >= 0.01:
                dxl_comm_result = groupSyncRead.txRxPacket()
                if dxl_comm_result != COMM_SUCCESS:
                    print(f"그룹 동기 읽기 실패: {packetHandler.getTxRxResult(dxl_comm_result)}")
                else:
                    frame = [groupSyncRead.getData(dxl_id, ADDR_PRESENT_POSITION, 4) for dxl_id in DXL_ID_LIST]
                    positions.append(frame)
                    print(f"기록: {frame}")
                start_time = current_time
        time.sleep(0.01)

    # 기록 저장
    if positions:
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"positions_{timestamp}.json"
        file_path = os.path.join(os.getcwd(), file_name)
        with open(file_path, 'w') as f:
            json.dump(positions, f)
        print(f"기록 저장: {file_path}")
    else:
        print("기록된 데이터 없음")

    portHandler.closePort()

if __name__ == "__main__":
    main()
