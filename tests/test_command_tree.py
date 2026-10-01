"""Coverage/correctness checks for LOG34970A_v2's SCPI command-builder tree.

These don't touch any transport; they just assert on the generated command
strings, cross-checked against the Agilent/Keysight 34970A/72A Command
Reference. See docs/scpi-driver-core.md "SCPI command coverage" for the full
comparison against the Robot Framework driver and the bugs found here.
"""

import LOG34970A.LOG34970A_v2 as m


def test_configure_conf_is_reachable_for_every_function():
    # Regression test: configure.prefix used to be the short form "CONF",
    # which meant no CONFigure:*.conf ever existed (every child class gates
    # on the long-form substring "CONFigure:").
    cmd = m.storage()
    assert cmd.configure.current.ac.conf.ch.list(101) == "CONFigure:CURR:AC (@101)"
    assert cmd.configure.voltage.dc.conf.ch.list(101) == "CONFigure:VOLT:DC (@101)"
    assert cmd.configure.resistance.conf.ch.list(101) == "CONFigure:RESistance (@101)"
    # the bare query still uses the short form, which is equally valid SCPI
    assert cmd.configure.req() == "CONF?"


def test_ac_voltage_has_no_resolution_parameter():
    # [SENSe:]VOLTage:AC has no RESolution parameter on real hardware, only
    # [SENSe:]CURRent:AC does.
    cmd = m.storage()
    assert not hasattr(cmd.sense.voltage.ac, "Resolution")
    assert hasattr(cmd.sense.current.ac, "Resolution")


def test_resistance_functions_have_no_bandwidth_parameter():
    cmd = m.storage()
    assert not hasattr(cmd.sense.resistance, "Bandwidth")
    assert not hasattr(cmd.sense.fresistance, "Bandwidth")


def test_frequency_has_no_bogus_nested_voltage_tree():
    cmd = m.storage()
    assert not hasattr(cmd.sense.frequency, "voltage")
    assert (
        cmd.sense.frequency.Volt_range_auto.on.ch.list(101)
        == "SENS:FREQuency:VOLTage:RANGe:AUTO ON,(@101)"
    )


def test_temperature_configure_and_measure_include_required_params():
    cmd = m.storage()
    assert (
        cmd.configure.temperature.conf.list("DEF", "DEF", 101)
        == "CONFigure:TEMPerature DEF,DEF,(@101)"
    )
    assert (
        cmd.measure.temperature.req.list("TCouple", "J", 101)
        == "MEASure:TEMPerature? TCouple,J,(@101)"
    )


def test_sense_totalize_is_wired_up():
    # sense.totalize used to silently reuse a class gated on "CONFigure:"/
    # "MEASure:" prefixes, neither of which matches "SENS:", leaving it with
    # no usable attributes at all.
    cmd = m.storage()
    assert cmd.sense.totalize.data_req.ch.list(107) == "SENS:TOTalize:DATA? (@107)"
    assert (
        cmd.sense.totalize.slope.list("POSitive", 107)
        == "SENS:TOTalize:SLOPe POSitive,(@107)"
    )


def test_new_subsystems_are_present():
    cmd = m.storage()
    assert cmd.data.points_req.req() == "DATA:POINts?"
    assert cmd.display.on.str() == "DISPlay ON"
    assert cmd.fformat.alarm.on() == "FORMat:READing:ALARm ON"
    assert cmd.memory.nstates_req.req() == "MEMory:NSTates?"
    assert cmd.output.mode_latch.str() == "OUTPut:ALARm:MODE LATCh"
    assert cmd.calculate.scale.gain.list("2", 101) == "CALCulate:SCALe:GAIN 2,(@101)"
    assert cmd.system.version_req.req() == "SYST:VERSion?"
    assert cmd.cls.str() == "*CLS"
    assert cmd.wai.str() == "*WAI"
