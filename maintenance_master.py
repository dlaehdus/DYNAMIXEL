from dynamixel_sdk import PortHandler, PacketHandler

# 연결 포트
MASTER_PORT_CON = '/dev/ttyACM1'
# 통신 버전
MASTER_PROTOCOL_VERSION = 2.0
# 통신 속도
MASTER_BAUDRATE = 57600
# End Effector 아이디
END_EFFECTOR = 15
# 연결 아이디
MASTER_DXL_IDS = [10, 11, 12, 13, 14, 15]
# 제한 위치 값 
MASTER_POS_LIMITS = [[0, 4095],  # Base Rotation     제한 걸어두면 안됌
                    [0, 4095],  # Shoulder Joint
                    [500, 2000],  # Elbow Joint
                    [1000, 2500],  # Wrist Pitch
                    [0, 4095],  # Wrist Roll        제한 걸어두면 안됌
                    [2000, 3000]]  # End Effector
# End Effector제외
OPERATING_MODE_EXTENDED_POSITION = 4
# End Effector 모드
OPERATING_MODE_CURRENT_BASE_POSITION_CONTROL = 5
# 회전 모드
DRIVE_MODE = 0
# 최대 전압
MAX_VOLTAGE_LIMIT = 160
# 최소 전압
MIN_VOLTAGE_LIMIT = 95
# 전류 제한
CURRENT_LIMIT = 1193
# 속도 제한
VELOCITY_LIMIT = 200
# Control Table 주소
ADDR_OPERATING_MODE      = 11
ADDR_DRIVE_MODE          = 10
ADDR_MAX_VOLTAGE_LIMIT   = 32
ADDR_MIN_VOLTAGE_LIMIT   = 30
ADDR_CURRENT_LIMIT       = 38
ADDR_VELOCITY_LIMIT      = 44
ADDR_MIN_POS_LIMIT       = 52
ADDR_MAX_POS_LIMIT       = 48
ADDR_TORQUE_ENABLE       = 64

portHandler = PortHandler(MASTER_PORT_CON)
packetHandler = PacketHandler(MASTER_PROTOCOL_VERSION)

if not portHandler.openPort():
    raise IOError(f"Failed to open port: {MASTER_PORT_CON}")

if not portHandler.setBaudRate(MASTER_BAUDRATE):
    raise IOError(f"Failed to set baudrate: {MASTER_BAUDRATE}")

for idx, dxl_id in enumerate(MASTER_DXL_IDS):
    packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_TORQUE_ENABLE, 0)
    if dxl_id == END_EFFECTOR:
        mode = OPERATING_MODE_CURRENT_BASE_POSITION_CONTROL
    else:
        mode = OPERATING_MODE_EXTENDED_POSITION
    packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_OPERATING_MODE, mode)
    packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_DRIVE_MODE, DRIVE_MODE)
    packetHandler.write2ByteTxRx(portHandler, dxl_id, ADDR_MAX_VOLTAGE_LIMIT, MAX_VOLTAGE_LIMIT)
    packetHandler.write2ByteTxRx(portHandler, dxl_id, ADDR_MIN_VOLTAGE_LIMIT, MIN_VOLTAGE_LIMIT)
    packetHandler.write2ByteTxRx(portHandler, dxl_id, ADDR_CURRENT_LIMIT, CURRENT_LIMIT)
    packetHandler.write4ByteTxRx(portHandler, dxl_id, ADDR_VELOCITY_LIMIT, VELOCITY_LIMIT)
    min_pos, max_pos = MASTER_POS_LIMITS[idx]
    if min_pos != 0 or max_pos != 0:
        packetHandler.write4ByteTxRx(portHandler, dxl_id, ADDR_MIN_POS_LIMIT, min_pos)
        packetHandler.write4ByteTxRx(portHandler, dxl_id, ADDR_MAX_POS_LIMIT, max_pos)
    packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_TORQUE_ENABLE, 1)
    packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_TORQUE_ENABLE, 0)