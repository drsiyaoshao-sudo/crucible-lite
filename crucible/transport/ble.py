"""
BLE transport layer — NUS console receiver + binary GATT session download.

Two independent entry points:

    BleConsole
        Scans for a named device, subscribes to the Nordic UART Service (NUS)
        TX characteristic, and streams lines to stdout (or a callback).

    download_session()
        Connects to a device, writes CTRL_EXPORT to the Control Point, and
        collects rolling_snapshot_t notifications until the transfer completes.
        Returns a list of SnapshotRecord and optionally writes a CSV.

Both require the ``bleak`` package (pip install bleak).

NUS UUIDs (Nordic UART Service):
    Service:     6E400001-B5A3-F393-E0A9-E50E24DCCA9E
    TX (notify): 6E400003-B5A3-F393-E0A9-E50E24DCCA9E  ← device → host
    RX (write):  6E400002-B5A3-F393-E0A9-E50E24DCCA9E

GATT session service UUIDs (must match ble_gait_svc.c):
    Service:     6e410000-b5a3-f393-e0a9-e50e24dcca9e
    Status:      6e410001-b5a3-f393-e0a9-e50e24dcca9e
    Data:        6e410002-b5a3-f393-e0a9-e50e24dcca9e
    Control:     6e410003-b5a3-f393-e0a9-e50e24dcca9e

rolling_snapshot_t PDU layout (20 bytes, little-endian):
    uint32  anchor_step_index
    uint32  anchor_ts_ms
    uint16  si_stance_x10        (13.3% → 133)
    uint16  si_swing_x10
    uint16  si_peak_angvel_x10
    uint16  mean_cadence_x10     (100 spm → 1000)
    uint8   step_count
    int8    flags                (bit0=walking, bit1=running)

Notification PDU header (4 bytes prepended):
    uint16  seq     — packet sequence number
    uint16  n       — number of snapshots in this PDU
"""
from __future__ import annotations

import asyncio
import csv
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

# ─────────────────────────────────────────────────────────────────────────────
# NUS UUIDs
# ─────────────────────────────────────────────────────────────────────────────

NUS_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
NUS_TX_UUID      = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"  # device → host
NUS_RX_UUID      = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"  # host → device

# ─────────────────────────────────────────────────────────────────────────────
# GATT session service UUIDs
# ─────────────────────────────────────────────────────────────────────────────

_SVC_UUID    = "6e410000-b5a3-f393-e0a9-e50e24dcca9e"
_STATUS_UUID = "6e410001-b5a3-f393-e0a9-e50e24dcca9e"
_DATA_UUID   = "6e410002-b5a3-f393-e0a9-e50e24dcca9e"
_CTRL_UUID   = "6e410003-b5a3-f393-e0a9-e50e24dcca9e"

_CTRL_EXPORT = struct.pack("<H", 0x0003)
_CTRL_CLEAR  = struct.pack("<H", 0x0004)

# Session status codes
SESSION_IDLE      = 0
SESSION_RECORDING = 1
SESSION_COMPLETE  = 2
SESSION_TRANSFER  = 3

# ─────────────────────────────────────────────────────────────────────────────
# Binary snapshot PDU
# ─────────────────────────────────────────────────────────────────────────────

_SNAP_STRUCT = struct.Struct("<IIHHHHBb")  # 20 bytes
_PDU_HEADER  = struct.Struct("<HH")        # seq (2) + count (2)


@dataclass
class SnapshotRecord:
    """One rolling_snapshot_t record received over BLE."""
    seq:                int
    anchor_step_index:  int
    anchor_ts_ms:       int
    si_stance_pct:      float   # %
    si_swing_pct:       float   # %
    si_peak_angvel_pct: float   # %
    mean_cadence_spm:   float   # spm
    step_count:         int
    is_walking:         bool
    is_running:         bool


def unpack_notification(data: bytes, seq: int) -> list[SnapshotRecord]:
    """Unpack one BLE notification PDU → list of SnapshotRecord.

    Parameters
    ----------
    data : bytes
        Raw notification bytes from the Step Data characteristic.
    seq : int
        PDU sequence number (caller-managed counter).

    Raises
    ------
    ValueError
        If the PDU is shorter than its declared length.
    """
    if len(data) < _PDU_HEADER.size:
        raise ValueError(f"PDU too short for header: {len(data)} bytes")

    pdu_seq, n = _PDU_HEADER.unpack_from(data, 0)
    payload_start = _PDU_HEADER.size
    expected = payload_start + n * _SNAP_STRUCT.size

    if len(data) < expected:
        raise ValueError(
            f"PDU truncated: declared {n} snapshots need {expected} bytes, "
            f"got {len(data)}"
        )

    records: list[SnapshotRecord] = []
    offset = payload_start
    for _ in range(n):
        (
            anchor_step, anchor_ts_ms,
            si_stance_x10, si_swing_x10, si_peak_x10,
            cadence_x10, step_count, flags,
        ) = _SNAP_STRUCT.unpack_from(data, offset)
        offset += _SNAP_STRUCT.size

        records.append(SnapshotRecord(
            seq                 = pdu_seq,
            anchor_step_index   = anchor_step,
            anchor_ts_ms        = anchor_ts_ms,
            si_stance_pct       = si_stance_x10  / 10.0,
            si_swing_pct        = si_swing_x10   / 10.0,
            si_peak_angvel_pct  = si_peak_x10    / 10.0,
            mean_cadence_spm    = cadence_x10    / 10.0,
            step_count          = step_count,
            is_walking          = bool(flags & 0x01),
            is_running          = bool(flags & 0x02),
        ))

    return records


def export_csv(records: list[SnapshotRecord], path: Path) -> None:
    """Write snapshot records to a CSV file."""
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "seq", "anchor_step_index", "anchor_ts_ms",
            "si_stance_pct", "si_swing_pct", "si_peak_angvel_pct",
            "mean_cadence_spm", "step_count", "is_walking", "is_running",
        ])
        writer.writeheader()
        for r in records:
            writer.writerow({
                "seq":                r.seq,
                "anchor_step_index":  r.anchor_step_index,
                "anchor_ts_ms":       r.anchor_ts_ms,
                "si_stance_pct":      f"{r.si_stance_pct:.1f}",
                "si_swing_pct":       f"{r.si_swing_pct:.1f}",
                "si_peak_angvel_pct": f"{r.si_peak_angvel_pct:.1f}",
                "mean_cadence_spm":   f"{r.mean_cadence_spm:.1f}",
                "step_count":         r.step_count,
                "is_walking":         int(r.is_walking),
                "is_running":         int(r.is_running),
            })


# ─────────────────────────────────────────────────────────────────────────────
# NUS console receiver
# ─────────────────────────────────────────────────────────────────────────────

class BleConsole:
    """Stream UART output from a device over the Nordic UART Service.

    Usage (standalone)::

        console = BleConsole(device_name="GaitS")
        asyncio.run(console.run())

    Usage (with callback)::

        def on_line(line: str):
            print(f"[DEVICE] {line}")

        console = BleConsole(device_name="GaitS", on_line=on_line)
        asyncio.run(console.run())
    """

    def __init__(
        self,
        device_name: str = "GaitS",
        scan_timeout: float = 15.0,
        on_line: Optional[Callable[[str], None]] = None,
    ):
        self.device_name  = device_name
        self.scan_timeout = scan_timeout
        self.on_line      = on_line or (lambda line: sys.stdout.write(line + "\n") or sys.stdout.flush())
        self._buf         = ""

    def _handle_notify(self, _sender, data: bytearray) -> None:
        self._buf += data.decode("utf-8", errors="replace")
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            self.on_line(line)

    async def run(self) -> None:
        """Scan, connect, and stream until KeyboardInterrupt."""
        try:
            from bleak import BleakScanner, BleakClient
        except ImportError:
            print("bleak not installed. Install with: pip install bleak", file=sys.stderr)
            sys.exit(1)

        device = None
        while device is None:
            print(f"Scanning for '{self.device_name}*'...")
            device = await BleakScanner.find_device_by_name(
                self.device_name, timeout=self.scan_timeout
            )
            if device is None:
                print("Not found, retrying...")

        print(f"Found: {device.name} [{device.address}]")
        print("Connecting...")

        async with BleakClient(device) as client:
            print("Connected. Subscribing to NUS TX...")
            await client.start_notify(NUS_TX_UUID, self._handle_notify)
            print("--- device output ---")
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                pass
            await client.stop_notify(NUS_TX_UUID)
            print("\n--- disconnected ---")


# ─────────────────────────────────────────────────────────────────────────────
# Binary GATT session download
# ─────────────────────────────────────────────────────────────────────────────

async def download_session(
    device_name: str = "GaitSense",
    output: Optional[Path] = None,
    poll_timeout_s: float = 30.0,
) -> list[SnapshotRecord]:
    """Connect to a device over BLE and download the completed session.

    Parameters
    ----------
    device_name : str
        BLE advertising name to scan for.
    output : Path | None
        If given, write records to this CSV path.
    poll_timeout_s : float
        Maximum time to wait for transfer completion after sending CTRL_EXPORT.

    Returns
    -------
    list[SnapshotRecord]
        All snapshot records received.

    Raises
    ------
    SystemExit
        If bleak is not installed, or the device is not found.
    RuntimeError
        If the device is not in COMPLETE state when we connect.
    """
    try:
        from bleak import BleakScanner, BleakClient
    except ImportError:
        print("bleak not installed. Install with: pip install bleak", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning for '{device_name}'...")
    device = await BleakScanner.find_device_by_name(device_name, timeout=10.0)
    if device is None:
        print(f"Device '{device_name}' not found.", file=sys.stderr)
        sys.exit(1)

    all_records: list[SnapshotRecord] = []
    seq_counter = [0]

    def _on_data(_, data: bytearray):
        try:
            recs = unpack_notification(bytes(data), seq_counter[0])
            all_records.extend(recs)
            seq_counter[0] += 1
        except ValueError as e:
            print(f"[WARN] bad PDU: {e}", file=sys.stderr)

    async with BleakClient(device) as client:
        print(f"Connected to {device.name} ({device.address})")

        status_raw = await client.read_gatt_char(_STATUS_UUID)
        status = status_raw[0]
        if status not in (SESSION_COMPLETE, SESSION_TRANSFER):
            raise RuntimeError(
                f"Device not in COMPLETE state (status={status}). "
                "Finish recording before downloading."
            )

        await client.start_notify(_DATA_UUID, _on_data)
        await client.write_gatt_char(_CTRL_UUID, _CTRL_EXPORT)

        poll_steps = int(poll_timeout_s / 0.1)
        for _ in range(poll_steps):
            await asyncio.sleep(0.1)
            status_raw = await client.read_gatt_char(_STATUS_UUID)
            if status_raw[0] != SESSION_TRANSFER:
                break

        await client.stop_notify(_DATA_UUID)

    print(f"Received {len(all_records)} snapshots.")

    if output:
        export_csv(all_records, output)
        print(f"Saved to {output}")

    return all_records
