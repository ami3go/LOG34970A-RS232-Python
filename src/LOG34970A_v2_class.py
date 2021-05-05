#import pyvisa # PyVisa info @ http://PyVisa.readthedocs.io/en/stable/
import serial.tools.list_ports
import serial
import time

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

# GLOBAL_TOUT =  10 # IO time out in milliseconds
#
# class LOG_34970A:
#
#     def __init__(self):
#         self.ser = None
#
#     def init(self, com_port, baudrate_var=115200):
#         com_port_list = [comport.device for comport in serial.tools.list_ports.comports()]
#         if com_port not in com_port_list:
#             print("COM port is not found")
#             print("Please ensure that USB is connected")
#             print(f"Please check COM port Number. Currently it is {com_port} ")
#             print(f'Founded COM ports:{com_port_list}')
#             return False
#         else:
#             self.ser = serial.Serial(
#                 port=com_port,
#                 baudrate=baudrate_var,
#                 timeout=0.1
#             )
#             if not self.ser.isOpen():
#                 self.ser.open()
#             txt = '*IDN'
#             read_back = self.query(txt)
#             print(f"Connected to: {read_back}")
#
#             # tmp = self.ser.isOpen()
#             # print("is open:", tmp)
#             # return_value = self.get_status()
#             return True
#
#     def send(self, cmd_srt):
#         txt = f'{cmd_srt}\r\n'
#         self.ser.write(txt.encode())
#
#     def query(self, cmd_srt):
#         txt = f'{cmd_srt}?'
#         self.send(txt)
#         return self.ser.readline().decode()
#
#     def close(self):
#         self.ser.close()
#         self.ser = None
#
#
#     # configuring reading time
#     # on_off = 0 - off
#     # on_off = 1 - on
#     # status -  check status
#     def conf_reading_time(self, on_off, check_val=1):
#         cmd_list = ["OFF", "ON", "Unknown"]
#         on_off = range_check(on_off,0,1,"ON/OFF state")
#         check_val = range_check(check_val, 0, 1, "check_back bool val")
#         txt = f'FORM:READ:TIME {cmd_list[on_off]}'
#         self.send(txt)
#         if check_val == 1:
#             txt = 'FORM:READ:TIME?'
#             read_back = int(self.query(txt))
#             print(f"FORM:READ:TIME {cmd_list[read_back]}")
#             return read_back
#
#     def conf_sys_date(self, yy=2021, mm=4, dd=23, check_val=1):
#         yy = range_check(yy,2021,2200,"Year")
#         mm = range_check(mm, 1, 12, "Month")
#         dd = range_check(dd, 1, 31, "Day")
#         check_val = range_check(check_val, 0, 1, "check_back bool val")
#         txt = f'SYST:DATE {yy},{str(mm).zfill(2)},{dd}\r\n'
#         self.ser.write(txt.encode())
#
#         if check_val == 1:
#             txt = f'SYST:DATE?\r\n'
#             self.ser.write(txt.encode())
#             read_back = self.ser.readline().decode()
#             print(f"SYST:DATE? {read_back}")
#             return read_back
#
#     def conf_sys_time(self, hh=12, mm=20, ss=23, check_val=1):
#         hh = range_check(hh, 0, 23, "hours")
#         mm = range_check(mm, 0, 59, "minutes")
#         ss = range_check(ss, 0, 59, "seconds")
#         ss = round(ss,3)
#         check_val = range_check(check_val, 0, 1, "check_back bool val")
#         txt = f'SYST:TIME {str(hh).zfill(2)},{str(mm).zfill(2)},{str(ss).zfill(6)}\r\n'
#         self.ser.write(txt.encode())
#
#         if check_val == 1:
#             txt = f'SYST:TIME?\r\n'
#             self.ser.write(txt.encode())
#             read_back = self.ser.readline().decode()
#             print(f"SYST:TIME? {read_back}")
#             return read_back
#
#     def get_sys_time_scan(self, show_val=0):
#         show_val = range_check(show_val, 0, 1, "show bool val")
#         txt = f'SYST:TIME:SCAN?\r\n'
#         self.ser.write(txt.encode())
#         read_back = self.ser.readline().decode()
#         if show_val ==1:
#             print(f"{read_back}")
#         return read_back
#
#     def read(self):
#         txt = f'READ?\r\n'
#         print(f"CMD:{txt} need to be checked")
#         self.ser.write(txt.encode())
#         read_back = self.ser.readline().decode()
#         print(f"SYST:TIME? {read_back}")
#         return read_back
#
#     def read(self):
#         txt = f'READ?\r\n'
#         print(f"CMD:{txt} need to be checked")
#         self.ser.write(txt.encode())
#         read_back = self.ser.readline().decode()
#         print(f"SYST:TIME? {read_back}")
#         return read_back
#
#     def configure(self):
#         txt = f'READ?\r\n'
#         print(f"CMD:{txt} need to be checked")
#         self.ser.write(txt.encode())
#         read_back = self.ser.readline().decode()
#         print(f"SYST:TIME? {read_back}")
#         return read_back


class com_interface():
    def __init__(self):
        # Commands Subsystem
        # this is the list of Subsystem commands
        # super(communicator, self).__init__(port="COM10",baudrate=115200, timeout=0.1)
        print("communicator init")
        self.cmd = None
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

            txt = '*IDN?'

            read_back = self.query(txt)
            print(f"Connected to: {read_back}")
            return True

    def send(self, txt):
        # will put sending command here
        txt = f'{txt}\r\n'
        #print(f'Sending: {txt}')
        self.ser.write(txt.encode())
    # an old variant of query
    # def query(self, cmd_srt):
    #     txt = f'{cmd_srt}?\r\n'
    #     self.ser.reset_input_buffer()
    #     self.ser.write(txt.encode())
    #     #print(f'Query: {txt}')
    #     return_val = self.ser.readline().decode()
    #     return return_val

    def query(self, cmd_srt):
        txt = f'{cmd_srt}\r\n'
        self.ser.reset_input_buffer()
        self.ser.write(txt.encode())
        # print(f'Query: {txt}')
        return_val = self.ser.readline().decode()
        return return_val


    def close(self):
        self.ser.close()
        self.ser = None


class str_return:
    def __init__(self):
        self.cmd = None


    def str(self):
        # will put sending command here
        return self.cmd

    def req(self):
        return self.cmd + "?"


    def ch_list(self,is_req, *argv):
        req_txt = ""
        if is_req == 1:
            req_txt = "?"
        txt = ""
        for arg in argv:
            txt = f'{txt}{arg},'
        txt = txt[:-1]
        txt = f'{self.cmd}{req_txt} (@{txt})'
        return txt

    def ch_range(self,is_req, min, max, channels_num=20):
        channels_34901A = 20  # 34901A 20 Channel Multiplexer (2/4-wire) Module
        channels_34902A = 16  # 34902A 16 Channel Multiplexer (2/4-wire) Module
        channels_34902A = 40  # 34908A 40 Channel Single-Ended Multiplexer Module
        req_txt = ""
        if is_req == 1:
            req_txt = "?"
        channels = channels_num
        slot_id = int(min/100)
        slot_id = range_check(slot_id,1,3,"slot ID")
        min = range_check(min, (slot_id*100+1), (slot_id*100+channels), " channels number")
        max = range_check(max, (slot_id*100+1), (slot_id*100+channels), " channels number")
        txt = f"{min},"
        l = [f"{min},"]
        for z in range(0, (max - min)):
            l.append(f'{min + z + 1},')
        txt = "".join(l)
        txt = txt[:-1]
        txt = f"{self.cmd}{req_txt} (@{txt})"
        return txt


class req_only:
    def __init__(self):
        self.cmd = None

    def req(self):
        return self.cmd + "?"

class ch_single:
    def __init__(self):
        self.cmd = None

    def ch_single(self, ch_num, max_ch_number=20):
        channels_34901A = 20  # 34901A 20 Channel Multiplexer (2/4-wire) Module
        channels_34902A = 16  # 34902A 16 Channel Multiplexer (2/4-wire) Module
        channels_34902A = 40  # 34908A 40 Channel Single-Ended Multiplexer Module
        channels = max_ch_number
        slot_id = int(ch_num / 100)
        slot_id = range_check(slot_id, 1, 3, "slot ID")
        ch_num = range_check(ch_num, (slot_id * 100 + 1), (slot_id * 100 + channels), " channels number")
        txt = f'{self.cmd} (@{ch_num})'
        return txt



class select_channel:
    def __init__(self, cmd):
        self.cmd = None

    def ch_list(self, *argv):
        txt = ""
        for arg in argv:
            txt = f'{txt}{arg},'
        txt = txt[:-1]
        txt = f'{self.cmd} (@{txt})'
        return txt

    def ch_range(self, min, max, channels_num=20):
        channels_34901A = 20  # 34901A 20 Channel Multiplexer (2/4-wire) Module
        channels_34902A = 16  # 34902A 16 Channel Multiplexer (2/4-wire) Module
        channels_34902A = 40  # 34908A 40 Channel Single-Ended Multiplexer Module
        channels = channels_num
        slot_id = int(min/100)
        slot_id = range_check(slot_id,1,3,"slot ID")
        min = range_check(min, (slot_id*100+1), (slot_id*100+channels), " channels number")
        max = range_check(max, (slot_id*100+1), (slot_id*100+channels), " channels number")
        txt = f"{min},"
        l = [f"{min},"]
        for z in range(0, (max - min)):
            l.append(f'{min + z + 1},')
        txt = "".join(l)
        txt = txt[:-1]
        txt = f"{self.cmd} (@{txt})"
        return txt


class make_request(select_channel):
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + "?"



class results_processor:
    def parse_output(self, output):
        print('RESULT')


class storage():
    def __init__(self):
        self.cmd = None
        self.prefix = None
        # super(communicator, self).__init__()
        # super(storage,self).__init__()
        # communicator.init(self, "COM10")
        # this is the list of Subsystem commands
        # self.calculate = calculate()
        # self.calibration = calibration()
        self.configure = configure()
        # self.data = data()
        # self.diagnostic = diagnostic()
        # self.display = display()
        # self.fformat = fformat()
        # self.ieee-488.2 = ieee-488.2()
        # self.instrument = instrument()
        self.measure = measure()
        # self.memory = memory()
        # self.mmemory = mmemory()
        # self.output = output()
        # self.route = route()
        self.sense = sense()
        # self.source = source()
        # self.status = status()
        # self.system = system()
        # self.trigger = trigger()
        self.read = read()
        self.init = init()
        self.route = route()


class configure(str_return):
    # availanle commands for CONFigure
    # * CONFigure?
    # * CONFigure:CURRent:AC
    # * CONFigure:CURRent:DC
    # * CONFigure:DIGital:BYTE
    # * CONFigure:FREQuency
    # * CONFigure:FRESistance
    # *  CONFigure:PERiod
    # * CONFigure:RESistance
    # *  CONFigure:TEMPerature
    # * CONFigure:TOTalize
    # * CONFigure:VOLTage:AC
    # * CONFigure:VOLTage:DC
    def __init__(self):
        print("INIT CONFIGURE")
        super(configure, self).__init__()
        self.prefix = "CONFigure"
        self.cmd = "CONFigure"
        self.current = current(self.prefix)
        self.voltage = voltage(self.prefix)
        self.digital_byte = digital_byte(self.prefix)
        self.frequency = frequency(self.prefix)
        self.period = period(self.prefix)
        self.temperature = temperature(self.prefix)
        self.resistance = resistance(self.prefix)
        self.fresistance = fresistance(self.prefix)
        self.totalize = totalize(self.prefix)

class measure:
    # command list :
    # MEASure:CURRent:AC?
    # MEASure:CURRent:DC?
    # MEASure:DIGital:BYTE?
    # MEASure:FREQuency?
    # MEASure:FRESistance?
    # MEASure:PERiod?
    # MEASure:RESistance?
    # MEASure:TEMPerature?
    # MEASure:TOTalize?
    # MEASure:VOLTage:AC?
    # MEASure:VOLTage:DC?

    def __init__(self):
        print("INIT Measure")
        self.cmd = "MEASure"
        self.prefix = "MEASure"
        self.current = current(self.prefix)
        self.voltage = voltage(self.prefix)
        self.digital_byte = digital_byte(self.prefix)
        self.frequency = frequency(self.prefix)
        self.period = period(self.prefix)
        self.temperature = temperature(self.prefix)
        self.resistance = resistance(self.prefix)
        self.fresistance = fresistance(self.prefix)
        self.totalize = totalize(self.prefix)

class sense:
    # AC Current
    # [SENSe:]CURRent:AC:BANDwidth
    # [SENSe:]CURRent:AC:BANDwidth?
    # [SENSe:]CURRent:AC:RANGe
    # [SENSe:]CURRent:AC:RANGe?
    # [SENSe:]CURRent:AC:RANGe:AUTO
    # [SENSe:]CURRent:AC:RANGe:AUTO
    # [SENSe:]CURRent:AC:RESolution
    # [SENSe:]CURRent:AC:RESolution?
    # DC Current
    # [SENSe:]CURRent:DC:APERture
    # [SENSe:]CURRent:DC:APERture?
    # [SENSe:]CURRent:DC:NPLC
    # [SENSe:]CURRent:DC:NPLC?
    # [SENSe:]CURRent:DC:RANGe
    # [SENSe:]CURRent:DC:RANGe?
    # [SENSe:]CURRent:DC:RANGe:AUTO
    # [SENSe:]CURRent:DC:RANGe:AUTO
    # [SENSe:]CURRent:DC:RESolution
    # [SENSe:]CURRent:DC:RESolution?
    # AC Voltage
    # [SENSe:]VOLTage:AC:RANGe
    # [SENSe:]VOLTage:AC:RANGe?
    # [SENSe:]VOLTage:AC:RANGe:AUTO
    # [SENSe:]VOLTage:AC:RANGe:AUTO?
    # [SENSe:]VOLTage:AC:BANDwidth
    # [SENSe:]VOLTage:AC:BANDwidth?
    # DC Current
    # [SENSe:]VOLTage:DC:APERture
    # [SENSe:]VOLTage:DC:APERture?
    # [SENSe:]VOLTage:DC:NPLC
    # [SENSe:]VOLTage:DC:NPLC?
    # [SENSe:]VOLTage:DC:RANGe
    # [SENSe:]VOLTage:DC:RANGe?
    # [SENSe:]VOLTage:DC:RANGe:AUTO
    # [SENSe:]VOLTage:DC:RANGe:AUTO?
    # [SENSe:]VOLTage:DC:RESolution
    # [SENSe:]VOLTage:DC:RESolution?
    # 2-Wire Resistance
    # [SENSe:]RESistance:APERture
    # [SENSe:]RESistance:APERture?
    # [SENSe:]RESistance:NPLC
    # [SENSe:]RESistance:NPLC?
    # [SENSe:]RESistance:OCOMpensated
    # [SENSe:]RESistance:OCOMpensated?
    # [SENSe:]RESistance:RANGe
    # [SENSe:]RESistance:RANGe?
    # [SENSe:]RESistance:RANGe:AUTO
    # [SENSe:]RESistance:RANGe:AUTO?
    # [SENSe:]RESistance:RESolution
    # [SENSe:]RESistance:RESolution?
    # 4-Wire Resistance
    # [SENSe:]FRESistance:APERture
    # [SENSe:]FRESistance:APERture?
    # [SENSe:]FRESistance:NPLC
    # [SENSe:]FRESistance:NPLC?
    # [SENSe:]FRESistance:OCOMpensated
    # [SENSe:]FRESistance:OCOMpensated?
    # [SENSe:]FRESistance:RANGe
    # [SENSe:]FRESistance:RANGe?
    # [SENSe:]FRESistance:RANGe:AUTO
    # [SENSe:]FRESistance:RANGe:AUTO?
    # [SENSe:]FRESistance:RESolution
    # [SENSe:]FRESistance:RESolution?
    # Frequency
    # [SENSe:]FREQuency:APERture
    # [SENSe:]FREQuency:APERture?
    # [SENSe:]FREQuency:RANGe:LOWer
    # [SENSe:]FREQuency:RANGe:LOWer?
    # [SENSe:]FREQuency:VOLTage:RANGe
    # [SENSe:]FREQuency:VOLTage:RANGe?
    # [SENSe:]FREQuency:VOLTage:RANGe:AUTO
    # [SENSe:]FREQuency:VOLTage:RANGe:AUTO?

    def __init__(self):
        print("INIT Sense")
        self.cmd = "SENSe"
        self.prefix = "SENSe"
        self.current = current(self.prefix)
        self.voltage = voltage(self.prefix)
        self.digital_byte = digital_byte(self.prefix)
        self.frequency = frequency(self.prefix)
        self.period = period(self.prefix)
        self.temperature = temperature(self.prefix)
        self.resistance = resistance(self.prefix)
        self.fresistance = fresistance(self.prefix)
        self.totalize = totalize(self.prefix)

class route:
    # Command Summary
    # ROUTe:CHANnel:ADVance:SOURce
    # ROUTe:CHANnel:ADVance:SOURce?
    # ROUTe:CHANnel:DELay
    # ROUTe:CHANnel:DELay?
    # ROUTe:CHANnel:DELay:AUTO
    # ROUTe:CHANnel:DELay:AUTO?
    # ROUTe:CHANnel:FWIRe
    # ROUTe:CHANnel:FWIRe?
    # ROUTe:CLOSe
    # ROUTe:CLOSe?
    # ROUTe: CLOSe:EXCLusive
    # ROUTe: DONE?
    # ROUTe: MONitor
    # ROUTe: MONitor?
    # ROUTe: MONitor:DATA?
    # ROUTe: MONitor:STATe
    # ROUTe: MONitor:STATe?
    # ROUTe: OPEN
    # ROUTe: OPEN?
    # ROUTe: SCAN
    # ROUTe: SCAN?
    # ROUTe: SCAN:SIZE?
    def __init__(self):
        print("INIT ROUTE")
        self.cmd = "ROUTe"
        self.prefix = "ROUTe"
        self.scan = scan(self.prefix)
        self.open = open_channel(self.prefix)
        self.close = close_channel(self.prefix)
        self.done = done(self.prefix)
        self.monitor = monitor(self.prefix)


# --------------------------------------------
#             READ
# --------------------------------------------
class read(str_return):
    def __init__(self):
        print("INIT Read")
        self.prefix = "READ"
        self.cmd = "READ"

# --------------------------------------------
#             INIT
# --------------------------------------------
class init(str_return):
    def __init__(self):
        print("INIT INIT")
        self.prefix = "INIT"
        self.cmd = "INIT"


# part of ROUTE class
class scan(str_return):
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "SCAN"
        self.cmd = self.prefix
        self.size = size(self.prefix)

# part of ROUTE: SCAN class
class size(req_only):
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "SIZE"
        self.cmd = self.prefix

# part of ROUTE class
class open_channel(str_return):
    # This command opens the specified channels on a multiplexer or switch
    # module.
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "OPEN"
        self.cmd = self.prefix
        self.size = size(self.prefix)

# part of ROUTE class
class close_channel(str_return):
    # This command closes the specified channels on a multiplexer or switch
    # module. On the multiplexer modules, if any channel on the module is
    # defined to be part of the scan list, attempting to send this command will
    # result in an error.
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "CLOSe"
        self.cmd = self.prefix
        self.exclusive = exclusive(self.prefix)

class exclusive(str_return):
    # This command opens all channels on a multiplexer or switch module and
    # then closes the specified channels. On the multiplexer modules, if any
    # channel on the module is defined to be part of the scan list, attempting to
    # send this command will result in an error.
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "EXCLusive"
        self.cmd = self.prefix

class done(req_only):
    # This queries the status of all relay operations on cards not involved in the
    # scan and returns a 1 when all relay operations are finished (even during
    # a scan). ONLY -> ROUTe:DONE?
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "DONE"
        self.cmd = self.prefix

class monitor(req_only, ch_single):
    # This command/query selects the channel to be displayed on the front
    # panel. Only one channel can be monitored at a time.
    # ROUTe:MONitor
    # ROUTe:MONitor?
    # ROUTe:MONitor:DATA?
    # ROUTe:MONitor:STATe
    # ROUTe:MONitor:STATe?
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "MONitor"
        self.cmd = self.prefix
        self.data = data(self.prefix)
        self.state = state(self.prefix)

class data(req_only):
    # This query reads the monitor data from the selected channel. It returns
    # the reading only; the units, time, channel, and alarm information are not
    # returned (the FORMat:READing commands do not apply to monitor
    # readings).
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "DATA"
        self.cmd = self.prefix

class state(req_only):
    # This query reads the monitor data from the selected channel. It returns
    # the reading only; the units, time, channel, and alarm information are not
    # returned (the FORMat:READing commands do not apply to monitor
    # readings).
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "STATe"
        self.cmd = self.prefix
    def mode_on(self):
        return self.prefix + " 1"

    def mode_off(self):
        return self.prefix + " 0"

class voltage():
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "VOLTage"
        self.ac = ac(self.prefix)
        self.dc = dc(self.prefix)

class current():
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "Current"
        self.ac = ac(self.prefix)
        self.dc = dc(self.prefix)

class digital_byte(str_return):
    #This command configures the instrument to scan the specified digital
    #input channels on the multifunction module as byte data, but does not
    #initiate the scan. This command redefines the scan list.
    #The digital input channels are numbered "s01" (LSB) and "s02"
    #(MSB), where s is the first digit of the slot number.
    # example: CONF:DIG:BYTE (@101:102)
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "DIG:BYTE"
        self.cmd = self.prefix

class frequency(str_return):
    #These commands configure the channels for frequency or period
    #measurements, but they do not initiate the scan.
    #The CONFigure command does not place the instrument in the "wait-fortrigger"
    #state. Use the INITiate or READ? command in conjunction with
    #CONFigure to place the instrument in the "wait-for-trigger" state.
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "FREQuency"
        self.cmd = self.prefix

class period(str_return):
    # These commands configure the channels for frequency or period
    # measurements, but they do not initiate the scan.
    # The CONFigure command does not place the instrument in the "wait-fortrigger"
    # state. Use the INITiate or READ? command in conjunction with
    # CONFigure to place the instrument in the "wait-for-trigger" state.
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "PERiod"
        self.cmd = self.prefix

class temperature(str_return):
    # These commands configure the channels for temperature measurements
    # but do not initiate the scan. If you omit the optional <ch_list> parameter,
    # this command applies to the currently defined scan list.
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "TEMPerature"
        self.cmd = self.prefix

class resistance(str_return):
    # These commands configure the channels for 2-wire (RESistance)
    # resistance measurements but do not initiate the scan.
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "RESistance"
        self.cmd = self.prefix
        self.prefix = self.cmd
        self.Bandwidth = Bandwidth(self.prefix)
        self.Range = Range(self.prefix)
        self.Resolution = Resolution(self.prefix)
        self.Aperture = Aperture(self.prefix)
        self.NPLC = NPLC(self.prefix)
        self.Ocompensated = Ocompensated(self.prefix)

class fresistance(str_return):
    # These commands configure the channels for  4-wire (FRESistance) resistance
    # measurements but do not initiate the scan.
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "FRESistance"
        self.cmd = self.prefix
        self.prefix = self.cmd
        self.Bandwidth = Bandwidth(self.prefix)
        self.Range = Range(self.prefix)
        self.Resolution = Resolution(self.prefix)
        self.Aperture = Aperture(self.prefix)
        self.NPLC = NPLC(self.prefix)
        self.Ocompensated = Ocompensated(self.prefix)

class totalize(str_return):
    # This command configures the instrument to read the specified totalizer
    # channels on the multifunction module but does not initiate the scan. To
    # read the totalizer during a scan without resetting the count, set the
    # <mode> to READ. To read the totalizer during a scan and reset the count
    # to 0 after it is read, set the <mode> to RRESet (this means "read and
    # reset").
    # CONFigure:TOTalize <mode: READ|RRESet>,(@<scan_list>)

    def __init__(self, prefix):
        self.prefix = prefix + ":" + "TOTalize"
        self.cmd = self.prefix


class ac(str_return):
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "AC"
        self.prefix = self.cmd
        if self.prefix.find("SENSe:") != -1:
            self.Bandwidth = Bandwidth(self.prefix)
            self.Range = Range(self.prefix)
            self.Resolution = Resolution(self.prefix)



class dc(str_return):
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "DC"
        self.prefix = self.cmd
        if self.prefix.find("SENSe:") != -1:
            self.Bandwidth = Bandwidth(self.prefix)
            self.Range = Range(self.prefix)
            self.Resolution = Resolution(self.prefix)
            self.Aperture = Aperture(self.prefix)
            self.NPLC = NPLC(self.prefix)


class Bandwidth(str_return):
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "BANDwidth"


class Range(str_return):
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "RANGe"
        self.Auto = Auto(self.prefix)

class Auto(str_return):
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "AUTO"

class Resolution(str_return):
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "RESolution"

class Aperture(str_return):
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "APERture"

class NPLC(str_return):
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "NPLC"

class Ocompensated(str_return):
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "OCOMpensated"






if __name__ == '__main__':
    # dev = LOG_34970A()
    # dev.init("COM10")
    # dev.send("COM10 send")
    cmd = storage()
    # dev = com_interface()
    # dev.init("COM10")
    # cmd.init("COM10")
    # cmd.send(152200)
    # cmd.write("write inheritant".encode())
    # cmd.configure.send(1555)
    # cmd.configure.voltage.ac.send(5555)
    # cmd.configure.voltage.ac.send()
    # dev.send(cmd.configure.voltage.ac.combine(), 100)
    # dev.send(cmd.measure.voltage.ac.combine(), 10)
    # dev.send(cmd.configure.frequency.combine(), 100)
    # dev.send(cmd.configure.period.combine(),100)
    # dev.send(cmd.configure.digital_byte.combine(), 100)
    # print(cmd.configure.combine())
    #
    # print("*" * 30)
    # print(cmd.configure.current.ac.combine())
    # print(cmd.configure.current.dc.combine())
    # print(cmd.configure.digital_byte.combine())
    # print(cmd.configure.frequency.combine())
    # print(cmd.configure.fresistance.combine())
    # print(cmd.configure.period.combine())
    # print(cmd.configure.resistance.combine())
    # print(cmd.configure.temperature.combine())
    # print(cmd.configure.totalize.combine())
    # print(cmd.configure.voltage.ac.combine())
    # print(cmd.configure.voltage.dc.combine())
    # # print(cmd.configure.voltage.ac.Range.combine())
    # print(cmd.sense.voltage.ac.Range.combine())
    # print("*" * 30)
    # print(cmd.sense.current.ac.Bandwidth.combine())
    # print(cmd.sense.current.ac.Range.combine())
    # print(cmd.sense.current.ac.Range.Auto.combine())
    # print(cmd.sense.current.ac.Resolution.combine())
    #
    # print("*"*30)
    # print(cmd.sense.current.dc.Aperture.combine())
    # print(cmd.sense.current.dc.NPLC.combine())
    # print(cmd.sense.current.dc.Range.combine())
    # print(cmd.sense.current.dc.Range.Auto.combine())
    # print(cmd.sense.current.dc.Resolution.combine())
    #
    # print("*" * 30)
    # print(cmd.sense.voltage.ac.Range.combine())
    # print(cmd.sense.voltage.ac.Resolution.combine())
    # print(cmd.sense.voltage.ac.Bandwidth.combine())
    #
    # print("*" * 30)
    # print(cmd.sense.current.dc.Aperture.combine())
    # print(cmd.sense.current.dc.NPLC.combine())
    # print(cmd.sense.current.dc.Range.combine())
    # print(cmd.sense.current.dc.Range.Auto.combine())
    # print(cmd.sense.current.dc.Resolution.combine())
    #
    # print("*" * 30)
    # print(cmd.sense.resistance.Aperture.combine())
    # print(cmd.sense.resistance.NPLC.combine())
    # print(cmd.sense.resistance.Ocompensated.combine())
    # print(cmd.sense.resistance.Range.combine())
    # print(cmd.sense.resistance.Range.Auto.combine())
    # print(cmd.sense.resistance.Resolution.combine())
    #
    # print("*" * 30)
    # print(cmd.sense.fresistance.Aperture.combine())
    # print(cmd.sense.fresistance.NPLC.combine())
    # print(cmd.sense.fresistance.Ocompensated.combine())
    # print(cmd.sense.fresistance.Range.combine())
    # print(cmd.sense.fresistance.Range.Auto.combine())
    # print(cmd.sense.fresistance.Resolution.combine())
    # # dev.close()
    # print(cmd.read.combine())
    print(cmd.read.ch_range(0, 301, 305))
    print(cmd.read.ch_range(1, 301, 305))
    print(cmd.read.ch_list(1, 301, 302))

    print("*" * 30)
    print(cmd.route.scan.str())
    print(cmd.route.scan.size.req())
    print(cmd.route.scan.ch_range(0, 301, 320))
    print(cmd.route.close.exclusive.str())
    print(cmd.route.close.exclusive.ch_range(0,110,120))
    print(cmd.route.open.req())
    print(cmd.route.scan.size.req())
    print(cmd.route.done.req())
    print(cmd.route.monitor.req())
    print(cmd.route.monitor.ch_single(320))
    print(cmd.route.monitor.state.mode_on())
    print(cmd.route.monitor.state.mode_off())
    print(cmd.route.monitor.state.req())
