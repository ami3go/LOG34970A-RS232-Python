"""Proof that LOG34970A_v2.LOG34970A runs on scpi-driver-core, on both paths.

These wire a MockTransport straight into a ScpiClient, the same way
connect_serial()/connect_usb() wire up the real SerialTransport/VisaTransport,
so they exercise the actual send/query/close code paths without needing real
hardware.
"""

from scpi_driver_core import ScpiClient
from scpi_driver_core.exceptions import TransportTimeoutError
from scpi_driver_core.transport.mock import MockTransport

import LOG34970A.LOG34970A_v2 as m


def _connected(connection: str) -> m.LOG34970A:
    transport = MockTransport()
    transport.open()
    driver = m.LOG34970A()
    codec = m._RS232_CODEC if connection == "serial" else m._VISA_CODEC
    driver._client = ScpiClient(transport, codec=codec)
    driver._connection = connection
    return driver


def test_serial_send_terminates_with_crlf():
    driver = _connected("serial")
    driver.send("ROUTe:OPEN (@101)")
    assert driver._client.transport.written == b"ROUTe:OPEN (@101)\r\n"


def test_serial_query_flushes_stale_input_before_reading():
    driver = _connected("serial")
    transport = driver._client.transport
    transport.feed(b"stale reading from a previous scan\n")

    original_flush = transport.flush

    def flush_then_deliver_reply(direction):
        original_flush(direction)
        transport.feed(b"+1.234000E+00\n")

    transport.flush = flush_then_deliver_reply

    reply = driver.query("READ?")

    assert reply == "+1.234000E+00"
    assert [op.kind for op in transport.operations] == ["open", "flush", "write", "read"]
    assert transport.written == b"READ?\r\n"


def test_serial_close_releases_the_transport():
    driver = _connected("serial")
    transport = driver._client.transport
    driver.close()
    assert transport.release_count == 1
    assert driver._client is None
    assert driver._connection is None


def test_usb_send_terminates_with_crlf():
    driver = _connected("usb")
    driver.send("ROUTe:OPEN (@101)")
    assert driver._client.transport.written == b"ROUTe:OPEN (@101)\r\n"


def test_usb_query_reopens_after_a_faulting_timeout_and_succeeds(monkeypatch):
    driver = _connected("usb")
    transport = driver._client.transport
    # simulates the instrument not answering within the (very short, see
    # docs/scpi-driver-core.md) post-connect read timeout on the first try
    transport.fail_next_read(TransportTimeoutError("no reply yet"), fault=True)
    transport.feed(b"AGILENT,34970A,0,1.0\n")
    monkeypatch.setattr(m.time, "sleep", lambda *_: None)

    reply = driver.query("*IDN?")

    assert reply == "AGILENT,34970A,0,1.0\n"
    assert transport.open_count == 2  # reopened once after the faulted read


def test_usb_close_clears_the_instrument_and_releases_the_transport():
    driver = _connected("usb")
    transport = driver._client.transport

    class _FakeResourceManager:
        closed = False

        def close(self):
            self.closed = True

    driver._rm = _FakeResourceManager()
    driver.close()

    assert transport.release_count == 1
    assert driver._rm is None


def test_query_dispatches_to_the_backend_matching_the_connection(monkeypatch):
    serial_driver = _connected("serial")
    serial_calls = []
    monkeypatch.setattr(serial_driver, "_query_serial", lambda cmd: serial_calls.append(cmd))
    monkeypatch.setattr(serial_driver, "_query_usb", lambda cmd: serial_calls.append("WRONG BACKEND"))
    serial_driver.query("READ?")
    assert serial_calls == ["READ?"]

    usb_driver = _connected("usb")
    usb_calls = []
    monkeypatch.setattr(usb_driver, "_query_serial", lambda cmd: usb_calls.append("WRONG BACKEND"))
    monkeypatch.setattr(usb_driver, "_query_usb", lambda cmd: usb_calls.append(cmd))
    usb_driver.query("READ?")
    assert usb_calls == ["READ?"]
