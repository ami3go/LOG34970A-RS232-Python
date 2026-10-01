"""Scan-and-log example that exercises most of the command tree.

Connects over RS232 (swap to log.connect_usb() for the USB-GPIB path), puts
a status message on the front panel, configures a voltage scan, logs a
handful of readings, and along the way touches the DATA, MEMory, and
CALCulate subsystems added to the command tree. See
docs/scpi-driver-core.md "SCPI command coverage" for what each of these maps
to in the official command reference.

Requires real hardware connected on the given COM port; this is not part of
the automated test suite (see tests/ for that).
"""

import time

import LOG34970A.LOG34970A_v2 as logger_class

log = logger_class.LOG34970A()
cmd = logger_class.storage()
channels = [101, 108]

log.connect_serial("COM11")

# DISPlay: put a status message on the front panel while we configure.
log.send(cmd.display.text.conf("CONFIGURING..."))

log.send(cmd.reset.str())
log.send(cmd.route.scan.conf.ch.range(channels[0], channels[1]))
log.send(cmd.sense.voltage.dc.NPLC.conf_10.ch.range(channels[0], channels[1]))
log.send(cmd.sense.voltage.dc.Range.conf_10V.ch.range(channels[0], channels[1]))

# CALCulate: flag any reading on channel 101 above 5V as out of limits.
log.send(cmd.calculate.limit.upper.list("5", 101))
log.send(cmd.calculate.limit.upper_state.on.ch.list(101))

# FORMat:READing: include the channel number with every reading.
log.send(cmd.fformat.channel.on())

# MEMory: save this configuration to state slot 1 so it survives a power cycle.
log.send(cmd.memory.state_name.conf(1, "voltage scan"))

log.send(cmd.display.text.clear.str())

for i in range(5):
    log.send(cmd.init.str())
    time.sleep(1)
    readings = log.query(cmd.fetch.req())
    print(f"scan {i}: {readings}")

# DATA: how many readings are sitting in reading memory right now.
print("readings in memory:", log.query(cmd.data.points_req.req()))

log.close()
