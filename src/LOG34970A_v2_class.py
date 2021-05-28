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

def ch_list_from_range(is_req, min, max, channels_num=20):
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
    txt = f"{req_txt} (@{txt})"
    return txt

def ch_list_from_list(is_req, *argv):
    req_txt = "?" if is_req == 1 else ""

    txt = f"{argv}"
    print(f'1****{txt}')
    txt = txt[2:-3]
    print(f'2****{txt}')
    txt = txt.replace(" ", "")
    print(f'3****{txt}')
    txt = f'{req_txt} (@{txt})'
    print(f'4****{txt}')
    return txt



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
        ch_list_txt = ch_list_from_list(is_req, argv)
        txt = f'{self.cmd}{ch_list_txt}'
        return txt

    def ch_range(self,is_req, min, max, channels_num=20):
        ch_list_txt = ch_list_from_range(is_req,min,max,channels_num)
        txt = f"{self.cmd}{ch_list_txt}"
        return txt

class str:
    def __init__(self):
        self.cmd = None

    def str(self):
        # will put sending command here
        return self.cmd


class req:
    def __init__(self):
        self.cmd = None

    def req(self):
        return self.cmd + "?"

class req_param:
    def __init__(self):
        self.cmd = None

    def req(self, count, min = 0, max = 50000):
        count = range_check(count, min, max, "MAX count")
        txt = f'{self.cmd}? {count}'
        return txt


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
        ch_list_txt = ch_list_from_list(0, argv)
        txt = f'{self.cmd}{ch_list_txt}'
        return txt

    def ch_range(self, min, max, channels_num=20):
        ch_list_txt = ch_list_from_range(0,min,max,channels_num)
        txt = f"{self.cmd}{ch_list_txt})"
        return txt



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
        self.route = route()
        self.abort = abort()
        self.fetch = fetch()
        self.init = init()
        self.read = read()
        self.r = r()
        self.unit_temperature = unit_temperature()
        self.input_impedance_auto =  input_impedance_auto()


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


# **********  ABORt *************
class abort(str):
    # The following command aborts the measurement in progress.
    def __init__(self):
        print("INIT Abort")
        self.prefix = "ABORt"
        self.cmd = "ABORt"
# **********  Fetch *************
class fetch(req):
    # The following command aborts the measurement in progress.
    def __init__(self):
        print("INIT FETCh")
        self.prefix = "FETCh"
        self.cmd = "FETCh"

# **********  READ *************
class read(str_return):
    def __init__(self):
        print("INIT Read")
        self.prefix = "READ"
        self.cmd = "READ"

# **********  R? *************
class r(req_param):
    # This query reads and erases readings from volatile memory up to the
    # specified <max_count>. The readings are erased from memory starting
    # with the oldest reading first. The purpose of this command is to allow you
    # to periodically remove readings from memory that would normally cause
    # reading memory to overflow (for example, during a scan with an infinite
    # scan count).
    def __init__(self):
        print("INIT R?")
        self.prefix = "R"
        self.cmd = "R"

# **********  INIT *************
class init(str):
    # This command changes the state of the triggering system from the "idle"
    # state to the "wait-for-trigger" state. Scanning will begin when the
    # specified trigger conditions are satisfied following the receipt of the
    # INITiate command. Readings are stored in the instrument's internal
    # reading memory. Note that the INITiate command also clears the
    # previous set of readings from memory.
    # If a scan list is currently defined (see ROUTe:SCAN command), the
    # INITiate command performs a scan of the specified channels.
    # If a scan list is not currently defined, the INITiate command fails.
    def __init__(self):
        print("INIT INIT")
        self.prefix = "INITiate"
        self.cmd = "INITiate"

# **********  UNIT:TEMPerature *************
class unit_temperature:
    def __init__(self):
        print("INIT Read")
        self.prefix = "UNIT:TEMPerature"
        self.cmd = "UNIT:TEMPerature"

    def req_ch_range(self, ch_min, ch_max):
        ch_list_txt = ch_list_from_range(1, ch_min,ch_max,20)
        txt = f'{self.cmd}{ch_list_txt}'
        return txt

    def req_ch_list(self, *channels):
        ch_list_txt = ch_list_from_list(1, channels)
        txt = f'{self.cmd}{ch_list_txt}'
        return txt

    def conf_ch_range(self, ch_min, ch_max, unit="C"):
    # The query returns C, F, or K for each channel specified.
    # Multiple responses are separated by commas.
        ch_list_txt = ch_list_from_range(0, ch_min, ch_max, 20)
        unit_list = ["C","F","K"]
        unit = unit.upper()
        txt = "none"
        if unit in unit_list:
            txt = f'{self.cmd} {unit},{ch_list_txt[1:]}'
        else:
           print(f'{self.cmd} incorrect unit. you entered: {unit}')
           print(f' A "C" was used as a default ')
        return txt

class input_impedance_auto:
    def __init__(self):
        print("INIT INPut:IMPedance:AUTO")
        self.prefix = "INPut:IMPedance:AUTO"
        self.cmd = "INPut:IMPedance:AUTO"

    def req_ch_range(self, ch_min, ch_max):
        ch_list_txt = ch_list_from_range(1, ch_min, ch_max, 20)
        txt = f'{self.cmd}{ch_list_txt}'
        return txt

    def req_ch_list(self, *channels):
        ch_list_txt = ch_list_from_list(1, channels)
        txt = f'{self.cmd}{ch_list_txt}'
        return txt

    def conf_ch_range(self, ch_min, ch_max, on_off=1):
        # This command enables or disables the automatic input resistance mode
        # for DC voltage measurements on the specified channels.
        ch_list_txt = ch_list_from_range(0, ch_min, ch_max, 20)
        on_off = range_check(on_off, 0, 1, "input impedance On/Off. enter 0 or 1" )
        txt_var = "ON" if on_off == 1 else "OFF"
        txt = f'{self.cmd} {txt_var} {ch_list_txt}'
        return txt


# part of ROUTE class
class scan(str_return):
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "SCAN"
        self.cmd = self.prefix
        self.size = size(self.prefix)

# part of ROUTE: SCAN class
class size(req):
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

class done(req):
    # This queries the status of all relay operations on cards not involved in the
    # scan and returns a 1 when all relay operations are finished (even during
    # a scan). ONLY -> ROUTe:DONE?
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "DONE"
        self.cmd = self.prefix

class monitor(req, ch_single):
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

class data(req):
    # This query reads the monitor data from the selected channel. It returns
    # the reading only; the units, time, channel, and alarm information are not
    # returned (the FORMat:READing commands do not apply to monitor
    # readings).
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "DATA"
        self.cmd = self.prefix

class state(req):
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
    print(cmd.abort.str())
    print(cmd.fetch.req())
    print(cmd.r.req(100))
    print(cmd.init.str())
    print(cmd.read.req())
    print(cmd.read.ch_range(0, 110, 120))
    print(cmd.read.ch_range(1, 110, 120))
    print(cmd.read.ch_list(0, 302, 305, 307, 308))
    print(cmd.read.ch_list(1, 302, 303))
    print(cmd.read.ch_list(0, 303))
    print(cmd.r.req(1000))
    print(cmd.unit_temperature.conf_ch_range(110, 120, "F"))
    print(cmd.unit_temperature.req_ch_range(110, 120))
    print(cmd.unit_temperature.req_ch_list(110))
    print(cmd.input_impedance_auto.conf_ch_range(110,120, 1))
    print(cmd.input_impedance_auto.conf_ch_range(110, 120, 0))
    print(cmd.input_impedance_auto.req_ch_range(110,120))
    print(cmd.input_impedance_auto.req_ch_list(115,110,112,118,120))


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
