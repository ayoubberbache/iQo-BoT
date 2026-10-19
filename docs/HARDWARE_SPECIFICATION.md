# IQO Bot — Physical Prototype & Hardware Specification

## 1. Hardware Architecture Overview

The IQO Bot workbench client is an autonomous, battery-operated, desk-mounted physical unit designed to monitor laboratory bench procedures, provide real-time audiovisual feedback, detect short circuits, and physically point to components or chemical apparatus.

```mermaid
flowchart TD
    subgraph Power["Power Management Subsystem"]
        Batt["18650 Li-ion Cell (3.7V, 2500 mAh)"] --> TP4056["TP4056 USB Type-C Charger & Protection"]
        TypeC["USB Type-C 5V Input"] --> TP4056
        TP4056 --> Boost["MT3608 DC-DC Boost Converter (Step-Up to 5.0V)"]
        Boost --> VCC5["5.0V Power Rail"]
        VCC5 --> LDO["ESP32-S3 Onboard 3.3V LDO"]
        LDO --> VCC33["3.3V Logic Rail"]
    end

    subgraph MCU["Central Microcontroller Node"]
        ESP["ESP32-S3 DevKit-C (Dual-Core Xtensa LX7, 8MB PSRAM, Wi-Fi/BLE)"]
    end

    subgraph Audio["Audiovisual Interface"]
        INMP["INMP441 I2S Digital Microphone"] -->|I2S In| ESP
        ESP -->|I2S Out| MAX["MAX98357A I2S Class D Amplifier"]
        MAX --> Speaker["4Ω 3W Dynamic Speaker"]
        ESP -->|SPI (25 FPS)| LCD["2.4' TFT LCD Display (ST7789, 240x320)"]
    end

    subgraph Sensors["Laboratory Sensing Suite"]
        INA["INA219 Current & Voltage Sensor"] -->|I2C (<20ms Short Alert)| ESP
        HCSR["HC-SR04 Ultrasonic Distance Sensor"] -->|GPIO Trigger/Echo| ESP
        DHT["DHT22 Temperature & Humidity"] -->|1-Wire GPIO| ESP
        LDR["LDR Ambient Light Sensor"] -->|ADC 12-bit| ESP
    end

    subgraph Actuators["Kinematic Pointer Arm"]
        ESP -->|PWM GPIO| Servos["3x MG90S Metal-Gear Micro Servos (3-DOF Arm)"]
        ESP -->|Digital Cutoff Pin| Relay["Power Cutoff Optocoupler / Relay"]
    end

    VCC5 --> Servos
    VCC5 --> MAX
    VCC5 --> LCD
    VCC33 --> ESP
    VCC33 --> INMP
    VCC33 --> INA
    VCC33 --> DHT
    VCC33 --> LDR
```

---

## 2. Complete Pinout Mapping Matrix (ESP32-S3)

The ESP32-S3 DevKit-C features 44 pins with flexible GPIO multiplexing. The pin assignments below avoid boot-strapping pin conflicts (GPIO 0, 45, 46) and optimize high-speed peripheral routing:

| Peripheral Module | Signal / Function | ESP32-S3 GPIO | Bus / Protocol | Notes & Voltage Tolerance |
| :--- | :--- | :--- | :--- | :--- |
| **INMP441 Microphone** | SCK (Bit Clock) | `GPIO 14` | I2S0 | 3.3V logic; Serial data clock |
| | WS (Word Select / LRCLK) | `GPIO 15` | I2S0 | Left/Right word synchronization |
| | SD (Serial Data) | `GPIO 16` | I2S0 | Audio data in |
| | L/R (Channel Select) | `GND` | Ground | Tied to GND for Left channel |
| **MAX98357A Amplifier** | BCLK (Bit Clock) | `GPIO 4` | I2S1 | 3.3V logic audio stream clock |
| | LRC (Word Select) | `GPIO 5` | I2S1 | Audio sample framing |
| | DIN (Data Input) | `GPIO 6` | I2S1 | PCM audio stream to speaker |
| | SD_MODE (Shutdown) | `3.3V` / `GPIO 7` | Digital Out | Active high enable |
| **ST7789 2.4" SPI LCD** | MOSI (SDA) | `GPIO 11` | SPI2 (FSPI) | High-speed SPI data line |
| | SCLK (SCL) | `GPIO 12` | SPI2 (FSPI) | Clock up to 40 MHz (DMA enabled) |
| | CS (Chip Select) | `GPIO 10` | SPI2 (FSPI) | Active low slave select |
| | DC (Data / Command) | `GPIO 9` | Digital Out | Low for command, high for data |
| | RST (Reset) | `GPIO 8` | Digital Out | Hardware reset line |
| | BL (Backlight PWM) | `GPIO 1` | LEDC PWM | Dimmable brightness control |
| **INA219 Current Sensor** | SDA | `GPIO 17` | I2C0 | 4.7kΩ pull-up to 3.3V |
| | SCL | `GPIO 18` | I2C0 | 4.7kΩ pull-up to 3.3V |
| | ALERT (Interrupt) | `GPIO 21` | GPIO IRQ | Instant overcurrent trip (<20 ms) |
| **HC-SR04 Proximity** | TRIG (Trigger) | `GPIO 38` | Digital Out | 10 µs high pulse |
| | ECHO (Echo) | `GPIO 39` | Digital In | Resistor divider: 5V -> 3.3V |
| **DHT22 Temp / Humidity**| DATA | `GPIO 40` | 1-Wire GPIO | 10kΩ pull-up to 3.3V |
| **LDR Photoresistor** | ANALOG | `GPIO 2` | ADC1_CH1 | Voltage divider with 10kΩ resistor |
| **Pointer Arm Servos** | Base Pan Servo | `GPIO 41` | LEDC PWM | 50 Hz PWM (0.5ms–2.5ms pulse) |
| | Shoulder Tilt Servo | `GPIO 42` | LEDC PWM | 50 Hz PWM |
| | Elbow Reach Servo | `GPIO 43` | LEDC PWM | 50 Hz PWM |
| **Bench Power Relay** | RELAY_TRIP | `GPIO 47` | Digital Out | High to open circuit on short detection |

---

## 3. Power Subsystem Design & Battery Runtime

### 3.1 Power Supply Topology
1. **Battery Cell:** Single 18650 Lithium-ion cell (nominal 3.7V, fully charged 4.2V, discharge cutoff 3.0V, rated capacity $C = 2500\text{ mAh} \approx 9.25\text{ Wh}$).
2. **Charging Controller:** TP4056 board with integrated DW01A battery protection IC and dual 8205A MOSFETs.
   - Charging input: Standard USB Type-C (5V @ 1.0A max).
   - Cutoff protection: 4.2V $\pm 1\%$ overcharge, 2.5V overdischarge cutoff, 3.0A short-circuit cutoff.
3. **Step-Up Boost Converter:** MT3608 DC-DC high-efficiency step-up module converting $3.0\text{V}–4.2\text{V} \rightarrow 5.0\text{V} \pm 2\%$.
   - Operating frequency: 1.2 MHz.
   - Typical efficiency: $\eta \approx 88\%–92\%$.

### 3.2 Power Consumption Breakdown

| Operating State | Active Peripherals | Average Current @ 5V | Power Consumption |
| :--- | :--- | :---: | :---: |
| **Idle / Standby** | ESP32-S3 (Wi-Fi connected), LCD dimmed, sensors polling (1 Hz) | **95 mA** | **475 mW** |
| **Active Monitoring** | Full sensor polling (20 Hz), LCD at 100% backlight, audio listening | **190 mA** | **950 mW** |
| **Interactive Peak** | Audio speaking (MAX98357A @ 1.5W), servos actively moving (3x MG90S) | **580 mA** | **2,900 mW** |
| **Weighted Average** | Assuming 60% standby, 30% monitoring, 10% speaking/moving | **172 mA** | **860 mW** |

### 3.3 Battery Autonomy Calculation
$$\text{Average Current from 3.7V Cell} = \frac{P_{avg}}{\eta \times V_{batt}} = \frac{0.860\text{ W}}{0.90 \times 3.7\text{ V}} \approx 258\text{ mA}$$

$$\text{Estimated Runtime} = \frac{2500\text{ mAh}}{258\text{ mA}} \times 0.90\text{ (derating)} \approx \mathbf{8.7\text{ Hours (Idle/Light)}} \quad \big/\quad \mathbf{\ge 3.5\text{ Hours (Heavy Continuous)}}$$

---

## 4. Bill of Materials (BOM) & Cost Tracking

All software tools, AI models, and IDEs are 100% open-source with **0 DZD (\$0.00)** licensing or cloud fees. Hardware component pricing is verified against academic laboratory stock and local electronics distributors:

| Item | Component Description | Qty | Est. Unit Price (DZD) | Est. Total (DZD) | Equivalent (USD) |
| :---: | :--- | :---: | :---: | :---: | :---: |
| 1 | ESP32-S3 DevKit-C N16R8 (8MB PSRAM, Wi-Fi/BLE) | 1 | 3,800 | 3,800 | \$28.00 |
| 2 | INMP441 Omnidirectional I2S Digital Microphone | 1 | 950 | 950 | \$7.00 |
| 3 | MAX98357A I2S 3W Class D Audio Amplifier Module | 1 | 850 | 850 | \$6.25 |
| 4 | 4Ω 3W Miniature Dynamic Speaker with enclosure | 1 | 450 | 450 | \$3.30 |
| 5 | 2.4-inch SPI TFT LCD Module (ST7789, 240x320) | 1 | 2,200 | 2,200 | \$16.20 |
| 6 | INA219 High-Side DC Current & Voltage Sensor Board | 1 | 900 | 900 | \$6.60 |
| 7 | HC-SR04 Ultrasonic Distance Sensor | 1 | 400 | 400 | \$2.95 |
| 8 | DHT22 (AM2302) Digital Temperature & Humidity Sensor | 1 | 800 | 800 | \$5.90 |
| 9 | 18650 3.7V 2500 mAh Li-ion Rechargeable Battery Cell | 1 | 950 | 950 | \$7.00 |
| 10 | TP4056 USB Type-C Li-ion Charging & Protection Board | 1 | 250 | 250 | \$1.85 |
| 11 | MT3608 2A DC-DC Boost Converter Module | 1 | 350 | 350 | \$2.60 |
| 12 | MG90S Metal-Gear Micro Servos (for 3-DOF Arm) | 3 | 450 | 1,350 | \$9.90 |
| 13 | 5V Optocoupler Solid-State / Electromechanical Relay | 1 | 350 | 350 | \$2.60 |
| 14 | Solderless Breadboard, Jumper Wire Ribbon (M-M, M-F) | 1 set | 600 | 600 | \$4.40 |
| 15 | Passive components (resistors, LDR, decoupling caps) | 1 set | 250 | 250 | \$1.85 |
| 16 | 3D-Printed Desktop Mounting Chassis (PETG/PLA) | 1 | 650 | 650 | \$4.80 |
| **Total** | **Base Physical Prototype Cost** | — | — | **14,800 DZD** | **~\$109.20** |
| **AI Software**| **Local SLM, PyTorch, Ollama, Whisper.cpp, Piper TTS**| — | **0 DZD** | **0 DZD** | **\$0.00** |

---

## 5. Mechanical Enclosure & Bench Integration

1. **Chassis Construction:** 3D-printed using high-impact PLA/PETG filament. The casing incorporates:
   - Front-facing 2.4" LCD bezel recessed by 1.5 mm to prevent bench scratching.
   - Acoustic resonance chamber for the 3W speaker ensuring clean vocal articulation up to 75 dB SPL.
   - Isolated microphone cavity with acoustic foam dampening to minimize ambient laboratory noise.
   - Articulated 3-DOF robotic arm mounting base positioned at the rear-center of the chassis.
2. **Thermal Dissipation:** Vented battery compartment physically isolated from the boost converter and microcontroller to comply with laboratory battery safety rules.
