# VM-E1 *Sparrow* — Interaction / Sequence Diagrams

> ⚠️ FULLY AI-GENERATED DUMMY EXAMPLE — NOT FOR REAL-WORLD USE. See [../README.md](../README.md).

Authored behaviours of the VM-E1, traceable to the [requirements](../requirements/requirements.yaml).

## 1. Throttle command → thrust (REQ-0100, REQ-0101, REQ-0102)

```mermaid
sequenceDiagram
    actor Pilot
    participant INCEPT as Inceptors
    participant FC as Flight Computer
    participant MCTRL as Motor Controller
    participant MOTOR as Electric Motor
    participant PROP as Propeller

    Pilot->>INCEPT: advance throttle
    INCEPT->>FC: throttle command
    FC->>MCTRL: torque/thrust setpoint
    MCTRL->>MCTRL: limit phase current (REQ-0101)
    MCTRL->>MOTOR: 3-phase drive
    MOTOR->>PROP: shaft torque
    PROP-->>Pilot: thrust
```

## 2. Battery fault → pilot annunciation (REQ-0111, REQ-0112, REQ-0203)

```mermaid
sequenceDiagram
    participant CELL as Cell Modules
    participant BMS as Battery Management System
    participant FC as Flight Computer
    participant DISP as Cockpit Display
    actor Pilot

    CELL->>BMS: cell temperature / voltage
    BMS->>BMS: detect over-temp / over-voltage (REQ-0111/0112)
    BMS->>FC: critical battery fault
    FC->>DISP: raise critical annunciation (REQ-0203)
    DISP-->>Pilot: warning within time limit
```

## 3. Loss of power → actuator fail-safe (REQ-0306)

```mermaid
sequenceDiagram
    participant ELEC as Electrical System
    participant ACT as Control Surface Actuator
    participant SURF as Control Surface

    ELEC--xACT: power loss
    ACT->>ACT: detect undervoltage
    ACT->>SURF: transition to defined safe position (REQ-0306)
    Note over ACT,SURF: DELIBERATE GAP — verified only by a FAILED test
```
