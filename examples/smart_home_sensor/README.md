# Example: Smart Home PIR Occupancy Sensor

**Status:** Skeleton — domain primitives and stage gate structure defined. Implementation not yet started.  
**Purpose:** This example demonstrates how to apply Crucible to a simpler, more accessible device than GaitSense. A PIR occupancy sensor is a good onboarding device: cheap dev kit, clear domain primitives, measurable output.

---

## Domain primitives

```
1. Occupancy state (binary: occupied / unoccupied)
   — the ground truth the device is trying to measure
   
2. Occupancy transition latency (ms)
   — time from physical motion to reported state change
   — traces to: PIR pyroelectric settling time + firmware debounce window
   
3. False-positive rate (%)
   — unoccupied room classified as occupied
   — traces to: PIR detection cone geometry + IR noise floor + debounce threshold
```

---

## Device purpose statement

> The PIR occupancy sensor detects human presence in a room and reports it to a home automation hub. A false negative (occupied room reported as empty) causes unnecessary HVAC/lighting shutoff. A false positive (empty room reported as occupied) wastes energy. Both errors are measurable; neither is acceptable above the validated threshold. The device must achieve < 2% false-positive rate and < 500 ms occupancy transition latency under all ambient light and temperature conditions the room will encounter.

---

## Stage gate sequence

```
Stage 0: HIL Toolchain Lock
         Counter → PIR digital readout → occupancy FSM USB → occupancy BLE/Zigbee
         
Stage 1: Simulation
         PIR output model (detection cone + noise floor) → occupancy FSM validation
         Feed field data: replay recorded PIR event logs to verify FSM correctness
         
Stage 2: Firmware Integration
         Occupancy FSM on dev kit, USB serial validation
         False-positive test: empty room, 15 minutes, count spurious triggers
         Transition latency test: hand break at measured distance, log latency
         
Stage 3: Field Test
         Real room, varied conditions (different temperatures, sunlight angles)
         Data captured, replayed in simulation to update PIR noise model
         
Stage 4: Host Integration
         Home Assistant via MQTT or Matter
         Automation trigger test: light turns on within 1s of occupancy detected
```

---

## Recommended dev kit

Any microcontroller with:
- Digital GPIO (for PIR output) or ADC (for analog PIR)
- BLE, Zigbee, or WiFi (for wireless transport)
- USB serial (for Stages 0–2)

Good starting points: Seeed XIAO nRF52840 (BLE), Espressif ESP32-C3 (WiFi/BLE), Nordic nRF52840 DK (BLE/Zigbee).

PIR module: HC-SR501 (~$2) is the simplest. AM312 is smaller for enclosure-constrained builds.

---

## What needs to be built

This example is a skeleton. Contributions welcome:

- [ ] `amendments.md` — at minimum the four mandatory Amendments adapted for PIR domain
- [ ] `toolchain_config.md` — hardware record, pin map, toolchain registration
- [ ] Stage 0 smoke test firmware (counter + PIR readout + occupancy FSM USB + occupancy BLE)
- [ ] Stage 1 simulation — PIR output model and occupancy FSM validation
- [ ] Stage 3 field test data and field-to-simulation replay example
- [ ] Stage 4 Home Assistant integration guide

If you build this out, the contribution would be the second complete device example in the Crucible repository. See [CONTRIBUTING.md](../../CONTRIBUTING.md) for the PR format.
