"""
Renode simulation bridge — domain-agnostic orchestrator.

Drives the full embedded simulation path:

    samples (float32 np.ndarray, N×6)
        │  write imu_sim file  (read by sim_imu_stub.py in Renode)
        ▼
    Renode process  (firmware.elf on nRF52840 + IMU + UART stubs)
        │  firmware emits UART output
        ▼
    UART log file   (returned as raw text; project's src/analysis.py parses it)

The stubs (sim_imu_stub.py, sim_uart_stub.py) are IronPython scripts that
Renode loads as Python peripherals. They live at:
    crucible/sim/stubs/sim_imu_stub.py
    crucible/sim/stubs/sim_uart_stub.py

Public API
----------
    RenoneBridge(elf_path, ...)
    text = bridge.run(samples)         — returns raw UART log as a string

    detect_renode() -> str | None
    detect_firmware(*candidates) -> str | None
    build_sim_firmware(project_root, env) -> str
"""
from __future__ import annotations

import os
import shutil
import socket
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional

import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# Default paths — all prefixed ``crucible_`` (not domain-specific)
# Projects can override via RenoneBridge constructor parameters.
# ─────────────────────────────────────────────────────────────────────────────

_STUBS_DIR      = Path(__file__).resolve().parent / "stubs"
_IMU_STUB_PATH  = _STUBS_DIR / "sim_imu_stub.py"
_UART_STUB_PATH = _STUBS_DIR / "sim_uart_stub.py"

# Shared temp paths used between the bridge and the IronPython stubs.
# Override by passing imu_sim= and uart_log= to RenoneBridge().
_IMU_SIM_PATH  = Path("/tmp/crucible_imu_sim.f32")
_UART_LOG_PATH = Path.home() / "crucible_uart.log"

# Config files used to pass paths to IronPython stubs (which cannot receive
# dynamic arguments — config files bridge the gap).
_CFG_IMU_PATH  = Path.home() / ".crucible_imu_sim_path.txt"
_CFG_LOG_PATH  = Path.home() / ".crucible_uart_log_path.txt"
_CFG_SENT_PATH = Path.home() / ".crucible_uart_sentinel_path.txt"

# Renode telnet monitor
_TELNET_HOST = "127.0.0.1"
_TELNET_PORT = 1234

# Timeouts (seconds)
_BOOT_TIMEOUT_S    = 10.0
_SESSION_TIMEOUT_S = 200.0
_POLL_INTERVAL_S   = 0.2


# ─────────────────────────────────────────────────────────────────────────────
# Auto-detection helpers
# ─────────────────────────────────────────────────────────────────────────────

def detect_renode() -> Optional[str]:
    """Return path to the renode binary if found on PATH, else None."""
    return shutil.which("renode")


def detect_firmware(*candidates: str | Path) -> Optional[str]:
    """Return the first existing ELF path from ``candidates``, else None.

    Pass paths in priority order. Typical call::

        elf = detect_firmware(
            "firmware/zephyr_sim.elf",
            ".pio/build/xiaoble_sense_sim/zephyr/zephyr.elf",
        )
    """
    for p in candidates:
        if p and Path(p).exists():
            return str(p)
    return None


def build_sim_firmware(project_root: str | Path, env: str = "xiaoble_sense_sim") -> str:
    """Build the sim firmware via PlatformIO + ninja and return the ELF path.

    Two-step process:
      1. ``pio run -e <env>``          — configures CMake, compiles Zephyr
      2. ``ninja zephyr/zephyr.elf``   — links the final ELF including app code

    Raises RuntimeError on failure.
    """
    root = Path(project_root)
    build_dir = root / ".pio" / "build" / env

    r = subprocess.run(
        ["pio", "run", "-e", env],
        cwd=str(root), capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(
            f"PlatformIO build failed:\n{r.stdout[-2000:]}\n{r.stderr[-1000:]}"
        )

    ninja_bin = shutil.which("ninja") or "ninja"
    r2 = subprocess.run(
        [ninja_bin, "zephyr/zephyr.elf"],
        cwd=str(build_dir), capture_output=True, text=True,
    )
    if r2.returncode != 0:
        raise RuntimeError(
            f"ninja link failed:\n{r2.stdout[-2000:]}\n{r2.stderr[-1000:]}"
        )

    elf = build_dir / "zephyr" / "zephyr.elf"
    if not elf.exists():
        raise RuntimeError(f"Expected ELF not found after build: {elf}")
    return str(elf)


# ─────────────────────────────────────────────────────────────────────────────
# Telnet monitor client
# ─────────────────────────────────────────────────────────────────────────────

class _MonitorClient:
    """Minimal telnet client for Renode's interactive monitor."""

    def __init__(self, host: str = _TELNET_HOST, port: int = _TELNET_PORT):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(5.0)
        self._sock.connect((host, port))
        self._buf = b""

    def _recv_until(self, marker: bytes, timeout: float = 5.0) -> str:
        deadline = time.monotonic() + timeout
        while True:
            idx = self._buf.find(marker)
            if idx >= 0:
                out = self._buf[:idx].decode("utf-8", errors="replace")
                self._buf = self._buf[idx + len(marker):]
                return out
            if time.monotonic() > deadline:
                raise TimeoutError(f"Renode monitor: timed out waiting for {marker!r}")
            try:
                chunk = self._sock.recv(4096)
                if chunk:
                    self._buf += chunk
            except socket.timeout:
                pass

    def send(self, cmd: str, timeout: float = 30.0) -> str:
        """Send a monitor command and return the response up to the next prompt."""
        self._sock.sendall((cmd.strip() + "\n").encode())
        return self._recv_until(b") \x1b[0m", timeout=timeout)

    def close(self) -> None:
        try:
            self._sock.close()
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# Main bridge
# ─────────────────────────────────────────────────────────────────────────────

class RenoneBridge:
    """Orchestrate a single Renode simulation run.

    Parameters
    ----------
    elf_path : str | Path
        Firmware ELF to flash (must exist).
    imu_sim : Path
        Where to write the float32 IMU sample file (read by sim_imu_stub.py).
        Defaults to ``/tmp/crucible_imu_sim.f32``.
    uart_log : Path
        Where Renode writes UART output (polled for session-end sentinel).
        Defaults to ``~/crucible_uart.log``.
    telnet_port : int
        Renode monitor telnet port.
    stationary_prefix_samples : int
        Quiet calibration samples prepended before the signal sequence.
        Must be ≥ the firmware's CAL_SAMPLES constant (typically 400).
    session_end_sentinel : str
        The UART string whose presence signals session completion.
        Must match ``docs/toolchain_config.md`` [firmware.uart_format] session_end_marker.
        Default: ``"SESSION_END"``.
    """

    def __init__(
        self,
        elf_path:  str | Path,
        imu_sim:   Path = _IMU_SIM_PATH,
        uart_log:  Path = _UART_LOG_PATH,
        telnet_port: int = _TELNET_PORT,
        stationary_prefix_samples: int = 450,
        session_end_sentinel: str = "SESSION_END",
    ) -> None:
        self.elf_path    = Path(elf_path)
        self.imu_sim     = imu_sim
        self.uart_log    = uart_log
        self.telnet_port = telnet_port
        self.stationary_prefix_n = stationary_prefix_samples
        self.session_end_sentinel = session_end_sentinel

        self._proc:            Optional[subprocess.Popen] = None
        self._monitor:         Optional[_MonitorClient]   = None
        self._n_samples:       int = 0
        self._tmp_repl:        Optional[str] = None
        self._tmp_repl2:       Optional[str] = None
        self._renode_log_path: Optional[Path] = None
        self._sentinel_path:   Optional[Path] = None
        self._sim_failed:      bool = False

    # ── public API ────────────────────────────────────────────────────────────

    def run(self, samples: np.ndarray) -> str:
        """Run a full simulation for the given sensor samples.

        Parameters
        ----------
        samples : np.ndarray (N, C)
            Physical-unit float32 sensor data (columns depend on sensor type).
            For IMU: [ax ay az gx gy gz].

        Returns
        -------
        str
            Raw UART log text. Pass to your project's ``src/analysis.py`` parser.
        """
        self._sim_failed = False
        try:
            self._prepare_imu_file(samples)
            self._start_renode()
            self._configure_renode()
            self._wait_for_session_end()
        except Exception:
            self._sim_failed = True
            raise
        finally:
            self._stop_renode()

        return self.uart_log.read_text(encoding="utf-8", errors="replace")

    # ── internal helpers ──────────────────────────────────────────────────────

    def _prepare_imu_file(self, samples: np.ndarray) -> None:
        G = 9.81
        n_pre = self.stationary_prefix_n
        stationary = np.zeros((n_pre, samples.shape[1]), dtype=np.float32)
        # Assume column 2 (az) is the gravity axis for IMU sensors.
        # For non-IMU sensors, pass stationary_prefix_samples=0.
        if samples.shape[1] >= 3:
            stationary[:, 2] = G

        full = np.vstack([stationary, samples.astype(np.float32)])
        self._n_samples = len(full)
        full.tofile(str(self.imu_sim))

        self.uart_log.unlink(missing_ok=True)

        # Communicate paths to IronPython stubs via config files.
        _CFG_IMU_PATH.write_text(str(self.imu_sim))
        _CFG_LOG_PATH.write_text(str(self.uart_log))
        sentinel = str(self.uart_log) + ".done"
        _CFG_SENT_PATH.write_text(sentinel)

    def _start_renode(self) -> None:
        renode_bin = detect_renode()
        if not renode_bin:
            raise RuntimeError("renode binary not found on PATH")

        _renode_log = Path(tempfile.mktemp(suffix="_renode.log"))
        self._renode_log_path = _renode_log
        self._proc = subprocess.Popen(
            [renode_bin, "--disable-xwt", "--port", str(self.telnet_port)],
            stdout=open(str(_renode_log), "w"),
            stderr=subprocess.STDOUT,
        )

        deadline = time.monotonic() + _BOOT_TIMEOUT_S
        while time.monotonic() < deadline:
            try:
                self._monitor = _MonitorClient(_TELNET_HOST, self.telnet_port)
                self._monitor._recv_until(b") \x1b[0m", timeout=5.0)
                return
            except (ConnectionRefusedError, OSError, TimeoutError):
                time.sleep(0.3)

        log_snippet = ""
        if self._renode_log_path and self._renode_log_path.exists():
            try:
                log_snippet = (
                    f"\nRenode log: "
                    f"{self._renode_log_path.read_text(errors='replace')[-500:]}"
                )
            except Exception:
                pass
        raise RuntimeError(
            f"Renode monitor did not open on port {self.telnet_port} "
            f"within {_BOOT_TIMEOUT_S}s{log_snippet}"
        )

    def _configure_renode(self) -> None:
        mon = self._monitor

        imu_stub_abs  = str(_IMU_STUB_PATH.resolve())
        uart_stub_abs = str(_UART_STUB_PATH.resolve())

        # REPL 1: nrf52840 base + IMU stub
        repl1 = (
            'using "platforms/cpus/nrf52840.repl"\n\n'
            'sim_imu: Python.PythonPeripheral @ sysbus 0x400B0000\n'
            '    size: 0x100\n'
            f'    filename: "{imu_stub_abs}"\n'
            '    initable: true\n'
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".repl", delete=False) as tmp:
            tmp.write(repl1)
            self._tmp_repl = tmp.name

        # REPL 2: UART Python stub (replaces built-in uart0)
        repl2 = (
            'sim_uart: Python.PythonPeripheral @ sysbus <0x40002000, +0x1000>\n'
            '    size: 0x1000\n'
            f'    filename: "{uart_stub_abs}"\n'
            '    initable: true\n'
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".repl", delete=False) as tmp:
            tmp.write(repl2)
            self._tmp_repl2 = tmp.name

        r = mon.send('mach create "device"')
        print(f"[Renode] mach create          : {r.strip()!r}")

        r = mon.send(f"machine LoadPlatformDescription @{self._tmp_repl}")
        print(f"[Renode] LoadPlatformDesc (1) : {r.strip()!r}")
        if "error" in r.lower() or "exception" in r.lower():
            raise RuntimeError(f"REPL 1 load failed: {r.strip()}")

        r = mon.send("sysbus Unregister uart0")
        print(f"[Renode] Unregister uart0     : {r.strip()!r}")

        r = mon.send(f"machine LoadPlatformDescription @{self._tmp_repl2}")
        print(f"[Renode] LoadPlatformDesc (2) : {r.strip()!r}")
        if "error" in r.lower() or "exception" in r.lower():
            raise RuntimeError(f"REPL 2 (uart stub) load failed: {r.strip()}")

        r = mon.send(f"sysbus LoadELF @{self.elf_path}", timeout=60.0)
        print(f"[Renode] LoadELF              : {r.strip()!r}")
        if "error" in r.lower() or "exception" in r.lower():
            raise RuntimeError(f"ELF load failed: {r.strip()}")

        # Fire UARTE0 IRQ on every TASKS_STARTTX write so Zephyr uart_poll_out()
        # unblocks after each byte. See sim_uart_stub.py for details.
        wp_hook = "self.GetMachine().SystemBus.WriteDoubleWord(0xE000E200, 4)"
        r = mon.send(f'sysbus AddWatchpointHook 0x40002008 4 2 "{wp_hook}"')
        print(f"[Renode] WatchpointHook UART  : {r.strip()!r}")

        sentinel = str(self.uart_log) + ".done"
        self._sentinel_path = Path(sentinel)
        self._sentinel_path.unlink(missing_ok=True)

        r = mon.send('emulation RunFor "1.5"', timeout=60.0)
        print(f"[Renode] RunFor 1.5s (boot)   : {r.strip()!r}")
        r = mon.send('emulation RunFor "0.1"', timeout=30.0)
        print(f"[Renode] RunFor 0.1s (settle) : {r.strip()!r}")

    def _wait_for_session_end(self) -> None:
        mon      = self._monitor
        odr      = 208.0
        walk_s   = self._n_samples / odr
        elapsed  = 0.0
        chunk    = 0.5
        sentinel = self._sentinel_path

        deadline = time.monotonic() + _SESSION_TIMEOUT_S
        while time.monotonic() < deadline:
            mon.send(f'emulation RunFor "{chunk}"')
            elapsed += chunk
            if sentinel and sentinel.exists():
                return
            time.sleep(_POLL_INTERVAL_S)
            if elapsed > walk_s + 8.0:
                break

        raise TimeoutError(
            f"Session-end sentinel not seen after {elapsed:.1f}s simulated "
            f"({self._n_samples} samples, {walk_s:.1f}s)"
        )

    def _stop_renode(self) -> None:
        if self._monitor:
            try:
                self._monitor.send("quit")
            except Exception:
                pass
            self._monitor.close()
            self._monitor = None

        if self._proc:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=5)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
            self._proc = None

        for attr in ("_tmp_repl", "_tmp_repl2"):
            p = getattr(self, attr, None)
            if p:
                try:
                    os.unlink(p)
                except Exception:
                    pass
                setattr(self, attr, None)

        if self._sentinel_path:
            try:
                self._sentinel_path.unlink(missing_ok=True)
            except Exception:
                pass
            self._sentinel_path = None

        if self._renode_log_path:
            if self._sim_failed and self._renode_log_path.exists():
                try:
                    tail = self._renode_log_path.read_text(errors="replace")[-2000:]
                    print(f"\n[Renode log tail]\n{tail}\n[/Renode log]")
                except Exception:
                    pass
            try:
                self._renode_log_path.unlink(missing_ok=True)
            except Exception:
                pass
            self._renode_log_path = None
