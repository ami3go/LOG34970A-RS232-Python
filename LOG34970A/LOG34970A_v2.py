import serial.tools.list_ports
import time

import pyvisa  # only used here to enumerate VISA resources; I/O goes through VisaTransport

from scpi_driver_core import ScpiClient, ScpiDriverError
from scpi_driver_core.scpi.codec import ScpiTextCodec
from scpi_driver_core.transport.models import FlushDirection, TransportState
from scpi_driver_core.transport.serial import SerialTransport
from scpi_driver_core.transport.visa import VisaTransport

# RS232 framing used by this instrument: commands are terminated with CRLF,
# responses with LF (matches the previous hand-rolled pyserial readline()).
_RS232_CODEC = ScpiTextCodec(command_terminator=b"\r\n", response_terminator=b"\n")

# VISA (USBTMC/GPIB) framing: commands are terminated with CRLF (matches the
# previous app.write_termination = "\r\n"). response_terminator=None means a
# reply is read as one whole VISA message (EOI-delimited), matching the
# previous behaviour of never setting read_termination on the pyvisa resource.
_VISA_CODEC = ScpiTextCodec(command_terminator=b"\r\n", response_terminator=None)

def range_check(val, min, max, val_name):
    if val > max:
        print(f"Wrong {val_name}: {val}. Max value should be less then {max}")
        val = max
    if val < min:
        print(f"Wrong {val_name}: {val}. Should be >= {min}")
        val = min
    return val


# def ch_list_from_range(is_req, min, max, add_space=1, channels_num=20 ):
#     channels_34901A = 20  # 34901A 20 Channel Multiplexer (2/4-wire) Module
#     channels_34902A = 16  # 34902A 16 Channel Multiplexer (2/4-wire) Module
#     channels_34908 = 40  # 34908A 40 Channel Single-Ended Multiplexer Module
#     req_txt = "?" if is_req == 1 else ""
#     space_txt = " " if add_space == 1 else ""
#     channels = channels_num
#     slot_id = int(min/100)
#     slot_id = range_check(slot_id,1,3,"slot ID")
#     min = range_check(min, (slot_id*100+1), (slot_id*100+channels), " channels number")
#     max = range_check(max, (slot_id*100+1), (slot_id*100+channels), " channels number")
#     txt = f"{min},"
#     l = [f"{min},"]
#     for z in range(0, (max - min)):
#         l.append(f'{min + z + 1},')
#     txt = "".join(l)
#     txt = txt[:-1]
#     txt = f"{req_txt}{space_txt}(@{txt})"
#     return txt


# def ch_list_from_list(is_req, *argv):
#     req_txt = "?" if is_req == 1 else ""
#     txt = ""
#     for items in argv:
#         txt = f'{txt}{items},'
#     txt = txt[:-1]
#     txt = f'{req_txt} (@{txt})'
#     return txt


def ch_list_from_list2(*argv):
    txt = ""
    for items in argv:
        txt = f'{txt}{items},'
    txt = txt[:-1]
    return f'(@{txt})'


def ch_list_from_range2(min, max, channels_num=20):
    channels_34901A = 20  # 34901A 20 Channel Multiplexer (2/4-wire) Module
    channels_34902A = 16  # 34902A 16 Channel Multiplexer (2/4-wire) Module
    channels_34908 = 40  # 34908 40 Channel Single-Ended Multiplexer Module
    channels = channels_num
    slot_id = int(min / 100)
    slot_id = range_check(slot_id, 1, 3, "slot ID")
    min = range_check(min, (slot_id * 100 + 1), (slot_id * 100 + channels), " channels number")
    max = range_check(max, (slot_id * 100 + 1), (slot_id * 100 + channels), " channels number")
    txt = f"{min},"
    l = [f"{min},"]
    for z in range(0, (max - min)):
        l.append(f'{min + z + 1},')
    txt = "".join(l)
    txt = txt[:-1]
    return f"(@{txt})"


# default USB/GPIB VISA resource substring for the Keysight IO Libraries
# bridge (USBTMC over a GPIB-USB adapter)
_DEFAULT_USB_RESOURCE_SUBSTRING = 'USB0::0x03EB::0x2065::GPIB_01_55137303031351C0D071::0::INSTR'


class LOG34970A:
    """34970A connection over either RS232 (serial) or USB/GPIB (VISA).

    Both connect_serial() and connect_usb() leave the instance in the same
    state: send()/query()/close() behave identically afterwards regardless of
    which physical connection was used.
    """

    # write/read delay (s) and post-connect read timeout used on the VISA
    # path, kept from the original usb_interface driver; see
    # docs/scpi-driver-core.md "Worth knowing".
    _USB_QUERY_DELAY_S = 1
    # NOTE: the original driver set this to 10ms after connecting, which is too
    # short for a real reply and is only survivable because of the retry loop
    # in _query_usb(). Kept as-is; see docs/scpi-driver-core.md "Worth knowing".
    _USB_POST_CONNECT_TIMEOUT_S = 0.010

    def __init__(self):
        self.cmd = None
        self._client = None
        self._connection = None  # "serial" or "usb", set by connect_*()
        self._rm = None  # VISA ResourceManager, only held for "usb"

    # -- connecting ---------------------------------------------------

    def connect_serial(self, com_port, baudrate_var=115200):
        """Connect over RS232. Returns False if com_port isn't present."""
        com_port_list = [comport.device for comport in serial.tools.list_ports.comports()]
        if com_port not in com_port_list:
            print("COM port is not found")
            print("Please ensure that USB is connected")
            print(f"Please check COM port Number. Currently it is {com_port} ")
            print(f'Founded COM ports:{com_port_list}')
            return False

        transport = SerialTransport(
            com_port,
            baudrate=baudrate_var,
            timeout_s=0.1,
            write_timeout_s=5.0,
        )
        self._client = ScpiClient(transport, codec=_RS232_CODEC)
        self._connection = "serial"
        transport.open()

        read_back = self.query('*IDN?')
        print(f"Connected to: {read_back}")
        return True

    def connect_usb(self, resource_substring=_DEFAULT_USB_RESOURCE_SUBSTRING, timeout_s=5.0):
        """Connect over USB/GPIB through the Keysight IO Libraries VISA backend.

        Scans the VISA resource list for one containing resource_substring,
        the same discovery this driver has always used for the native USB-GPIB
        bridge. Returns False if no matching resource is found.
        """
        self._rm = pyvisa.ResourceManager()
        resource_name = next(
            (item for item in self._rm.list_resources() if resource_substring in item), None
        )
        if resource_name is None:
            print(f"No VISA resource matching {resource_substring!r} found")
            print(f"Found VISA resources: {list(self._rm.list_resources())}")
            self._rm.close()
            self._rm = None
            return False

        transport = VisaTransport(resource_name, timeout_s=timeout_s, resource_manager=self._rm)
        self._client = ScpiClient(transport, codec=_VISA_CODEC)
        self._connection = "usb"
        transport.open()
        print(resource_name)
        time.sleep(1)

        read_back = self.query('*IDN?')
        print(f"Connected to: {read_back}")
        return True

    # -- communication --------------------------------------------------

    def send(self, txt):
        self._client.write(txt)

    def query(self, cmd_srt):
        if self._connection == "serial":
            return self._query_serial(cmd_srt)
        return self._query_usb(cmd_srt)

    def _query_serial(self, cmd_srt):
        # matches the previous reset_input_buffer() before every query
        self._client.transport.flush(FlushDirection.INPUT)
        return self._client.query(cmd_srt)

    def _query_usb(self, cmd_srt):
        """Query the VISA resource. Resends up to 10 times in case of any error.

        :param cmd_srt: VISA string command
        :type cmd_srt: str
        :return: VISA string reply
        """
        for i in range(10):
            try:
                self._client.write(cmd_srt)
                # regular delay according to datasheet before next command
                time.sleep(self._USB_QUERY_DELAY_S)
                raw = self._client.read_bytes(
                    self._client.response_request, timeout_s=self._USB_POST_CONNECT_TIMEOUT_S
                )
                return self._client.codec.decode_response(raw)

            except ScpiDriverError as e:
                print(f"query[{i}]: {cmd_srt}, Error: {e}")
                # a read that times out leaves the core transport FAULTED
                # (see docs/scpi-driver-core.md); reopen before the next try
                if self._client.transport.state is TransportState.FAULTED:
                    self._client.transport.open()
                time.sleep(3)

    def close(self):
        if self._connection == "usb":
            self._client.transport.flush(FlushDirection.BOTH)
        self._client.transport.close()
        self._client = None
        if self._rm is not None:
            self._rm.close()
            self._rm = None
        self._connection = None





class str_return:
    def __init__(self):
        self.cmd = None

    def str(self):
        # will put sending command here
        return self.cmd

    def req(self):
        return self.cmd + "?"

    def ch_list(self, is_req, *argv):
        ch_list_txt = ch_list_from_list(is_req, *argv)
        txt = f'{self.cmd}{ch_list_txt}'
        return txt

    def ch_range(self, is_req, min, max, channels_num=20):
        ch_list_txt = ch_list_from_range2(min, max)
        txt = f"{self.cmd}{ch_list_txt}"
        return txt


class str:
    def __init__(self):
        self.cmd = None

    def str(self):
        # will put sending command here
        return self.cmd


class req2(str):
    def __init__(self, prefix):
        self.prefix = prefix + "?"
        self.cmd = self.prefix
        self.ch = select_channel2(self.prefix + " ")


class conf2(str):
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix
        self.ch = select_channel2(self.prefix)


class select_channel2:
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix

    def list(self, *argv):
        ch_list_txt = ch_list_from_list2(*argv)
        txt = f'{self.cmd}{ch_list_txt}'
        return txt

    def range(self, min, max, channels_num=20):
        ch_list_txt = ch_list_from_range2(min, max, channels_num)
        txt = f"{self.cmd}{ch_list_txt}"
        return txt


class req:
    def __init__(self):
        self.cmd = None

    def req(self):
        return self.cmd + "?"

class req3:
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix

    def req(self):
        return self.cmd + "?"



class str3:
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix

    def str(self, ):
        return self.cmd


class str_and_req:
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix

    def str(self, ):
        return self.cmd

    def req(self):
        return self.cmd + "?"


class sel_ch_with_param:
    def __init__(self, prefix, min, max):
        self.prefix = prefix
        self.cmd = self.prefix
        self.max = max
        self.min = min

    def list(self,var, *argv):
        var = range_check(var, self.min, self.max, self.cmd)
        ch_list_txt = ch_list_from_list2(*argv)
        txt = f'{self.cmd} {var},{ch_list_txt}'
        return txt

    def range(self, var, ch_min, ch_max, ch_num=20):
        var = range_check(var, self.min, self.max, self.cmd)
        ch_list_txt = ch_list_from_range2(ch_min, ch_max, ch_num)
        txt = f"{self.cmd} {var},{ch_list_txt}"
        return txt


class sel_ch_with_value:
    # Like sel_ch_with_param, but the leading value is passed through as-is
    # (a discrete keyword, or a number with no documented/enforceable
    # range) instead of being numerically range-checked.
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix

    def list(self, value, *argv):
        ch_list_txt = ch_list_from_list2(*argv)
        txt = f'{self.cmd} {value},{ch_list_txt}'
        return txt

    def range(self, value, ch_min, ch_max, ch_num=20):
        ch_list_txt = ch_list_from_range2(ch_min, ch_max, ch_num)
        txt = f"{self.cmd} {value},{ch_list_txt}"
        return txt


class discrete_setting:
    # A discrete-value set/query pair with no channel-list argument, e.g.
    # OUTPut:ALARm:MODE {LATCh|TRACk}.
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix
        self.req = req3(self.prefix)

    def conf(self, value):
        return f'{self.cmd} {value}'


class bool_setting:
    # A boolean set/query pair with no channel-list argument, e.g.
    # FORMat:READing:ALARm {OFF|0|ON|1}.
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix
        self.req = req3(self.prefix)

    def on(self):
        return f'{self.cmd} ON'

    def off(self):
        return f'{self.cmd} OFF'


class dig_param:
    def __init__(self):
        self.cmd = None  # this value to be inherited for high order class
        self.max = None  # this value to be inherited for high order class
        self.min = None  # this value to be inherited for high order class

    def val(self, count=0):
        count = range_check(count, self.min, self.max, "MAX count")
        txt = f'{self.cmd} {count}'
        return txt

class dig_param3:
    def __init__(self, prefix, min, max):
        self.prefix = prefix
        self.cmd = self.prefix
        self.max = max
        self.min = min

    def val(self, count=0):
        count = range_check(count, self.min, self.max, "MAX count")
        txt = f'{self.cmd} {count}'
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
    def __init__(self):
        self.cmd = None

    def ch_list(self, *argv):
        ch_list_txt = ch_list_from_list(0, *argv)
        txt = f'{self.cmd}{ch_list_txt}'
        return txt

    def ch_range(self, min, max, channels_num=20):
        ch_list_txt = ch_list_from_range2( min, max)
        txt = f"{self.cmd}{ch_list_txt}"
        return txt


# **********  DATA Subsystem *************
class data_last:
    # DATA:LAST? [<num_rdgs>,](@<channel>)  -- note: a single channel, not a
    # scan list.
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix

    def req(self, channel, num_rdgs=None):
        count_txt = f'{num_rdgs},' if num_rdgs is not None else ''
        return f'{self.cmd}? {count_txt}(@{channel})'


class data_remove:
    # DATA:REMove? <num_rdgs> -- a query that also takes a parameter.
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix
        self.min = 1
        self.max = 50000

    def req(self, num_rdgs):
        num_rdgs = range_check(num_rdgs, self.min, self.max, self.cmd)
        return f'{self.cmd}? {num_rdgs}'


class data:
    # DATA:LAST? [<num_rdgs>,](@<channel>)
    # DATA:POINts?
    # DATA:POINts:EVENt:THReshold <num_rdgs>
    # DATA:POINts:EVENt:THReshold?
    # DATA:REMove? <num_rdgs>
    def __init__(self):
        self.cmd = "DATA"
        self.prefix = "DATA"
        self.last = data_last(self.prefix + ":LAST")
        self.points_req = req3(self.prefix + ":POINts")
        self.points_event_threshold = dig_param3(self.prefix + ":POINts:EVENt:THReshold", 0, 50000)
        self.points_event_threshold_req = req3(self.prefix + ":POINts:EVENt:THReshold")
        self.remove = data_remove(self.prefix + ":REMove")


# **********  DISPlay Subsystem *************
class display_text:
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix
        self.req = req3(self.prefix)
        self.clear = str3(self.prefix + ":CLEar")

    def conf(self, message):
        return f'{self.cmd} "{message}"'


class display:
    # DISPlay <state> / DISPlay?
    # DISPlay:TEXT <quoted_string> / DISPlay:TEXT? / DISPlay:TEXT:CLEar
    def __init__(self):
        self.cmd = "DISPlay"
        self.prefix = "DISPlay"
        self.req = req3(self.prefix)
        self.on = str3(self.prefix + " ON")
        self.off = str3(self.prefix + " OFF")
        self.text = display_text(self.prefix + ":TEXT")


# **********  FORMat Subsystem *************
class fformat_time_type:
    def __init__(self, prefix):
        self.prefix = prefix + ":TYPE"
        self.cmd = self.prefix
        self.req = req3(self.prefix)
        self.absolute = str3(self.prefix + " ABSolute")
        self.relative = str3(self.prefix + " RELative")


class fformat:
    # FORMat:READing:{ALARm|CHANnel|TIME|UNIT} {OFF|0|ON|1} / ?
    # FORMat:READing:TIME:TYPE {ABSolute|RELative} / ?
    # These control what accompanies each reading pulled from a scan (READ?/
    # FETCh?); they apply instrument-wide, not per channel.
    def __init__(self):
        self.cmd = "FORMat:READing"
        self.prefix = "FORMat:READing"
        self.alarm = bool_setting(self.prefix + ":ALARm")
        self.channel = bool_setting(self.prefix + ":CHANnel")
        self.time = bool_setting(self.prefix + ":TIME")
        self.time_type = fformat_time_type(self.prefix + ":TIME")
        self.unit = bool_setting(self.prefix + ":UNIT")


# **********  MEMory Subsystem *************
class memory_state_name:
    # MEMory:STATe:NAME <location>[,<name>] / MEMory:STATe:NAME? <location>
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix
        self.min = 0
        self.max = 5

    def conf(self, location, name):
        location = range_check(location, self.min, self.max, self.cmd)
        return f'{self.cmd} {location},"{name}"'

    def req(self, location):
        location = range_check(location, self.min, self.max, self.cmd)
        return f'{self.cmd}? {location}'


class memory_state_valid:
    # MEMory:STATe:VALid? <location>
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix
        self.min = 0
        self.max = 5

    def req(self, location):
        location = range_check(location, self.min, self.max, self.cmd)
        return f'{self.cmd}? {location}'


class memory:
    # MEMory:NSTates? -- always 6 locations (0-5) on the 34970A/34972A.
    # MEMory:STATe:DELete <location>
    # MEMory:STATe:NAME <location>[,<name>] / ?
    # MEMory:STATe:RECall:AUTO {OFF|0|ON|1} / ?
    # MEMory:STATe:VALid? <location>
    def __init__(self):
        self.cmd = "MEMory"
        self.prefix = "MEMory"
        self.nstates_req = req3(self.prefix + ":NSTates")
        self.state_delete = dig_param3(self.prefix + ":STATe:DELete", 0, 5)
        self.state_name = memory_state_name(self.prefix + ":STATe:NAME")
        self.state_recall_auto = bool_setting(self.prefix + ":STATe:RECall:AUTO")
        self.state_valid = memory_state_valid(self.prefix + ":STATe:VALid")


# **********  OUTPut Subsystem *************
class output_alarm_channel:
    # OUTPut:ALARm{1|2|3|4}:CLEar
    # OUTPut:ALARm{1|2|3|4}:SOURce (@<ch_list>) / ?
    def __init__(self, prefix, alarm_num):
        self.prefix = f'{prefix}{alarm_num}'
        self.cmd = self.prefix
        self.clear = str3(self.prefix + ":CLEar")
        self.source = conf2(self.prefix + ":SOURce ")
        self.source_req = req3(self.prefix + ":SOURce")


class output:
    # OUTPut:ALARm:CLEar:ALL
    # OUTPut:ALARm:MODE {LATCh|TRACk} / ?
    # OUTPut:ALARm:SLOPe {NEGative|POSitive} / ?
    # OUTPut:ALARm{1|2|3|4}:CLEar / :SOURce
    def __init__(self):
        self.cmd = "OUTPut"
        self.prefix = "OUTPut"
        alarm_prefix = self.prefix + ":ALARm"
        self.clear_all = str3(alarm_prefix + ":CLEar:ALL")
        self.mode = discrete_setting(alarm_prefix + ":MODE")
        self.mode_latch = str3(alarm_prefix + ":MODE LATCh")
        self.mode_track = str3(alarm_prefix + ":MODE TRACk")
        self.slope = discrete_setting(alarm_prefix + ":SLOPe")
        self.slope_negative = str3(alarm_prefix + ":SLOPe NEGative")
        self.slope_positive = str3(alarm_prefix + ":SLOPe POSitive")
        self.alarm1 = output_alarm_channel(alarm_prefix, 1)
        self.alarm2 = output_alarm_channel(alarm_prefix, 2)
        self.alarm3 = output_alarm_channel(alarm_prefix, 3)
        self.alarm4 = output_alarm_channel(alarm_prefix, 4)


# **********  CALCulate Subsystem *************
# Requires the instrument's internal DMM to store readings and perform
# calculations (see the Command Reference's CALCulate Subsystem
# Introduction); an error is returned if it is disabled or not installed.
class calculate_average:
    def __init__(self, prefix):
        self.prefix = prefix + ":AVERage"
        self.cmd = self.prefix
        self.average_req = req2(self.prefix + ":AVERage")
        self.clear = conf2(self.prefix + ":CLEar ")
        self.count_req = req2(self.prefix + ":COUNt")
        self.maximum_req = req2(self.prefix + ":MAXimum")
        self.maximum_time_req = req2(self.prefix + ":MAXimum:TIME")
        self.minimum_req = req2(self.prefix + ":MINimum")
        self.minimum_time_req = req2(self.prefix + ":MINimum:TIME")
        self.ptpeak_req = req2(self.prefix + ":PTPeak")


class calculate_compare:
    def __init__(self, prefix):
        self.prefix = prefix + ":COMPare"
        self.cmd = self.prefix
        self.data = sel_ch_with_value(self.prefix + ":DATA")
        self.data_req = req2(self.prefix + ":DATA")
        self.mask = sel_ch_with_value(self.prefix + ":MASK")
        self.mask_req = req2(self.prefix + ":MASK")
        self.state = req_on_off_ch_select(self.prefix + ":STATe")
        self.type = sel_ch_with_value(self.prefix + ":TYPE")
        self.type_req = req2(self.prefix + ":TYPE")


class calculate_limit:
    def __init__(self, prefix):
        self.prefix = prefix + ":LIMit"
        self.cmd = self.prefix
        self.lower = sel_ch_with_value(self.prefix + ":LOWer")
        self.lower_req = req2(self.prefix + ":LOWer")
        self.lower_state = req_on_off_ch_select(self.prefix + ":LOWer:STATe")
        self.upper = sel_ch_with_value(self.prefix + ":UPPer")
        self.upper_req = req2(self.prefix + ":UPPer")
        self.upper_state = req_on_off_ch_select(self.prefix + ":UPPer:STATe")


class calculate_scale:
    def __init__(self, prefix):
        self.prefix = prefix + ":SCALe"
        self.cmd = self.prefix
        self.gain = sel_ch_with_value(self.prefix + ":GAIN")
        self.gain_req = req2(self.prefix + ":GAIN")
        self.offset = sel_ch_with_value(self.prefix + ":OFFSet")
        self.offset_req = req2(self.prefix + ":OFFSet")
        self.offset_null = conf2(self.prefix + ":OFFSet:NULL ")
        self.state = req_on_off_ch_select(self.prefix + ":STATe")
        self.unit = sel_ch_with_value(self.prefix + ":UNIT")
        self.unit_req = req2(self.prefix + ":UNIT")


class calculate:
    def __init__(self):
        self.cmd = "CALCulate"
        self.prefix = "CALCulate"
        self.average = calculate_average(self.prefix)
        self.compare = calculate_compare(self.prefix)
        self.limit = calculate_limit(self.prefix)
        self.scale = calculate_scale(self.prefix)


class storage:
    def __init__(self):
        self.cmd = None
        self.prefix = None
        # super(communicator, self).__init__()
        # super(storage,self).__init__()
        # this is the list of Subsystem commands
        self.calculate = calculate()
        # CALibration subsystem intentionally not implemented: it exposes a
        # calibration security code and writes calibration constants to the
        # instrument. See docs/scpi-driver-core.md.
        self.configure = configure()
        self.data = data()
        # DIAGnostic subsystem intentionally not implemented: engineering/
        # service-only slot-memory peek/poke. See docs/scpi-driver-core.md.
        self.display = display()
        self.fformat = fformat()
        # INSTrument subsystem intentionally not implemented: controls the
        # 34972A's internal DMM module, which this driver targets the
        # 34970A without. See docs/scpi-driver-core.md.
        self.measure = measure()
        self.memory = memory()
        # MMEMory subsystem (USB mass-storage export/import) intentionally
        # not implemented: not applicable over RS232/GPIB. See
        # docs/scpi-driver-core.md.
        self.output = output()
        self.sense = sense()
        self.source = source()
        self.status = status()
        self.system = system()
        self.trigger = trigger()
        self.route = route()
        self.abort = str3("ABORt")
        self.fetch = req3("FETCh")
        self.init = str3("INITiate")
        self.read = req3("READ")
        self.idn = req3("*IDN")
        self.reset = str3("*RST")
        self.r = dig_param3("R?", 1, 50000)
        self.unit_temperature = unit_temperature()
        self.input_impedance_auto = req_on_off_ch_select("INPut:IMPedance:AUTO")
        # IEEE-488.2 common commands not already covered by status.ese/esr/
        # sre/stb above, or by idn/reset(*RST) above.
        self.cls = str3("*CLS")
        self.opc = str3("*OPC")
        self.opc_req = req3("*OPC")
        self.psc = dig_param3("*PSC", 0, 1)
        self.psc_req = req3("*PSC")
        self.rcl = dig_param3("*RCL", 0, 5)
        self.sav = dig_param3("*SAV", 0, 5)
        self.trg = str3("*TRG")
        self.tst_req = req3("*TST")
        self.wai = str3("*WAI")


class configure(req):
    # availanle commands for CONFigure
    # * CONFigure?
    # * CONFigure:CURRent:AC
    # * CONFigure:CURRent:DC
    # * CONFigure:DIGital:BYTE
    # * CONFigure:FREQuency
    # * CONFigure:FRESistance
    # * CONFigure:PERiod
    # * CONFigure:RESistance
    # * CONFigure:TEMPerature
    # * CONFigure:TOTalize
    # * CONFigure:VOLTage:AC
    # * CONFigure:VOLTage:DC
    def __init__(self):
        # print("INIT CONFIGURE")
        super(configure, self).__init__()
        # NOTE: self.prefix must be the long form "CONFigure", not the short
        # "CONF", because every child class below gates its .conf attribute
        # on `self.prefix.find("CONFigure:")`. Using the short form here used
        # to make that check fail silently everywhere, so cmd.configure.*.conf
        # never existed (see docs/scpi-driver-core.md).
        self.prefix = "CONFigure"
        self.cmd = "CONF"
        self.current = current(self.prefix)
        self.voltage = voltage(self.prefix)
        self.digital_byte = digital_byte(self.prefix)
        self.frequency = frequency(self.prefix)
        self.period = period(self.prefix)
        self.temperature = temperature(self.prefix)
        self.resistance = resistance(self.prefix)
        self.fresistance = fresistance(self.prefix)
        self.totalize = totalize(self.prefix)


class system_date:
    # SYSTem:DATE <yyyy>,<mm>,<dd> / SYSTem:DATE?
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix
        self.req = req3(self.prefix)

    def conf(self, year, month, day):
        # NOTE: this module's own `class str:` shadows the builtin, so
        # zero-padding is done with an f-string format spec, not str().
        return f'{self.cmd} {year},{month:02d},{day:02d}'


class system_time:
    # SYSTem:TIME <hh>,<mm>,<ss.sss> / SYSTem:TIME? / SYSTem:TIME:SCAN?
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix
        self.req = req3(self.prefix)
        self.scan_req = req3(self.prefix + ":SCAN")

    def conf(self, hour, minute, second):
        return f'{self.cmd} {hour:02d},{minute:02d},{second:06.3f}'


class system:
    # SYSTem:ALARm? / :CPON <slot> / :CTYPe? <slot> / :DATE / :ERRor?
    # SYSTem:INTerface {GPIB|RS232} / :LANGuage / :LFRequency?
    # SYSTem:LOCal / :LOCK:* / :PRESet / :REMote / :RWLock / :TIME / :VERSion?
    #
    # Intentionally not implemented: SYSTem:SECurity[:IMMediate], which
    # irreversibly erases all instrument memory except calibration data and
    # reboots (see docs/scpi-driver-core.md), and the
    # SYSTem:COMMunicate:LAN:* subtree, which only applies to LAN-equipped
    # models and is out of scope for this RS232/USB-GPIB driver.
    def __init__(self):
        self.prefix = "SYST"
        self.cmd = "SYST"
        self.alarm = req3(self.prefix + ":ALAR")
        self.cpon = dig_param3(self.prefix + ":CPON", 1, 3)
        self.ctype = req3(self.prefix + ":CTYPe")
        self.date = system_date(self.prefix + ":DATE")
        self.error = req3(self.prefix + ":ERRor")
        self.interface = discrete_setting(self.prefix + ":INTerface")
        self.interface_gpib = str3(self.prefix + ":INTerface GPIB")
        self.interface_rs232 = str3(self.prefix + ":INTerface RS232")
        self.language = discrete_setting(self.prefix + ":LANGuage")
        self.lfrequency_req = req3(self.prefix + ":LFRequency")
        self.local = str3(self.prefix + ":LOCal")
        self.lock_name_req = req3(self.prefix + ":LOCK:NAME")
        self.lock_owner_req = req3(self.prefix + ":LOCK:OWNer")
        self.lock_release = str3(self.prefix + ":LOCK:RELease")
        self.lock_request_req = req3(self.prefix + ":LOCK:REQuest")
        self.preset = str3(self.prefix + ":PRESet")
        self.remote = str3(self.prefix + ":REMote")
        self.rwlock = str3(self.prefix + ":RWLock")
        self.time = system_time(self.prefix + ":TIME")
        self.version_req = req3(self.prefix + ":VERSion")



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
        # print("INIT Measure")
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
    # [SENSe:]FREQuency:VOLTage:RANGe:AU
    # Miscellaneous
    # [SENSe:]FUNCtion
    # [SENSe:]FUNCtion?
    # [SENSe:]ZERO:AUTO
    # [SENSe:]ZERO:AUTO?
    def __init__(self):
        # print("INIT Sense")
        self.cmd = "SENS"
        self.prefix = "SENS"
        self.current = current(self.prefix)
        self.voltage = voltage(self.prefix)
        self.digital_byte = digital_data(self.prefix)
        self.frequency = frequency(self.prefix)
        self.period = period(self.prefix)
        self.temperature = temperature(self.prefix)
        self.resistance = resistance(self.prefix)
        self.fresistance = fresistance(self.prefix)
        self.totalize = sense_totalize(self.prefix)
        self.func = sence_func(self.prefix)
        self.zero = zero(self.prefix)


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
        # print("INIT ROUTE")
        self.cmd = "ROUTe"
        self.prefix = "ROUTe"
        self.channel = route_channel(self.prefix)
        self.close = open_close_ch(self.prefix + ":CLOSe")
        self.close_exclusice = conf2(self.prefix + ":CLOSe" + ":EXCLusive ")
        self.done = req3(self.prefix + ":DONE")
        self.monitor = monitor(self.prefix)
        self.open = open_close_ch(self.prefix + ":OPEN")
        self.scan = scan(self.prefix)


# **********  UNIT:TEMPerature *************
class unit_temperature:
    def __init__(self):
        # print("INIT Read")
        self.prefix = "UNIT:TEMPerature"
        self.cmd = "UNIT:TEMPerature"
        self.req = req2(self.prefix)
        self.conf_f = conf2(self.prefix + " F,")
        self.conf_c = conf2(self.prefix + " C,")
        self.conf_k = conf2(self.prefix + " K,")


class req_on_off_ch_select:
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix
        self.req = req2(self.prefix)
        self.on = conf2(self.prefix + " ON,")
        self.off = conf2(self.prefix + " OFF,")



# part of ROUTE class
class scan:
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "SCAN"
        self.cmd = self.prefix
        self.conf = conf2(self.prefix + " ")
        self.req = req3(self.prefix)
        self.size = req3(self.prefix + ":" + "SIZE")



# part of ROUTE class
class open_close_ch:
    # This command opens the specified channels on a multiplexer or switch
    # module.
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix
        self.conf = conf2(self.prefix + " ")
        self.req = req2(self.prefix)



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
        self.conf = conf2(self.prefix + " ")
        self.req = req3(self.prefix)
        self.data = req3(self.prefix + ":" + "DATA")
        self.state_req = req3(self.prefix + ":" + "STATe")
        self.state_conf_on = str3(self.prefix + ":" + "STATe" + " ON")
        self.state_conf_off = str3(self.prefix + ":" + "STATe" + " OFF")

class route_channel:
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "CHANnel"
        self.cmd = self.prefix
        self.delay = channel_delay(self.prefix + ":DELay")
        self.fwire = req_on_off_ch_select(self.prefix + ":FWIRe")
        self.advance_source = trig_source(self.prefix + ":ADVance")

class channel_delay:
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "CHANnel"
        self.cmd = self.prefix
        self.conf = sel_ch_with_param(self.prefix + ":DELay", 0, 50)
        self.req = req2(self.prefix + ":DELay")
        self.auto = req_on_off_ch_select(self.prefix + ":DELay:AUTO")



class zero:
    # This queries the status of all relay operations on cards not involved in the
    # scan and returns a 1 when all relay operations are finished (even during
    # a scan). ONLY -> ROUTe:DONE?
    def __init__(self, prefix):
        # super(zero, self).__init__()
        self.prefix = prefix + ":" + "ZERO"
        self.cmd = self.prefix
        self.auto = req_on_off_ch_select(self.prefix + ":" + "AUTO")
        self.auto_once = conf2(self.prefix + ":" + "AUTO" + " ONCE,")


class sence_func:
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "FUNC"
        self.cmd = self.prefix
        self.req = req2(self.prefix)
        self.temperature = conf2(self.prefix + ' "TEMP",')
        self.volt_dc = conf2(self.prefix + ' "VOLT:DC",')
        self.volt_ac = conf2(self.prefix + ' "VOLT:AC",')
        self.resistance = conf2(self.prefix + ' "RES",')
        self.fresistance = conf2(self.prefix + ' "FRES",')
        self.current_dc = conf2(self.prefix + ' "CURR:DC",')
        self.current_ac = conf2(self.prefix + ' "CURR:AC",')
        self.frequency = conf2(self.prefix + ' "FREQ",')
        self.period = conf2(self.prefix + ' "PER",')


class voltage:
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "VOLT"
        self.ac = ac(self.prefix)
        self.dc = dc(self.prefix)
        if (self.prefix.find(":FREQuency:") != -1) or self.prefix.find(":PERiod:") != -1:
            self.Range = Range(self.prefix)


class current:
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "CURR"
        self.ac = ac(self.prefix)
        self.dc = dc(self.prefix)


class digital_byte:
    # This command configures the instrument to scan the specified digital
    # input channels on the multifunction module as byte data, but does not
    # initiate the scan. This command redefines the scan list.
    # The digital input channels are numbered "s01" (LSB) and "s02"
    # (MSB), where s is the first digit of the slot number.
    # example: CONF:DIG:BYTE (@101:102)
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "DIG:BYTE"
        self.cmd = self.prefix
        if self.prefix.find("CONFigure:") != -1:
            self.conf = conf2(self.prefix + " ")
        if self.prefix.find("MEASure:") != -1:
            self.req = req2(self.prefix)


class digital_data:
    # This command configures the instrument to scan the specified digital
    # input channels on the multifunction module as byte data, but does not
    # initiate the scan. This command redefines the scan list.
    # The digital input channels are numbered "s01" (LSB) and "s02"
    # (MSB), where s is the first digit of the slot number.
    # example: CONF:DIG:BYTE (@101:102)
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "DIGital:DATA:"
        self.cmd = self.prefix
        self.req_byte = req2(self.prefix + "BYTE")
        self.req_word = req2(self.prefix + "WORD")
        if self.prefix.find("SOURce:") != -1:
            self.conf_byte = sel_ch_with_param(self.prefix + "BYTE", 0, 255)
            self.conf_word = sel_ch_with_param(self.prefix + "WORD", 0, 65535)



class frequency(select_channel):
    # These commands configure the channels for frequency or period
    # measurements, but they do not initiate the scan.
    # The CONFigure command does not place the instrument in the "wait-fortrigger"
    # state. Use the INITiate or READ? command in conjunction with
    # CONFigure to place the instrument in the "wait-for-trigger" state.
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "FREQuency"
        self.cmd = self.prefix
        if self.prefix.find("CONFigure:") != -1:
            self.conf = conf2(self.prefix + " ")
        if self.prefix.find("MEASure:") != -1:
            self.req = req2(self.prefix)
        if self.prefix.find("SENS:") != -1:
            self.Range_lower_req = req2(self.prefix + ":RANGe:LOWer")
            self.Range_lower_conf = conf2(self.prefix + ":RANGe:LOWer")
            self.Volt_range_req = req2(self.prefix + ":VOLTage:RANGe")
            self.Volt_range_conf = conf2(self.prefix + ":VOLTage:RANGe")
            self.Volt_range_auto = req_on_off_ch_select(self.prefix + ":VOLTage:RANGe:AUTO")
            self.Aperture = Aperture(self.prefix)


class period(select_channel):
    # These commands configure the channels for frequency or period
    # measurements, but they do not initiate the scan.
    # The CONFigure command does not place the instrument in the "wait-fortrigger"
    # state. Use the INITiate or READ? command in conjunction with
    # CONFigure to place the instrument in the "wait-for-trigger" state.
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "PERiod"
        self.cmd = self.prefix
        if self.prefix.find("CONFigure:") != -1:
            self.conf = conf2(self.prefix + " ")
        if self.prefix.find("MEASure:") != -1:
            self.req = req2(self.prefix)
        if self.prefix.find("SENS:") != -1:
            self.Volt_range_req = req2(self.prefix + ":VOLTage:RANGe")
            self.Volt_range_conf = conf2(self.prefix + ":VOLTage:RANGe")
            self.Volt_range_auto = req_on_off_ch_select(self.prefix + ":VOLTage:RANGe:AUTO")
            self.Aperture = Aperture(self.prefix)


class temperature_conf:
    # CONFigure:TEMPerature / MEASure:TEMPerature? both require a probe_type
    # and sensor_type ahead of the channel list, unlike every other
    # CONFigure/MEASure function in this driver:
    #   CONFigure:TEMPerature {<probe_type>|DEF},{<type>|DEF},(@<scan_list>)
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix

    def list(self, probe_type="DEF", sensor_type="DEF", *argv):
        ch_list_txt = ch_list_from_list2(*argv)
        return f'{self.cmd} {probe_type},{sensor_type},{ch_list_txt}'

    def range(self, probe_type, sensor_type, ch_min, ch_max, ch_num=20):
        ch_list_txt = ch_list_from_range2(ch_min, ch_max, ch_num)
        return f'{self.cmd} {probe_type},{sensor_type},{ch_list_txt}'


class temperature(select_channel):
    # These commands configure the channels for temperature measurements
    # but do not initiate the scan. If you omit the optional <ch_list> parameter,
    # this command applies to the currently defined scan list.
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "TEMPerature"
        self.cmd = self.prefix
        if self.prefix.find("CONFigure:") != -1:
            self.conf = temperature_conf(self.prefix)
        if self.prefix.find("MEASure:") != -1:
            self.req = temperature_conf(self.prefix + "?")
        if self.prefix.find("SENS:") != -1:
            self.rjunction = req2(self.prefix + ":" + "RJUNction")
            self.transducer = transduser(self.prefix)
            self.Aperture = Aperture(self.prefix)
            self.NPLC = NPLC(self.prefix)


class resistance(select_channel):
    # These commands configure the channels for 2-wire (RESistance)
    # resistance measurements but do not initiate the scan.
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "RESistance"
        self.cmd = self.prefix
        self.prefix = self.cmd
        if self.prefix.find("CONFigure:") != -1:
            self.conf = conf2(self.prefix + " ")
        if self.prefix.find("MEASure:") != -1:
            self.req = req2(self.prefix)
        if self.prefix.find("SENS:") != -1:
            # No Bandwidth parameter for [SENSe:]RESistance (that only
            # applies to the AC current/voltage functions).
            self.Range = Range(self.prefix)
            self.Resolution = Resolution(self.prefix)
            self.Aperture = Aperture(self.prefix)
            self.NPLC = NPLC(self.prefix)
            self.Ocompensated = Ocompensated(self.prefix)


class fresistance(select_channel):
    # These commands configure the channels for  4-wire (FRESistance) resistance
    # measurements but do not initiate the scan.
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "FRESistance"
        self.cmd = self.prefix
        self.prefix = self.cmd
        if self.prefix.find("CONFigure:") != -1:
            self.conf = conf2(self.prefix + " ")
        if self.prefix.find("MEASure:") != -1:
            self.req = req2(self.prefix)
        if self.prefix.find("SENS:") != -1:
            # No Bandwidth parameter for [SENSe:]FRESistance either.
            self.Range = Range(self.prefix)
            self.Resolution = Resolution(self.prefix)
            self.Aperture = Aperture(self.prefix)
            self.NPLC = NPLC(self.prefix)
            self.Ocompensated = Ocompensated(self.prefix)


class totalize:
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
        if self.prefix.find("CONFigure:") != -1:
            self.conf_read = conf2(self.prefix + " READ,")
            self.conf_rres = conf2(self.prefix + " RRES,")
        # probably it will be better to use conf2 class
        if self.prefix.find("MEASure:") != -1:
            self.req_read = conf2(self.prefix + "?" + " READ,")
            self.req_rres = conf2(self.prefix + "?" + " RRES,")


class sense_totalize:
    # [SENSe:]TOTalize:* — a distinct command tree from CONFigure/
    # MEASure:TOTalize's READ/RRESet mode selector above; this one drives the
    # 34907A's hardware totalizer channel directly.
    #   [SENSe:]TOTalize:CLEar:IMMediate [(@<ch_list>)]
    #   [SENSe:]TOTalize:DATA? [(@<ch_list>)]
    #   [SENSe:]TOTalize:SLOPe {NEGative|POSitive}[,(@<ch_list>)]
    #   [SENSe:]TOTalize:STARt[:IMMediate] [(@<ch_list>)]
    #   [SENSe:]TOTalize:STOP[:IMMediate] [(@<ch_list>)]
    #   [SENSe:]TOTalize:TYPE {READ|RRESet}[,(@<ch_list>)]
    def __init__(self, prefix):
        self.prefix = prefix + ":" + "TOTalize"
        self.cmd = self.prefix
        self.clear_immediate = conf2(self.prefix + ":CLEar:IMMediate ")
        self.data_req = req2(self.prefix + ":DATA")
        self.slope = sel_ch_with_value(self.prefix + ":SLOPe")
        self.slope_req = req2(self.prefix + ":SLOPe")
        self.start_immediate = conf2(self.prefix + ":STARt:IMMediate ")
        self.stop_immediate = conf2(self.prefix + ":STOP:IMMediate ")
        self.type = sel_ch_with_value(self.prefix + ":TYPE")
        self.type_req = req2(self.prefix + ":TYPE")


class ac(select_channel):
    # [SENSe:]CURRent:AC has a Resolution parameter; [SENSe:]VOLTage:AC does
    # not (see the 34970A/72A Command Reference SENSe Subsystem summary).
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "AC"
        self.prefix = self.cmd
        if self.prefix.find("CONFigure:") != -1:
            self.conf = conf2(self.prefix + " ")
        if self.prefix.find("MEASure:") != -1:
            self.req = req2(self.prefix)
        if self.prefix.find("SENS:") != -1:
            self.Bandwidth = Bandwidth(self.prefix)
            self.Range = Range(self.prefix)
            if self.prefix.find("CURR") != -1:
                self.Resolution = Resolution(self.prefix)


class dc(select_channel):
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "DC"
        self.prefix = self.cmd
        if self.prefix.find("CONFigure:") != -1:
            self.conf = conf2(self.prefix + " ")
        if self.prefix.find("MEASure:") != -1:
            self.req = req2(self.prefix)
        if self.prefix.find("SENS:") != -1:
            self.Range = Range(self.prefix)
            self.Resolution = Resolution(self.prefix)
            self.Aperture = Aperture(self.prefix)
            self.NPLC = NPLC(self.prefix)


class Bandwidth:
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "BANDwidth"
        self.prefix = self.cmd
        self.conf_3 = conf2(self.prefix + " 3,")
        self.conf_20 = conf2(self.prefix + " 20,")
        self.conf_200 = conf2(self.prefix + " 200,")
        self.req = req2(self.prefix)


class Range(str_return):
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "RANGe"
        self.prefix = self.cmd
        self.auto = req_on_off_ch_select(self.prefix + ":AUTO")
        self.conf = conf2(self.prefix + " ")
        self.conf_100mV = conf2(self.prefix + " 100 mV,")
        self.conf_1V = conf2(self.prefix + " 1V,")
        self.conf_10V = conf2(self.prefix + " 10V,")
        self.conf_100V = conf2(self.prefix + " 100V,")
        self.conf_300V = conf2(self.prefix + " 300V,")
        self.req = req2(self.prefix)
        self.conf_min = conf2(self.prefix + " MIN,")
        self.conf_max = conf2(self.prefix + " MAX,")


class Resolution:
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "RESolution"
        self.prefix = self.cmd
        self.conf = sel_ch_with_param(self.prefix, 0, 65535)
        self.req = req2(self.prefix)


class Aperture(str_return):
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "APERture"
        self.prefix = self.cmd
        self.req = req2(self.prefix)
        self.conf_sec = sel_ch_with_param(self.prefix, 0.000004, 1)
        self.conf_min = conf2(self.prefix + " 400E-6,")
        self.conf_10ms = conf2(self.prefix + " 10E-3,")
        self.conf_100ms = conf2(self.prefix + " 100E-3,")
        self.conf_500ms = conf2(self.prefix + " 500E-3,")
        self.conf_max = conf2(self.prefix + " 1,")


class NPLC(str_return):
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "NPLC"
        self.prefix = self.cmd
        self.conf = conf2(self.prefix + " ")
        self.req = req2(self.prefix)
        self.conf_min = conf2(self.prefix + " 0.02,")
        self.conf_02 = conf2(self.prefix + " 0.2,")
        self.conf_1 = conf2(self.prefix + " 1,")
        self.conf_2 = conf2(self.prefix + " 2,")
        self.conf_10 = conf2(self.prefix + " 10,")
        self.conf_20 = conf2(self.prefix + " 20,")
        self.conf_100 = conf2(self.prefix + " 100,")
        self.conf_max = conf2(self.prefix + " 200,")


class Ocompensated:
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "OCOMpensated"
        self.prefix = self.cmd
        self.conf_on = conf2(self.prefix + " ON,")
        self.conf_off = conf2(self.prefix + " OFF,")
        self.req = req2(self.prefix)


class transduser:
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "TRANsducer"
        self.prefix = self.cmd
        self.rtd = rtd(self.prefix)
        self.frtd = frtd(self.prefix)
        self.tcouple = tcouple(self.prefix)
        self.thermistor = thermistor(self.prefix)


class rtd:
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "RTD"
        self.prefix = self.cmd
        self.Ocompensated = Ocompensated(self.prefix)
        self.type = rtd_type(self.prefix)
        self.resistance = resistance_ref(self.prefix)


class frtd:
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "FRTD"
        self.prefix = self.cmd
        self.Ocompensated = Ocompensated(self.prefix)
        self.type = rtd_type(self.prefix)
        self.resistance = resistance_ref(self.prefix)


class rtd_type:
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "TYPE"
        self.prefix = self.cmd
        self.conf_85 = conf2(self.prefix + " 85,")
        self.conf_91 = conf2(self.prefix + " 91,")
        self.req = req2(self.prefix)


class resistance_ref:
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "RESistance:REFerence"
        self.prefix = self.cmd
        self.conf_49 = conf2(self.prefix + " 49,")
        self.conf_2100 = conf2(self.prefix + " 2100,")
        self.req = req2(self.prefix)


class tcouple:
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "TCouple"
        self.prefix = self.cmd
        self.check = tcouple_check(self.prefix)
        self.rjunction = tcouple_rjunction(self.prefix)
        self.type = tcouple_type(self.prefix)


class tcouple_check:
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "CHECk"
        self.prefix = self.cmd
        self.conf_on = conf2(self.prefix + " ON,")
        self.conf_off = conf2(self.prefix + " OFF,")
        self.req = req2(self.prefix)


class tcouple_rjunction:
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "RJUNction"
        self.prefix = self.cmd
        self.req = req2(self.prefix)
        self.conf_m20C = conf2(self.prefix + " -20,")
        self.conf_80C = conf2(self.prefix + " 80,")
        self.type = junction_type(self.prefix)


class junction_type:
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "TYPE"
        self.prefix = self.cmd
        self.req = req2(self.prefix)
        self.conf_internal = conf2(self.prefix + " INTernal,")
        self.conf_external = conf2(self.prefix + " EXTernal,")
        self.conf_fixed = conf2(self.prefix + " FIXed,")


class tcouple_type:
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "TYPE"
        self.prefix = self.cmd
        self.req = req2(self.prefix)
        self.conf_B = conf2(self.prefix + " B,")
        self.conf_E = conf2(self.prefix + " E,")
        self.conf_J = conf2(self.prefix + " J,")
        self.conf_K = conf2(self.prefix + " K,")
        self.conf_N = conf2(self.prefix + " N,")
        self.conf_R = conf2(self.prefix + " R,")
        self.conf_S = conf2(self.prefix + " S,")
        self.conf_T = conf2(self.prefix + " T,")


class thermistor:
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + ":THERmistor:TYPE"
        self.prefix = self.cmd
        self.req = req2(self.prefix)
        self.conf_type_2252 = conf2(self.prefix + " 2252,")
        self.conf_type_5000 = conf2(self.prefix + " 5000,")
        self.conf_type_10000 = conf2(self.prefix + " 10000,")


class trigger:
    # TRIGger:COUNt
    # TRIGger:COUNt?
    # TRIGger:SOURce
    # TRIGger:SOURce?
    # TRIGger:TIMer
    # TRIGger:TIMer?
    def __init__(self):
        # print("INIT Trigger")
        self.cmd = "TRIGger"
        self.prefix = "TRIGger"
        self.count = trig_count(self.prefix)
        self.source = trig_source(self.prefix)
        self.timer = trig_timer(self.prefix)


class trig_count(dig_param):
    # This command specifies the number of times to sweep through the scan
    # list. A sweep is one pass through the scan list. The scan stops when the
    # number of specified sweeps has occurred.
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "COUNt"
        self.prefix = self.cmd
        self.req = req2(self.prefix)
        self.min = 0
        self.max = 500000


class trig_source:
    # Select the trigger source to control the onset of each sweep through the
    # scan list (a sweep is one pass through the scan list). The instrument will
    # accept a software (bus) command, an immediate (continuous) scan
    # trigger, an external TTL trigger pulse, an alarm-initiated action, or an
    # internally paced timer.
    # IMMediate=Continuous scan trigger
    # BUS =Software trigger
    # EXTernal =An external TTL pulse trigger
    # ALARm = Trigger on an alarm
    # TIMer =Internally paced timer trigger
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "SOURce"
        self.prefix = self.cmd
        self.req = req2(self.prefix)
        self.bus = str3(self.prefix + " BUS")
        self.immediate = str3(self.prefix + " IMMediate")
        self.external = str3(self.prefix + " EXTernal")
        if self.prefix.find("TRIGger:") != -1:
            self.alarm1 = str3(self.prefix + " ALARm1")
            self.alarm2 = str3(self.prefix + " ALARm2")
            self.alarm3 = str3(self.prefix + " ALARm3")
            self.alarm4 = str3(self.prefix + " ALARm4")
            self.timer = str3(self.prefix + " TIMer")


class trig_timer(dig_param):
    # This command sets the trigger-to-trigger interval (in seconds) for
    # measurements on the channels in the present scan list. This command
    # defines the time from the start of one trigger to the start of the next
    # trigger, up to the specified trigger count (see TRIGger:COUNt
    # command).
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "TIMer"
        self.prefix = self.cmd
        self.req = req2(self.prefix)
        self.min = 0
        self.max = 0.359999

class source:
    # SOURce:DIGital:DATA[:{BYTE|WORD}]
    # SOURce:DIGital:DATA[:{BYTE|WORD}]?
    # This command outputs a digital pattern as an 8-bit byte or 16-bit word to
    # the specified digital output channels.
    #
    # SOURce:DIGital:STATe?
    # This command returns the status (input or output) of the specified digital
    # channels.
    #
    # SOURce:VOLTage
    # SOURce:VOLTage?
    def __init__(self):
        # print("INIT SOURce")
        self.cmd = "SOURce"
        self.prefix = "SOURce"
        self.digital_data = digital_data(self.prefix)
        self.digital_state_req = req2(self.prefix + ":DIGital:STATe")
        self.voltage = source_voltage(self.prefix)


class source_voltage:
    # This command sets the output voltage level for the specified DAC
    # channels on the 34907A Multifunction Module.
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix + ":" + "VOLTage"
        self.prefix = self.cmd
        self.min = -12
        self.max = 12
        self.req = req2(self.prefix)
        self.conf = sel_ch_with_param(self.prefix, self.min, self.max)

class status:
    # *ESE
    # *ESE?
    # *ESR?
    # *SRE
    # *STB?
    # STATus:ALARm:CONDition?
    # STATus:ALARm:ENABle
    # STATus:ALARm:ENABle?
    # STATus:ALARm[:EVENt]?
    # STATus:OPERation:CONDition?
    # STATus:OPERation:ENABle
    # STATus:OPERation:ENABle?
    # STATus:OPERation[:EVENt]?
    # STATus:PRESet
    # STATus:QUEStionable:CONDition?
    # STATus:QUEStionable:ENABle
    # STATus:QUEStionable:ENABle?
    # STATus:QUEStionable[:EVENt]?
    def __init__(self):
        # print("INIT Status")
        self.cmd = "STATus"
        self.prefix = "STATus"
        self.ese = str_and_req("*ESE")
        self.esr = req3("*ESR")
        self.sre = str3("*SRE")
        self.stb = req3("*STB")
        self.preset = str3(self.prefix + ":" + "PRESet")
        self.alarm = st_com(self.prefix + ":" + "ALARm" )
        self.operation = st_com(self.prefix + ":" + "OPERation" )
        self.questionable = st_com(self.prefix + ":" + "QUEStionable")

class st_com:
    # This command sets the output voltage level for the specified DAC
    # channels on the 34907A Multifunction Module.
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix
        self.prefix = self.cmd
        self.condition = req3(self.prefix + ":" + "CONDition")
        self.enable_conf = dig_param3(self.prefix + ":ENABle", 0, 65535)
        self.enable_req = req3(self.prefix + ":ENABle")
        self.event = req3(self.prefix + ":" + "EVENt")



if __name__ == '__main__':
    # dev = LOG_34970A()
    # dev.init("COM10")
    # dev.send("COM10 send")
    cmd = storage()
    print("")
    print("TOP LEVEL")
    print("*" * 150)
    print(cmd.abort.str())
    print(cmd.fetch.req())
    print(cmd.r.val(100))
    print(cmd.init.str())

    print(cmd.read.req())
    # print(cmd.read.ch.range(102, 105))

    print(cmd.r.val(1000))

    print(cmd.unit_temperature.req.str())
    print(cmd.unit_temperature.req.ch.range(102, 110))
    print(cmd.unit_temperature.conf_c.ch.range(110, 115))
    print(cmd.unit_temperature.conf_f.ch.range(110, 115))
    print(cmd.unit_temperature.conf_k.ch.range(110, 115))

    print(cmd.input_impedance_auto.req.str())
    print(cmd.input_impedance_auto.req.ch.range(109, 112))
    print(cmd.input_impedance_auto.on.ch.range(101, 108))
    print(cmd.input_impedance_auto.off.ch.list(101, 108))

    print("")
    print("Configure")
    print("*" * 150)
    print(cmd.configure.req())

    # NOTE: these used to be commented out because cmd.configure.*.conf
    # never existed (see the fix for configure.prefix near its class
    # definition, and docs/scpi-driver-core.md).
    print(cmd.configure.voltage.ac.conf.ch.range(101, 108))
    print(cmd.configure.voltage.dc.conf.ch.range(101, 108))

    print(cmd.configure.current.ac.conf.ch.range(101, 108))
    print(cmd.configure.current.dc.conf.ch.range(101, 108))

    print(cmd.configure.digital_byte.conf.ch.range(101, 110))

    print(cmd.configure.resistance.conf.ch.range(101, 107))
    print(cmd.configure.fresistance.conf.ch.range(101, 107))

    print(cmd.configure.frequency.conf.ch.range(101, 110))
    print(cmd.configure.period.conf.ch.range(101, 110))

    print(cmd.configure.temperature.conf.range("DEF", "DEF", 101, 110))
    print(cmd.configure.totalize.conf_read.ch.range(101, 110))

    print("")
    print("MEASURE")
    print("*" * 150)
    print(cmd.measure.voltage.ac.req.ch.range(109, 115))
    print(cmd.measure.voltage.dc.req.ch.range(109, 115))
    print(cmd.measure.current.dc.req.ch.range(109, 115))
    print(cmd.measure.digital_byte.req.ch.range(101, 120))
    print(cmd.measure.frequency.req.ch.range(101, 120))
    print(cmd.measure.period.req.ch.range(101, 120))
    print(cmd.measure.temperature.req.range("DEF", "DEF", 101, 120))
    print(cmd.measure.totalize.req_read.ch.range(101, 120))
    print(cmd.measure.totalize.req_rres.ch.range(101, 120))
    print(cmd.measure.resistance.req.ch.range(101, 120))
    print(cmd.measure.fresistance.req.ch.range(101, 120))

    print("")
    print("sense")
    print("*" * 150)
    print(cmd.sense.voltage.dc.NPLC.conf_10.ch.range(101, 103))
    # print(cmd.sense.current.ac.Bandwidth.conf_200.ch.list(102, 105))
    # print(cmd.sense.current.ac.Bandwidth.conf_3.ch.list(101))
    print(cmd.sense.current.ac.Range.req.ch.range(102, 105))
    print(cmd.sense.current.ac.Range.auto.req.ch.range(102, 105))
    print(cmd.sense.current.ac.Range.auto.off.ch.range(102, 105))
    print(cmd.sense.current.ac.Resolution.conf.range(100,101,105))
    print(cmd.sense.current.ac.Bandwidth.req.ch.range(102, 105))
    print(cmd.sense.current.dc.NPLC.conf_10.ch.range(101, 103))
    print(cmd.sense.current.dc.Aperture.conf_sec.range(0.5, 101, 104))

    print(cmd.sense.current.ac.Range.req.ch.range(102, 105))
    print(cmd.sense.current.ac.Range.auto.req.ch.range(102, 105))
    print(cmd.sense.current.ac.Resolution.conf.range(100, 101, 105))
    print(cmd.sense.current.ac.Bandwidth.req.ch.range(102, 105))

    print(cmd.sense.digital_byte.req_byte.ch.range(101, 105))
    print(cmd.sense.digital_byte.req_word.ch.range(101, 105))

    print(cmd.sense.frequency.Volt_range_auto.off.ch.list(101))

    print(cmd.sense.zero.auto.off.ch.list(102))
    print(cmd.sense.func.req.ch.list(120))
    print(cmd.sense.func.temperature.ch.range(101, 104))
    print(cmd.sense.temperature.rjunction.ch.range(101, 105))
    print(cmd.sense.temperature.transducer.rtd.type.conf_85.ch.range(103, 108))
    print(cmd.sense.temperature.transducer.frtd.type.conf_91.ch.range(103, 108))
    print(cmd.sense.temperature.transducer.rtd.resistance.conf_49.ch.list(101))
    print(cmd.sense.temperature.transducer.tcouple.type.conf_K.ch.list(102, 110))
    print(cmd.sense.temperature.transducer.thermistor.conf_type_5000.ch.list(120))

    print("")
    print("TRIGER")
    print("*" * 150)
    print(cmd.trigger.timer.val(0.001))
    print(cmd.trigger.count.val(100))
    print(cmd.trigger.source.alarm1.str())
    print(cmd.trigger.source.timer.str())

    print("")
    print("SOURCE")
    print("*" * 150)
    print(cmd.source.voltage.req.ch.list(102))
    print(cmd.source.voltage.conf.list(10, 101, 102))
    print(cmd.source.voltage.conf.range(8.000, 101, 115))
    print(cmd.source.digital_state_req.ch.range(101, 102))
    print(cmd.source.digital_data.conf_byte.list(100, 101))
    print(cmd.source.digital_data.conf_word.range(65540, 101, 110))

    print("")
    print("STATUS")
    print("*" * 150)
    print(cmd.status.ese.req())
    print(cmd.status.ese.str())
    print(cmd.status.sre.str())
    print(cmd.status.alarm.condition.req())
    print(cmd.status.alarm.enable_conf.val(10))
    print(cmd.status.alarm.enable_req.req())
    print(cmd.status.operation.enable_conf.val(100))
    print(cmd.status.questionable.condition.req())

    print("")
    print("ROUTE")
    print("*" * 150)
    print(cmd.route.scan.req.req())
    print(cmd.route.scan.conf.ch.range(101,105))
    print(cmd.route.scan.size.req())
    print(cmd.route.open.conf.ch.list(102))
    print(cmd.route.open.req.ch.range(102, 108))
    print(cmd.route.close.conf.ch.list(102))
    print(cmd.route.close.req.ch.range(102, 108))
    print(cmd.route.close_exclusice.ch.list(102))
    print(cmd.route.monitor.req.req())
    print(cmd.route.monitor.conf.ch.range(104, 108))
    print(cmd.route.monitor.data.req())
    print(cmd.route.monitor.state_conf_on.str())
    print(cmd.route.done.req())
    print(cmd.route.channel.delay.conf.list(10,101))
    print(cmd.route.channel.delay.req.ch.range(102,106))
    print(cmd.route.channel.delay.auto.req.ch.list(104))
    print(cmd.route.channel.delay.auto.on.ch.list(110))
    print(cmd.route.channel.delay.auto.off.ch.list(104))
    print(cmd.route.channel.fwire.on.ch.list(103))
    print(cmd.route.channel.fwire.req.ch.list(102))
    print(cmd.route.channel.advance_source.bus.str())
    print(cmd.route.channel.advance_source.external.str())

    print("")
    print("SENSE: TOTALIZE / PERIOD / TEMPERATURE additions")
    print("*" * 150)
    print(cmd.sense.totalize.clear_immediate.ch.list(107))
    print(cmd.sense.totalize.data_req.ch.list(107))
    print(cmd.sense.totalize.slope.list("POSitive", 107))
    print(cmd.sense.totalize.start_immediate.ch.list(107))
    print(cmd.sense.totalize.type.list("RRES", 107))
    print(cmd.sense.period.Aperture.req.ch.range(101, 102))
    print(cmd.sense.period.Volt_range_auto.off.ch.list(101))
    print(cmd.sense.temperature.Aperture.conf_min.ch.list(101))
    print(cmd.sense.temperature.NPLC.conf_10.ch.list(101))

    print("")
    print("DATA / DISPlay / FORMat:READing")
    print("*" * 150)
    print(cmd.data.last.req(310, 5))
    print(cmd.data.points_req.req())
    print(cmd.data.points_event_threshold.val(1000))
    print(cmd.data.remove.req(50))
    print(cmd.display.text.conf("WAITING..."))
    print(cmd.display.text.clear.str())
    print(cmd.fformat.alarm.on())
    print(cmd.fformat.time_type.absolute.str())

    print("")
    print("MEMory / OUTPut / CALCulate")
    print("*" * 150)
    print(cmd.memory.nstates_req.req())
    print(cmd.memory.state_name.conf(1, "bench setup"))
    print(cmd.memory.state_recall_auto.on())
    print(cmd.output.mode_latch.str())
    print(cmd.output.alarm1.source.ch.range(101, 105))
    print(cmd.calculate.limit.upper.list("50", 101))
    print(cmd.calculate.limit.upper_state.on.ch.list(101))
    print(cmd.calculate.scale.gain.list("2", 101))

    print("")
    print("SYSTem / IEEE-488.2 additions")
    print("*" * 150)
    print(cmd.system.date.conf(2026, 9, 30))
    print(cmd.system.time.conf(14, 5, 1.123))
    print(cmd.system.version_req.req())
    print(cmd.system.preset.str())
    print(cmd.cls.str())
    print(cmd.opc_req.req())
    print(cmd.trg.str())


