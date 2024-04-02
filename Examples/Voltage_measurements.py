
import datetime
import time
import src.LOG34970A_v2_class as logger_class

global log, cmd, channels
log = logger_class.usb_interface()
cmd = logger_class.storage()
channels = [101, 116]


def init_logger():
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
def read_volatge():
    log.send(cmd.init.str())
    time.sleep(15)
    srt = log.query(cmd.fetch.req())
    meas_array = srt.split(",")
    for z in range(0, len(meas_array)):
        if meas_array[z] != "":
            meas_array[z] = round((float(meas_array[z])), 7)
        else:
            meas_array[z] = 0
    return meas_array
