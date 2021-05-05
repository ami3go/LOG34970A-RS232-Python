
import src.LOG34970A_v2_class as logger_class
import datetime
import time
log = logger_class.com_interface()
cmd = logger_class.storage()
log.init("COM11")

log.send(cmd.configure.voltage.dc.ch_range(0, 301, 320))
time.sleep(3)

log.send(cmd.route.scan.ch_range(0, 301, 320))
time.sleep(3)

log.send(cmd.init.str())
time.sleep(5)


file_log = open("log.txt","w+")

for i in range(0, 10000):
    srt = log.query(cmd.read.req())
    # print(srt)
    array = srt.split(",")
    for z in range(0, len(array)):
        array[z] = round((float(array[z])),4)
    log_string = f'time:{datetime.datetime.now()} {array}\n'
    file_log.writelines(log_string)
    file_log.flush()
    print(log_string)
    time.sleep(2)
log.close()
file_log.close()