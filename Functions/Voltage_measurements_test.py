import time

import Functions.Voltage_measurements as dmm

dmm.init_logger()
dmm.trigger()
for i in range(5):
    dmm.trigger()
    time.sleep(1)
    print(dmm.read_voltage())
