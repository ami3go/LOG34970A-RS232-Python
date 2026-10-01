# LOG34970A RS232/USB-GPIB Python Driver

Python driver for the **Agilent/Keysight 34970A/34972A Data Acquisition /
Switch Unit**, connectable either over RS232 or over USB-GPIB (via the
Keysight IO Libraries' VISA backend).

## Features

- One driver class, two connections: `LOG34970A.connect_serial(com_port)` or
  `LOG34970A.connect_usb()`; `send()`/`query()`/`close()` behave identically
  afterwards regardless of which was used.
- Built on [`scpi-driver-core`](https://github.com/ami3go/scpi-driver-core)
  for the byte transport, SCPI framing, and timeout/retry handling — see
  [`docs/scpi-driver-core.md`](docs/scpi-driver-core.md) for the full
  architecture writeup.
- A `storage()` command-tree builder covering the instrument's full SCPI
  surface (CONFigure, MEASure, SENSe, ROUTe, SOURce, STATus, SYSTem, DATA,
  DISPlay, FORMat:READing, MEMory:STATe, OUTPut:ALARm, CALCulate, and the
  IEEE-488.2 common commands) — see
  [`LOG34970A/Command_coverage.txt`](LOG34970A/Command_coverage.txt) for the
  exact command-by-command status.

## Installation

```bash
pip install -r requirements.txt
```

`scpi-driver-core` has no PyPI release yet (private, pre-1.0), so
`requirements.txt` pins it to a commit via git — installing requires git
access to `ami3go/scpi-driver-core`.

For running the tests:

```bash
pip install -r requirements-dev.txt
pytest
```

## Usage

```python
import LOG34970A.LOG34970A_v2 as logger_class

log = logger_class.LOG34970A()
log.connect_serial("COM11")        # RS232
# or: log.connect_usb()            # USB/GPIB via the Keysight IO Libraries VISA backend

cmd = logger_class.storage()

log.send(cmd.reset.str())
log.send(cmd.route.scan.conf.ch.range(101, 108))
log.send(cmd.sense.voltage.dc.NPLC.conf_10.ch.range(101, 108))

log.send(cmd.init.str())
readings = log.query(cmd.fetch.req())
print(readings)

log.close()
```

See [`Functions/Voltage_measurements.py`](Functions/Voltage_measurements.py)
and [`Examples/`](Examples/) for complete, runnable scripts, including a
scan-and-log example that exercises most of the command tree (connection,
configuration, DATA/DISPlay/MEMory/CALCulate subsystems, and more) in
[`Examples/Logger_class_v2_full_coverage_demo.py`](Examples/Logger_class_v2_full_coverage_demo.py).

## Repository layout

```text
LOG34970A/                   the driver itself (LOG34970A_v2.py) and its
                              command-coverage notes
Functions/                   small reusable measurement helper modules built
                              on top of the driver
Examples/                    standalone runnable scripts
docs/                        architecture notes (scpi-driver-core migration)
tests/                       pytest suite (transport wiring + command tree)
Docs/                        the vendor's own Command Reference PDF
ai/                          machine-readable driver description for AI
                              agents; see ai/ai_contract.yaml
```

## Testing

```bash
pytest
```

The suite drives the driver against `scpi_driver_core`'s in-memory
`MockTransport` and against the command-tree builder directly — no hardware
required. It does not touch real COM ports or VISA resources.

## License

MIT — see [LICENSE](LICENSE).
