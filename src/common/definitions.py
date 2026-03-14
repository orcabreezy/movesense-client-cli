import bleak.uuids

HR_SVC_UUID_16 = 0x180D
ACTIVITY_SVC_UUID_16 = 0x1859

HR_SVC_UUID_128 = bleak.uuids.normalize_uuid_16(HR_SVC_UUID_16)
ACTIVITY_SVC_UUID_128 = bleak.uuids.normalize_uuid_16(ACTIVITY_SVC_UUID_16)


class MovesenseV7:
    ECG_VOLTAGE_UUID_16 = 0x2BDD
    IMU_MEAS_UUID_16 = 0x2BE2
    ECG_INTERVAL_UUID_16 = 0x2BE3
    IMU_INTERVAL_UUID_16 = 0x2BE4

    ECG_VOLTAGE_UUID_128 = bleak.uuids.normalize_uuid_16(ECG_VOLTAGE_UUID_16)
    IMU_MEAS_UUID_128 = bleak.uuids.normalize_uuid_16(IMU_MEAS_UUID_16)
    ECG_INTERVAL_UUID_128 = bleak.uuids.normalize_uuid_16(ECG_INTERVAL_UUID_16)
    IMU_INTERVAL_UUID_128 = bleak.uuids.normalize_uuid_16(IMU_INTERVAL_UUID_16)


class MovesenseV8:
    ECG_VOLTAGE_UUID_16 = 0x2BF1
    IMU_MEAS_UUID_16 = 0x2BF2
    CONFIG_UUID_16 = 0x2BF3
    RECORDED_UUID_16 = 0x2BF4

    ECG_VOLTAGE_UUID_128 = bleak.uuids.normalize_uuid_16(ECG_VOLTAGE_UUID_16)
    IMU_MEAS_UUID_128 = bleak.uuids.normalize_uuid_16(IMU_MEAS_UUID_16)
    CONFIG_UUID_128 = bleak.uuids.normalize_uuid_16(CONFIG_UUID_16)
    RECORDED_UUID_128 = bleak.uuids.normalize_uuid_16(RECORDED_UUID_16)


ECG_INTERVALS = [2, 4, 8, 10]
IMU_INTERVALS = [5, 10, 20, 40]
