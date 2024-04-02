
import datetime
import time

import src.LOG34970A_v2_class as logger_class

log = logger_class.com_interface()
cmd = logger_class.storage()
log.init("COM11")

log.send(cmd.configure.voltage.dc.ch_range(0, 301, 316))
time.sleep(3)

log.send(cmd.route.scan.ch_range(0, 301, 316))
time.sleep(3)

signals_names = ["Time,",
                 "1 Sensor 1,",
                 "2 Sensor 2,",
                 "3 Sensor 3,",
                 "4 Sensor 4,",
                 "5 Sensor 5,",
                 "6 Sensor 6,",
                 "7 Sensor 7,",
                 "8 MDI_P_5V_ASIC_PG,",
                 "9 RELAY_HS_FAULT,",
                 "10 MAI_RELAY_DRV_2_DIAG,",
                 "11 MDI_P_7V_ASIC_PG,",
                 "12 RESET_N,",
                 "13 ASIC_A_INT,",
                 "14 ASIC_B_INT,",
                 "15 ASIC_C_INT,",
                 "16 MDI_P_7V_ASIC_PG,",
                 ]
log.send(cmd.init.str())
time.sleep(5)


file_log = open("log.txt","w+")
file_log.writelines(signals_names)
print(signals_names)
for i in range(0, 10000):
    srt = log.query(cmd.read.req())
    # print(srt)
    array = srt.split(",")
    for z in range(0, len(array)):
        if array[z] != "":
            array[z] = round((float(array[z])),4)
        else:
            array[z] = 0
    log_string = f'time:{datetime.datetime.now()} {array}\n'
    file_log.writelines(log_string)
    file_log.flush()
    print(log_string)
    time.sleep(3)
log.close()
file_log.close()