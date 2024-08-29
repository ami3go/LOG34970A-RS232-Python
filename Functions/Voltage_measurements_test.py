import Functions.Voltage_measurements as dmm

dmm.init_logger()

for i in range(5):
    print(dmm.read_voltage())
