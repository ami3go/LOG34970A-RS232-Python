
import src.LOG34970A_class as logdev
import time
log = logdev.LOG_34970A()

log.init("COM9")
log.conf_reading_time(1,1)
log.conf_system_date(2021, 4,23,1)
log.conf_system_time(19,2,1.123)

log.close()