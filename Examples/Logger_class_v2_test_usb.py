
import datetime
import time
import csv
import src.LOG34970A_v2_class as logger_class

log = logger_class.usb_interface()
cmd = logger_class.storage()
channels = [101, 116]

config_cmd_list = [
    cmd.reset.str(),
    cmd.route.scan.conf.ch.range(channels[0], channels[1]),
    cmd.sense.voltage.dc.NPLC.conf_20.ch.range(channels[0], channels[1]),
    cmd.sense.voltage.dc.Range.conf_10V.ch.range(channels[0], channels[1]),
]

# apply setting from the list
for item in config_cmd_list:
    log.send(item)
    print(item)
    time.sleep(3)
#
signals_names = [   "CH1",
                    "CH2",
                    "CH3",
                    "CH4",
                    "CH5",
                    "CH6",
                    "CH7",
                    "CH8",
                    "CH9",
                    "CH10",
                    "CH11",
                    "CH12",
                    "CH13",
                    "CH14",
                    "CH15",
                    "CH16",
                 ]

#
#
csv_header = ["Time"] + signals_names
csv_file = open("NGI_voltage_meas.csv", 'w', newline='')
csv_wrt = csv.DictWriter(csv_file, fieldnames=(csv_header), delimiter=',')
csv_wrt.writeheader()
data = {}
for i in range(0, 10000):
    log.send(cmd.init.str())
    time.sleep(15)
    srt = log.query(cmd.fetch.req())
    capture_time = datetime.datetime.now()
    # print(srt)
    array = srt.split(",")
    for z in range(0, len(array)):
        if array[z] != "":
            array[z] = round((float(array[z])),7)
        else:
            array[z] = 0
    for index, item in enumerate(signals_names):
        data[item] = array[index]
    data["Time"] = f"{capture_time}"
    print(data)
    csv_wrt.writerow(data)
    csv_file.flush()


log.close()
csv_file.close()