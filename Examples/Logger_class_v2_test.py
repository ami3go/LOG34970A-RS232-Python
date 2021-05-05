
import src.LOG34970A_v2_class as logger_class
import datetime
import time
log = logger_class.com_interface()
cmd = logger_class.storage()
log.init("COM11")
txt = f"{cmd.configure.voltage.dc.ch_range(301,320)}"
cmd.sense.voltage.ac.Range
cmd.configure.voltage.ac.Range

print(txt)
log.send(txt)
time.sleep(3)

txt ="ROUT:SCAN (@301,302,303,304,305,306,307,308,309,310,311,312,313,314,315,316,317,318,319,320)"
log.send(txt)

time.sleep(3)
print(log.query(cmd.configure.combine()))

txt ="INIT"
log.send(txt)
time.sleep(5)

txt="READ? (@301,302,303,304,305,306,307,308,309,310,311,312,313,314,315,316,317,318,319,320)"
txt="READ"
file_log = open("log.txt","w+")

for i in range(0, 10000):
    srt = log.query(txt)
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