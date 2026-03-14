import bleak.uuids
from src.common.definitions import HR_SVC_UUID_16, ACTIVITY_SVC_UUID_16, HR_SVC_UUID_128, ACTIVITY_SVC_UUID_128, MovesenseV7, MovesenseV8, ECG_INTERVALS, IMU_INTERVALS

def test_hr_svc_uuid_normalization():
    assert HR_SVC_UUID_128 == bleak.uuids.normalize_uuid_16(HR_SVC_UUID_16)

def test_activity_svc_uuid_normalization():
    assert ACTIVITY_SVC_UUID_128 == bleak.uuids.normalize_uuid_16(ACTIVITY_SVC_UUID_16)

def test_movesense_v7_uuids_normalization():
    assert MovesenseV7.ECG_VOLTAGE_UUID_128 == bleak.uuids.normalize_uuid_16(MovesenseV7.ECG_VOLTAGE_UUID_16)
    assert MovesenseV7.IMU_MEAS_UUID_128 == bleak.uuids.normalize_uuid_16(MovesenseV7.IMU_MEAS_UUID_16)
    assert MovesenseV7.ECG_INTERVAL_UUID_128 == bleak.uuids.normalize_uuid_16(MovesenseV7.ECG_INTERVAL_UUID_16)
    assert MovesenseV7.IMU_INTERVAL_UUID_128 == bleak.uuids.normalize_uuid_16(MovesenseV7.IMU_INTERVAL_UUID_16)

def test_movesense_v8_uuids_normalization():
    assert MovesenseV8.ECG_VOLTAGE_UUID_128 == bleak.uuids.normalize_uuid_16(MovesenseV8.ECG_VOLTAGE_UUID_16)
    assert MovesenseV8.IMU_MEAS_UUID_128 == bleak.uuids.normalize_uuid_16(MovesenseV8.IMU_MEAS_UUID_16)
    assert MovesenseV8.CONFIG_UUID_128 == bleak.uuids.normalize_uuid_16(MovesenseV8.CONFIG_UUID_16)
    assert MovesenseV8.RECORDED_UUID_128 == bleak.uuids.normalize_uuid_16(MovesenseV8.RECORDED_UUID_16)

def test_ecg_intervals_content():
    assert ECG_INTERVALS == [2, 4, 8, 10]

def test_imu_intervals_content():
    assert IMU_INTERVALS == [5, 10, 20, 40]
