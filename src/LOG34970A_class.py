#import pyvisa # PyVisa info @ http://PyVisa.readthedocs.io/en/stable/
import serial
import serial.tools.list_ports


def range_check(val, min, max, val_name):
    if val > max:
        print(f"Wrong {val_name}: {val}. Max output should be less then {max} V")
        val = max
    if val < min:
        print(f"Wrong {val_name}: {val}. Should be >= {min}")
        val = min
    return val



# ## Number of Points to request
# USER_REQUESTED_POINTS = 1000
#     ## None of these scopes offer more than 8,000,000 points
#     ## Setting this to 8000000 or more will ensure that the maximum number of available points is retrieved, though often less will come back.
#     ## Average and High Resolution acquisition types have shallow memory depth, and thus acquiring waveforms in Normal acq. type and post processing for High Res. or repeated acqs. for Average is suggested if more points are desired.
#     ## Asking for zero (0) points, a negative number of points, fewer than 100 points, or a non-integer number of points (100.1 -> error, but 100. or 100.0 is ok) will result in an error, specifically -222,"Data out of range"
#
# ## Initialization constants
# INSTRUMENT_VISA_ADDRESS = 'USB0::0x0957::0x0A07::MY48001027::0::INSTR' # Get this from Keysight IO Libraries Connection Expert
#     ## Note: sockets are not supported in this revision of the script (though it is possible), and PyVisa 1.8 does not support HiSlip, nor do these scopes.
#     ## Note: USB transfers are generally fastest.
#     ## Video: Connecting to Instruments Over LAN, USB, and GPIB in Keysight Connection Expert: https://youtu.be/sZz8bNHX5u4

GLOBAL_TOUT =  10 # IO time out in milliseconds

class LOG_34970A:

    def __init__(self):
        self.ser = None

    def init(self, com_port, baudrate_var=115200):
        com_port_list = [comport.device for comport in serial.tools.list_ports.comports()]
        if com_port not in com_port_list:
            print("COM port is not found")
            print("Please ensure that USB is connected")
            print(f"Please check COM port Number. Currently it is {com_port} ")
            print(f'Founded COM ports:{com_port_list}')
            return False
        else:
            self.ser = serial.Serial(
                port=com_port,
                baudrate=baudrate_var,
                timeout=0.1
            )
            if not self.ser.isOpen():
                self.ser.open()
            txt = '*IDN?\r\n'

            read_back = self.ser.write(txt.encode())
            read_back = self.ser.readline().decode()
            print(f"Connected to: {read_back}")

            # tmp = self.ser.isOpen()
            # print("is open:", tmp)
            # return_value = self.get_status()
            return True

    def send(self, cmd_srt):
        txt = f'{cmd_srt}\r\n'
        self.ser.write(txt.encode())

    def query(self, cmd_srt):
        txt = f'{cmd_srt}?'
        self.send(txt)
        return self.ser.readline().decode()

    def close(self):
        self.ser.close()
        self.ser = None


    # configuring reading time
    # on_off = 0 - off
    # on_off = 1 - on
    # status -  check status
    def conf_reading_time(self, on_off, check_val=1):
        cmd_list = ["OFF", "ON", "Unknown"]
        on_off = range_check(on_off,0,1,"ON/OFF state")
        check_val = range_check(check_val, 0, 1, "check_back bool val")
        txt = f'FORM:READ:TIME {cmd_list[on_off]}'
        self.send(txt)
        if check_val == 1:
            txt = 'FORM:READ:TIME?'
            read_back = int(self.query(txt))
            print(f"FORM:READ:TIME {cmd_list[read_back]}")
            return read_back

    def conf_sys_date(self, yy=2021, mm=4, dd=23, check_val=1):
        yy = range_check(yy,2021,2200,"Year")
        mm = range_check(mm, 1, 12, "Month")
        dd = range_check(dd, 1, 31, "Day")
        check_val = range_check(check_val, 0, 1, "check_back bool val")
        txt = f'SYST:DATE {yy},{str(mm).zfill(2)},{dd}\r\n'
        self.ser.write(txt.encode())

        if check_val == 1:
            txt = f'SYST:DATE?\r\n'
            self.ser.write(txt.encode())
            read_back = self.ser.readline().decode()
            print(f"SYST:DATE? {read_back}")
            return read_back

    def conf_sys_time(self, hh=12, mm=20, ss=23, check_val=1):
        hh = range_check(hh, 0, 23, "hours")
        mm = range_check(mm, 0, 59, "minutes")
        ss = range_check(ss, 0, 59, "seconds")
        ss = round(ss,3)
        check_val = range_check(check_val, 0, 1, "check_back bool val")
        txt = f'SYST:TIME {str(hh).zfill(2)},{str(mm).zfill(2)},{str(ss).zfill(6)}\r\n'
        self.ser.write(txt.encode())

        if check_val == 1:
            txt = f'SYST:TIME?\r\n'
            self.ser.write(txt.encode())
            read_back = self.ser.readline().decode()
            print(f"SYST:TIME? {read_back}")
            return read_back

    def get_sys_time_scan(self, show_val=0):
        show_val = range_check(show_val, 0, 1, "show bool val")
        txt = f'SYST:TIME:SCAN?\r\n'
        self.ser.write(txt.encode())
        read_back = self.ser.readline().decode()
        if show_val ==1:
            print(f"{read_back}")
        return read_back

    def read(self):
        txt = f'READ?\r\n'
        print(f"CMD:{txt} need to be checked")
        self.ser.write(txt.encode())
        read_back = self.ser.readline().decode()
        print(f"SYST:TIME? {read_back}")
        return read_back

    def read(self):
        txt = f'READ?\r\n'
        print(f"CMD:{txt} need to be checked")
        self.ser.write(txt.encode())
        read_back = self.ser.readline().decode()
        print(f"SYST:TIME? {read_back}")
        return read_back

    def configure(self):
        txt = f'READ?\r\n'
        print(f"CMD:{txt} need to be checked")
        self.ser.write(txt.encode())
        read_back = self.ser.readline().decode()
        print(f"SYST:TIME? {read_back}")
        return read_back

if __name__ == "__main__":
    pass