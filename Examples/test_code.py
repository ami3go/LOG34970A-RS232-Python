# import pyvisa # PyVisa info @ http://PyVisa.readthedocs.io/en/stable/
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


def ch_list_from_range(is_req, min, max, add_space=1, channels_num=20):
    channels_34901A = 20  # 34901A 20 Channel Multiplexer (2/4-wire) Module
    channels_34902A = 16  # 34902A 16 Channel Multiplexer (2/4-wire) Module
    channels_34902A = 40  # 34908A 40 Channel Single-Ended Multiplexer Module
    req_txt = "?" if is_req == 1 else ""
    space_txt = " " if add_space == 1 else ""
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
    txt = f"{req_txt}{space_txt}(@{txt})"
    return txt


def ch_list_from_list(is_req, *argv):
    req_txt = "?" if is_req == 1 else ""
    txt = ""
    for items in argv:
        txt = f'{txt}{items},'
    txt = txt[:-1]
    txt = f'{req_txt} (@{txt})'
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
        # print(f'Sending: {txt}')
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

    def ch_list(self, is_req, *argv):
        ch_list_txt = ch_list_from_list(is_req, *argv)
        txt = f'{self.cmd}{ch_list_txt}'
        return txt

    def ch_range(self, is_req, min, max, channels_num=20):
        ch_list_txt = ch_list_from_range(is_req, min, max, channels_num)
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
        print("INIT req2")
        self.prefix = prefix + "?"
        self.cmd = self.prefix
        self.ch = select_channel(self.prefix)
        print(f"req2: {self.prefix}")

class conf2(str):
    def __init__(self, prefix):
        print("INIT conf2")
        self.prefix = prefix + " "
        self.cmd = self.prefix
        self.ch = select_channel(self.prefix)
        print(f"req2: {self.prefix}")



class select_channel():
    def __init__(self, prefix):
        self.prefix = prefix
        self.cmd = self.prefix

    def list(self, *argv):
        ch_list_txt = ch_list_from_list(0, *argv)
        txt = f'{self.cmd}{ch_list_txt}'
        return txt

    def range(self, min, max, channels_num=20):
        ch_list_txt = ch_list_from_range(0, min, max, channels_num)
        txt = f"{self.cmd}{ch_list_txt}"
        return txt


class storage():
    def __init__(self):
        print("init storage")
        # super(storage, self).__init__()
        self.cmd = None
        self.prefix = None
        self.read = read()
        print(f"storage: {self.prefix}")







# **********  READ *************
class read():
    def __init__(self):
        #super(read, self).__init__()
        print("INIT Read")
        self.prefix = "READ"
        self.cmd = "READ"
        self.req = req2(self.prefix)
        self.conf = conf2(self.prefix)
        print(f"read: {self.prefix}")



if __name__ == '__main__':
    # dev = LOG_34970A()
    # dev.init("COM10")
    # dev.send("COM10 send")
    cmd = storage()
    print(cmd.read.req.str())
    print(cmd.read.req.ch.list(102, 103))
    print(cmd.read.conf.ch.range(103, 108))
