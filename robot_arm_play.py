#!/home/limdoyeon/miniconda3/bin/python

import os
import json
import time
import argparse
from dynamixel_sdk import *  # Dynamixel SDK 라이브러리 import (사용자가 설치해야 함)

# Dynamixel 설정 상수
PROTOCOL_VERSION = 2.0
BAUDRATE = 57600  # 기본 baudrate, 필요에 따라 변경
DEVICENAME = '/dev/ttyACM0'  # 포트 이름, Linux 기준 (Windows는 'COM3' 등으로 변경)
ADDR_TORQUE_ENABLE = 64
ADDR_GOAL_POSITION = 116
TORQUE_ENABLE = 1
TORQUE_DISABLE = 0

# 모터 ID 리스트 (6개의 Dynamixel)
DXL_ID_LIST = [10, 11, 12, 13, 14, 15]


def main(file_path='positions_2025-08-15_18-22-54.json'):  # 기본값으로 하드코딩
    # 포트 핸들러 초기화
    portHandler = PortHandler(DEVICENAME)
    packetHandler = PacketHandler(PROTOCOL_VERSION)

    # 포트 열기
    if portHandler.openPort():
        print("포트 열기 성공")
    else:
        print("포트 열기 실패")
        return

    # Baudrate 설정
    if portHandler.setBaudRate(BAUDRATE):
        print("Baudrate 설정 성공")
    else:
        print("Baudrate 설정 실패")
        return

    # 그룹 동기 쓰기 객체 생성 (목표 위치 설정용)
    groupSyncWrite = GroupSyncWrite(portHandler, packetHandler, ADDR_GOAL_POSITION, 4)  # 4 bytes for position

    # 모든 모터에 토크 활성화 (play 모드이므로 토크를 켜야 함)
    for dxl_id in DXL_ID_LIST:
        dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
        if dxl_comm_result != COMM_SUCCESS:
            print(f"ID {dxl_id} 토크 활성화 실패: {packetHandler.getTxRxResult(dxl_comm_result)}")
        elif dxl_error != 0:
            print(f"ID {dxl_id} 토크 활성화 오류: {packetHandler.getRxPacketError(dxl_error)}")
        else:
            print(f"ID {dxl_id} 토크 활성화 성공")

    # 기록된 파일 로드
    if not os.path.exists(file_path):
        print(f"파일이 존재하지 않습니다: {file_path}")
        return

    try:
        with open(file_path, 'r') as f:
            positions = json.load(f)  # [[pos1_id1, pos1_id2, ..., pos1_id6], ...] 형식
    except json.JSONDecodeError as e:
        print(f"JSON 파일 로드 실패: {e}")
        return

    print(f"재생 시작: {len(positions)} 프레임")

    # 각 프레임(위치 세트)을 0.05초 간격으로 재생 (코드상 0.01로 되어 있지만 주석에 맞춤)
    for frame in positions:
        if len(frame) != len(DXL_ID_LIST):
            print("프레임 길이가 모터 수와 맞지 않습니다. 스킵")
            continue

        # 그룹 동기 쓰기를 위한 데이터 준비
        for i, dxl_id in enumerate(DXL_ID_LIST):
            pos = frame[i]
            param_goal_position = [DXL_LOBYTE(DXL_LOWORD(pos)), DXL_HIBYTE(DXL_LOWORD(pos)), DXL_LOBYTE(DXL_HIWORD(pos)), DXL_HIBYTE(DXL_HIWORD(pos))]
            addparam_result = groupSyncWrite.addParam(dxl_id, param_goal_position)
            if not addparam_result:
                print(f"ID {dxl_id} 그룹 동기 쓰기 파라미터 추가 실패")

        # 동기 쓰기 전송
        dxl_comm_result = groupSyncWrite.txPacket()
        if dxl_comm_result != COMM_SUCCESS:
            print(f"그룹 동기 쓰기 실패: {packetHandler.getTxRxResult(dxl_comm_result)}")

        # 파라미터 클리어
        groupSyncWrite.clearParam()

        # 0.05초 대기 (주석에 맞춰 조정, 필요 시 변경)
        time.sleep(0.01)

    print("재생 완료")

    # 모든 모터에 토크 비활성화 (재생 후 선택적으로)
    for dxl_id in DXL_ID_LIST:
        packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)

    # 포트 닫기
    portHandler.closePort()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Robot Arm Play: 기록된 파일을 재생하여 로봇 팔 동작 재현")
    parser.add_argument('file_path', nargs='?', default='positions_2025-08-15_18-13-06.json', type=str, help="재생할 기록 파일 경로 (JSON 형식, 기본값: positions_2025-08-15_18-13-06.json)")
    args = parser.parse_args()
    main(args.file_path)
