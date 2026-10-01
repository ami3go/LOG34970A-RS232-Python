# Architecture: built on scpi-driver-core

This driver's byte transports come from
[`scpi-driver-core`](https://github.com/ami3go/scpi-driver-core). This page
records what moved, what stayed, and why.

## Layering

```text
        Functions/ and Examples/ scripts
                      |
              LOG34970A driver          command tree, channel/range checks,
              (LOG34970A_v2.py)         connect_serial() / connect_usb()
                      |
                 ScpiClient             SCPI framing, typed queries
                      |
       SerialTransport (RS232)  or  VisaTransport (USB/GPIB, e.g. the
                                     Keysight IO Libraries USBTMC bridge)
```

Nothing in `scpi_driver_core` imports this driver, or knows the 34970A
exists. The huge `storage`/`configure`/`measure`/`sense`/`route`/... command
tree in `LOG34970A_v2.py` is unchanged by this migration: it only builds SCPI
strings, so it stays here regardless of which transport sends them.

## One driver, two connections

`LOG34970A` exposes a single `send()`/`query()`/`close()` surface regardless
of how you connected:

```python
import LOG34970A.LOG34970A_v2 as logger_class

log = logger_class.LOG34970A()
log.connect_serial("COM11")        # RS232
# or
log.connect_usb()                  # USB/GPIB via the Keysight IO Libraries VISA backend
```

Previously these were two separate classes (`com_interface`, `usb_interface`)
with different construction patterns (one needed an explicit `.init(port)`
call, the other connected inside `__init__` with no way to pick a different
resource). They're merged because every caller in this repo only ever used
one or the other through the same `send`/`query`/`close` calls; keeping two
classes bought nothing but an inconsistent API.

## What moved to the core

The hand-rolled `pyserial`/`pyvisa` read/write/reconnect code in the old
`com_interface`/`usb_interface` classes. That included byte framing,
termination handling, and transport lifecycle (open/close/fault) — all of it
now comes from `SerialTransport`, `VisaTransport`, and `ScpiClient`.

## What stayed here

- The RS232 COM-port presence check and the USB/GPIB VISA resource
  discovery (scanning `list_resources()` for a substring match) — both are
  this driver's own connection policy, not something the core should know
  about.
- The USB/GPIB retry-on-timeout loop in `_query_usb`, including its 1-second
  write/read delay. This instrument's USBTMC bridge needs it; it is not a
  general SCPI behavior.
- The full `storage`/`configure`/`measure`/`sense`/`route`/... command tree:
  it interprets the 34970A's own command set and module/channel numbering, so
  per the core's own rule it belongs in the driver, not the core.

## SCPI command coverage

This repo was compared against `rf_keysight349xx`, the Robot Framework
driver for this instrument family (in a sibling `RobotFrameworks_hw_drivers`
checkout), and against the official *Agilent 34970A/72A Command Reference*
(`Docs/Agilent 34970A 72A Command Reference.pdf`, the actual ground truth).

**The RF driver has narrower coverage, not fuller.** Its own
`vendor_command_coverage.yaml` explicitly `DEFER`s temperature measurement
and `EXCLUDE`s the CALibration and DIAGnostic subsystems; it implements only
`MEASure`/generic `CONFigure`/scan/trigger/`INITiate`/`ABORt`/`READ?`/
`FETCh?`/`R?`/`DATA`. This driver's `storage` command tree already covered
all of that (including temperature) before this pass, plus `SENSe`,
`ROUTe`, `SOURce`, and `STATus` in much more depth.

Comparing against the actual command reference turned up real gaps and bugs,
which this pass fixed:

- **`cmd.configure.*.conf` never worked, for any function.**
  `configure.__init__` set `self.prefix = "CONF"` (short form), but every
  child class gates its `.conf` attribute on
  `self.prefix.find("CONFigure:")` (long form) — a substring that can never
  appear in anything built from the short form. The demo script at the
  bottom of `LOG34970A_v2.py` had every `CONFigure` line commented out,
  presumably because someone hit this and gave up rather than tracking it
  down. Fixed by making `configure.prefix` the long form; `self.cmd` (used
  only for the bare `CONFigure?` query) stays short since both forms are
  valid SCPI.
- **Three command-tree bugs generated SCPI that doesn't exist on this
  instrument**: `[SENSe:]VOLTage:AC:RESolution` (AC voltage has no
  resolution parameter — only AC *current* does), and
  `[SENSe:]RESistance:BANDwidth` / `[SENSe:]FRESistance:BANDwidth`
  (Bandwidth only applies to the AC current/voltage functions). A fourth,
  `frequency.voltage`, built a nonsensical nested `VOLTage:AC`/`VOLTage:DC`
  tree under `SENSe:FREQuency:` instead of the one real parameter,
  `[SENSe:]FREQuency:VOLTage:RANGe[:AUTO]`.
- **`CONFigure:TEMPerature` / `MEASure:TEMPerature?` were missing their
  required leading parameters.** Both need `{<probe_type>|DEF},{<type>|DEF}`
  before the channel list; the old `conf2`/`req2` wiring only ever appended
  a channel list, so a real instrument would have rejected every one of
  these as a malformed command. `temperature_conf.list()`/`.range()` now
  take `probe_type`/`sensor_type` (defaulting to `"DEF"`, which makes the
  command syntactically complete without specifying one).
- **`[SENSe:]TOTalize:*` was entirely dead.** `sense.totalize` reused the
  `totalize` class built for `CONFigure`/`MEASure:TOTalize`'s `READ`/
  `RRESet` mode selector, but that class only sets attributes when its
  prefix contains `"CONFigure:"` or `"MEASure:"` — neither matches `"SENS:"`,
  so `cmd.sense.totalize` was an object with no usable attributes. Replaced
  with `sense_totalize`, covering `CLEar:IMMediate`, `DATA?`, `SLOPe`,
  `STARt`/`STOP:IMMediate`, and `TYPE`.
- **Missing parameters**: `[SENSe:]PERiod` had no `SENSe` branch at all
  (`APERture`, `VOLTage:RANGe[:AUTO]`); `[SENSe:]TEMPerature` was missing
  `APERture` and `NPLC`.

New subsystems added, matching the Command Reference's own grouping:
`DATA`, `DISPlay`, `FORMat:READing`, `MEMory:STATe`, `OUTPut:ALARm`,
`CALCulate`, the rest of `SYSTem` (`DATE`, `TIME`, `VERSion?`, `PRESet`,
`LOCal`, `RWLock`, `LOCK:*`, `INTerface`, `LANGuage`, `LFRequency?`), and
the remaining IEEE-488.2 common commands (`*CLS`, `*OPC`, `*PSC`, `*RCL`,
`*SAV`, `*TRG`, `*TST?`, `*WAI`).

Intentionally **not** implemented, matching the RF driver's own exclusion
policy:

- `CALibration` — exposes a calibration security code and writes
  calibration constants.
- `DIAGnostic` — engineering/service-only slot-memory peek/poke.
- `SYSTem:SECurity[:IMMediate]` — irreversibly erases all instrument memory
  except calibration data and reboots.
- `SYSTem:COMMunicate:LAN:*`, `MMEMory`, `INSTrument`, `LXI` — apply to
  LAN-equipped models, USB mass storage, or the 34972A's internal DMM
  module; out of scope for this RS232/USB-GPIB driver of the 34970A.

Watch for a module-level footgun if extending this file further: it
declares `class str:` (for the `.str()`/`.req()` command-builder base),
which shadows the builtin `str` for the rest of the module. Don't call
`str(x)` inside `LOG34970A_v2.py` — use an f-string format spec
(`f'{x:02d}'`) instead, as `system_date.conf`/`system_time.conf` do.

## Worth knowing

- **The RS232 codec strips the line terminator.** The old `com_interface`
  returned whatever `pyserial.readline()` gave back, terminator included.
  `ScpiTextCodec(response_terminator=b"\n")` now removes exactly that one
  trailing `\n`. Every caller in this repo only ever ran `float()` or
  `.split(",")` on the reply, both of which tolerate the change either way.
- **The USB/GPIB path deliberately does not flush input before each query.**
  `VisaTransport.flush()` for a non-`OUTPUT` direction issues a VISA device
  clear (`resource.clear()`), which could interrupt an in-progress scan on
  real hardware. The RS232 path does flush before every query (matching the
  original `reset_input_buffer()` call), because a stream transport has no
  equivalent risk.
- **The 10ms post-connect read timeout on the USB/GPIB path is original,
  known-bad behavior, kept as-is.** The old `usb_interface` set
  `self.app.timeout = 10` (10 **milliseconds**) right after connecting, which
  is far too short for a real reply on its own — it only worked because of
  the 10-attempt/3-second-backoff retry loop around it. `_query_usb` keeps the
  same number (`_USB_POST_CONNECT_TIMEOUT_S = 0.010`) rather than silently
  "fixing" instrument timing nobody asked to change. If queries are
  unexpectedly slow to return, this is the first thing to look at.
- **A timed-out USB/GPIB read leaves the transport `FAULTED`.**
  `VisaTransport` calls `_fault()` (which releases the VISA resource) on any
  read failure, including a timeout — unlike raw `pyvisa`, where a timeout on
  `.query()` does not tear down the session. `_query_usb` checks for
  `TransportState.FAULTED` after a failed attempt and calls
  `transport.open()` before retrying; without that, the second retry attempt
  would raise `NotConnectedError` instead of actually retrying.
- **`VI_ATTR_SEND_END_EN` is no longer set explicitly.** The old
  `usb_interface` called
  `self.app.set_visa_attribute(pyvisa.constants.VI_ATTR_SEND_END_EN, 1)`.
  `VisaTransport` has no hook for arbitrary VISA attributes, and PyVISA
  enables `send_end` by default for USB/GPIB resources, so this was not
  expected to change behavior — but it's a known deviation if a specific
  adapter needs it explicitly set.

## Guarantees the core adds

- **Bounded reads.** Every read declares how it ends and how large it may
  get. There is no unbounded receive loop in the transport layer.
- **Byte fidelity.** SCPI framing removes only the terminator it was
  configured with, never a generic `strip()`.
- **An explicit transport state model.** `close()` is idempotent; I/O while
  not open fails before anything is transmitted; a failure leaving session
  validity uncertain faults the transport rather than being retried blindly.
- **Nothing retried by default.** The core never resends a write on your
  behalf. The USB/GPIB retry loop above is this driver's own choice, not
  something `scpi-driver-core` does automatically.

## Testing

`tests/test_log34970a_v2_transport.py` drives `LOG34970A` against
`scpi_driver_core.transport.mock.MockTransport` (the core's reference,
in-memory transport) for both connection kinds, since this repo's prior
scripts were manual (`Examples/`), not automated, and said nothing about the
transport this migration replaced. It covers: CRLF command framing on both
paths, the RS232 pre-query flush, the USB/GPIB reopen-after-fault retry, and
that `close()` releases the transport (and, for USB/GPIB, the VISA resource
manager).

Run it with:

```sh
pip install -r requirements-dev.txt
pytest
```
