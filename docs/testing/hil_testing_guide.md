# HIL Testing Guide — Hardware-in-the-Loop First

## Why HIL runs first, not last

Every hardware project eventually faces the same moment: the algorithm is validated in simulation, the firmware compiles cleanly, and the board is on the bench. You flash it. Nothing works. Four hours later you discover the USB cable was charge-only, or the FQBN was wrong, or the SoftDevice offset mismatch silently corrupted the flash, or the BLE device name truncated in the advertising packet and the scanner was looking for the wrong string.

None of these failures are algorithm problems. None of them are firmware problems. They are all toolchain problems — and every one of them could have been found in 15 minutes on Day 1.

**This is the HIL-first principle:** prove that the complete loop — build → flash → run → observe — works before validating any algorithm. The cost of HIL failure at Day 1 is 20 minutes. The cost of the same failure at Week 6 of algorithm validation is days of confusion and a broken mental model.

---

## What HIL testing proves

A passing Stage 0 HIL session proves exactly four things — no more, no less:

1. **The build toolchain produces a flashable binary for this specific board.** Not "a binary that compiles" — a binary that actually runs on this hardware.

2. **The flash mechanism works end-to-end.** Whatever method you use (UF2 drag-and-drop, J-Link, DFU, JTAG), it deposits the firmware correctly and the device boots.

3. **The observation path works.** You can see output from the device — USB serial, BLE, UART, RTT — and the output is interpretable.

4. **The sensor hardware is alive.** The sensor is reachable over its interface (I2C, SPI, ADC), returns physically plausible values, and does not crash the firmware at init.

Stage 0 does not prove the algorithm is correct. It does not prove the power budget. It does not prove BLE range or packet integrity under load. Those are Stages 1–4. Stage 0 only proves that the development loop is functional.

---

## The four-smoke-test sequence

Stage 0 consists of four smoke tests run in this exact order. Each test is independent — if test N fails, diagnose and fix it before running test N+1. Do not run tests out of order.

The sequence is borrowed from Amendment 16 of the GaitSense reference implementation. The principle generalises to any device.

### Smoke Test 1 — Counter

**Purpose:** Prove build → flash → USB serial observe works.  
**Firmware:** A sketch/program that increments a counter once per second and prints it to USB serial.  
**Expected output:** `counter=1`, `counter=2`, `counter=3`...  
**Pass criteria:** Counter increments without reset for ≥ 10 lines.

**What this isolates:**
- USB-C / USB-A cable is data-capable (not charge-only)
- Board appears as a valid USB CDC device on your OS
- Baud rate is correct
- Board variant is correct (wrong variant often silently boots but has no USB CDC)
- Build environment targets the right board (FQBN / linker script / flash offset)

**Common failures at this step:**
| Symptom | Root cause |
|---------|-----------|
| No serial device appears | Charge-only cable; try a different cable |
| Garbage characters | Baud rate mismatch in monitor; set to 115200 |
| Counter resets every few seconds | Watchdog enabled with wrong feed interval; or board rebooting |
| Device appears but empty output | Wrong board variant; verify board model against FQBN |
| Flash appears to succeed but no boot | Flash offset wrong; verify bootloader region not overwritten |

---

### Smoke Test 2 — Sensor Readout

**Purpose:** Prove the sensor hardware is alive and readable.  
**Firmware:** Reads the sensor at a fixed interval and prints raw values to USB serial.  
**Expected output:** Physically plausible values (gravity on Z axis for an IMU; ~21°C for a temperature sensor; ~0 lux for a light sensor in a dark room).  
**Pass criteria:** Values stream continuously, are physically plausible, and update correctly when the sensor input changes.

**What this isolates:**
- Sensor I2C/SPI address is correct
- Power rail to sensor is enabled (power-enable pin if present)
- Wire assignments are correct (SDA/SCL or MOSI/MISO/SCK/CS not swapped)
- Sensor WHO_AM_I or equivalent identification register returns expected value
- Data is in correct physical units (g vs m/s², raw counts vs calibrated, etc.)

**Physical plausibility checklist for common sensor types:**
| Sensor type | What to check |
|------------|--------------|
| 6-DOF IMU (acc+gyro) | `az ≈ ±9.8 m/s²` when flat; `gx/gy/gz ≈ 0 dps` when still |
| Temperature | Within ±5°C of room temperature |
| Humidity | 20–80% in typical indoor conditions |
| Ambient light | Near 0 lux covered; hundreds to thousands lux in sunlight |
| PIR | Digital output toggles when hand passes in front |
| ADC (resistive sensor) | Value changes in expected direction when stimulus applied |

**Common failures at this step:**
| Symptom | Root cause |
|---------|-----------|
| `Sensor init FAILED` and halt | I2C address wrong; check WHO_AM_I register in datasheet. Or power-enable pin not asserted. |
| Values all zero | I2C not responding; check SDA/SCL pin assignment and pull-up presence |
| Values physically wrong (e.g. `az ≈ 1.0` instead of `9.81`) | Unit conversion missing; sensor returns g, firmware expects m/s² |
| Values frozen / not updating | Trigger mode wrong; polling instead of interrupt, or interrupt not wired |
| Sensor found but wrong data | Wire (I2C bus 0) vs Wire1 (I2C bus 1) confusion on multi-bus boards |

---

### Smoke Test 3 — Algorithm over USB

**Purpose:** Prove the algorithm runs on the device and produces output over USB serial.  
**Firmware:** Full algorithm stack reading from the sensor, processing, and printing results.  
**Expected output:** Algorithm-specific lines (step counts, temperature events, occupancy transitions, etc.) over USB serial.  
**Pass criteria:** Algorithm output appears within a few seconds of applying the relevant stimulus.

**What this isolates:**
- Algorithm compiles and runs correctly on this MCU (integer overflow, stack size, FPU availability)
- Sensor data flows into the algorithm correctly (units, axis orientation, sampling rate)
- Algorithm output is in the expected format and physically plausible range

**Common failures at this step:**
| Symptom | Root cause |
|---------|-----------|
| No algorithm output | Input not reaching algorithm (sampling loop not running, wrong sensor bus) |
| Output but values wrong | Unit mismatch between sensor driver and algorithm (m/s² vs g, etc.) |
| Firmware crashes on start | Stack overflow; increase `MAIN_STACK_SIZE` or reduce local variable size |
| Output but always same value | Algorithm not receiving varying input; check sensor sampling loop |
| Output with BUG-013-class issue (correct answer should be non-zero, returns zero) | FPU emulation bug or compiler optimisation eliminating a computation; test explicitly under non-zero input |

---

### Smoke Test 4 — Algorithm over BLE (or your wireless transport)

**Purpose:** Prove the wireless path works end-to-end.  
**Firmware:** Same algorithm as Smoke Test 3, output sent over BLE / Zigbee / WiFi / LoRa.  
**Receiver:** Host script or app on laptop / phone that subscribes and prints.  
**Expected output:** Same algorithm output as Smoke Test 3, received on the host.  
**Pass criteria:** Data arrives on host within 5 seconds of stimulus; output is not truncated or garbled.

**What this isolates:**
- BLE advertising starts correctly and device is discoverable
- Device name matches what the host is scanning for
- Notification subscription works
- MTU / packet size is handled correctly (long lines do not fragment silently)
- BLE write path works unconditionally (not gated on `connected()` check that returns false)

**Common failures at this step:**
| Symptom | Root cause |
|---------|-----------|
| Device not found in scan | Device name truncation; advertising packet has a length limit — verify exact advertised name |
| Connected but no data | Write gated on `connected()` check that returns false; write unconditionally |
| Truncated lines | Line length exceeds BLE MTU; shorten format strings or add line-buffering in receiver |
| Data arrives out of order | Multiple notifications for one logical line; add line-buffer in receiver |
| Device found but won't connect | SoftDevice version mismatch; verify bootloader + SoftDevice combo for your BLE stack |

---

## Stage 0 lock criteria

Stage 0 is CLOSED when all four smoke tests pass and the human confirms:

- [ ] Smoke Test 1 PASS: counter streams without reset
- [ ] Smoke Test 2 PASS: sensor values physically plausible and updating
- [ ] Smoke Test 3 PASS: algorithm output appears over USB within stimulus
- [ ] Smoke Test 4 PASS: algorithm output received on host over wireless

Record the confirmation in your project's stage gate log. Run `/toolchain lock` to stamp the toolchain config as Stage 0 validated.

After lock: the toolchain is frozen. Any change to the build tool, FQBN, flash method, or library version requires a Bill before it can be made. This is not bureaucracy for its own sake — it is the only way to ensure that a future hardware failure can be attributed to a specific change rather than to "something changed."

---

## What HIL testing does not replace

Stage 0 validates the development loop. It does not validate:
- Algorithm correctness (Stage 1 — simulation)
- Algorithm accuracy under real-world conditions (Stage 3 — field test)
- Power budget (field test or bench measurement)
- BLE range and packet loss under real conditions (field test)
- Long-term reliability (not in scope for Crucible 0.1)

A device that passes Stage 0 has a working dev loop. That is all. It says nothing about whether the algorithm is correct or the hardware is production-ready.

---

## Adapting this guide for your device

The four-smoke-test sequence is general. Adapt it:

**If your device has no BLE:** Replace Smoke Test 4 with your actual wireless transport (Zigbee, WiFi MQTT, LoRa, CAN). The principle is the same — prove the wireless path with the simplest possible payload before the full algorithm.

**If your device has no sensor:** Replace Smoke Test 2 with your equivalent hardware readout (ADC reading, GPIO state, external device communication). The goal is the same — prove the hardware interface before the algorithm depends on it.

**If your device has multiple sensors:** Run Smoke Test 2 once per sensor. Stack them: counter → sensor 1 → sensor 2 → algorithm USB → algorithm wireless.

**If your wireless is unavailable in the dev environment:** Smoke Test 4 becomes a USB serial test with the wireless transport stubbed. Note this in your Stage 0 record and run the real wireless test in Stage 3 (field test).
