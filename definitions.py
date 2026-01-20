import bleak.uuids

hr_svc_uuid_16 = 0x180D
activity_svc_uuid_16 = 0x1859

hr_svc_uuid_128 = bleak.uuids.normalize_uuid_16(activity_svc_uuid_16)
activity_svc_uuid_128 = bleak.uuids.normalize_uuid_16(activity_svc_uuid_16)
# Version 0.7
ecg_voltage_7_uuid_16 = 0x2BDD
imu_meas_7_uuid_16 = 0x2BE2
ecg_interval_7_uuid_16 = 0x2BE3
imu_interval_7_uuid_16 = 0x2BE4

ecg_voltage_7_uuid_128 = bleak.uuids.normalize_uuid_16(ecg_voltage_7_uuid_16)
imu_meas_7_uuid_128 = bleak.uuids.normalize_uuid_16(imu_meas_7_uuid_16)
ecg_interval_7_uuid_128 = bleak.uuids.normalize_uuid_16(ecg_interval_7_uuid_16)
imu_interval_7_uuid_128 = bleak.uuids.normalize_uuid_16(imu_interval_7_uuid_16)

# Version 0.8
ecg_voltage_8_uuid_16 = 0x2BF1
imu_meas_8_uuid_16 = 0x2BF2
config_8_uuid_16 = 0x2BF3
recorded_8_uuid_16 = 0x2BF4

ecg_voltage_8_uuid_128 = bleak.uuids.normalize_uuid_16(ecg_voltage_8_uuid_16)
imu_meas_8_uuid_128 = bleak.uuids.normalize_uuid_16(imu_meas_8_uuid_16)
config_8_uuid_128 = bleak.uuids.normalize_uuid_16(config_8_uuid_16)
recorded_uuid_128 = bleak.uuids.normalize_uuid_16(recorded_8_uuid_16)

ecg_intervals = [2, 4, 8, 10]
imu_intervals = [5, 10, 20, 40]
