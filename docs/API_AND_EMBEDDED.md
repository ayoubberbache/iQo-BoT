# IQO Bot — API Reference & Embedded C Integration

## 1. Web Dashboard & Server REST API

Both `chem/web_dashboard.py` and `elec/web_dashboard.py` expose high-performance, asynchronous REST endpoints for workbench client integration and remote telemetry.

### 1.1 Health Check Endpoint
- **Method:** `GET`
- **Path:** `/health`
- **Response Format:** `application/json`

```bash
curl -X GET http://localhost:8081/health
```

**Response (200 OK):**
```json
{
  "status": "ok",
  "domain": "chemistry"
}
```

---

### 1.2 Query Evaluation Endpoint
- **Method:** `POST`
- **Path:** `/api/query`
- **Content-Type:** `application/json`

**Request Payload:**
```json
{
  "question": "What happens if I add concentrated sulfuric acid directly to water?"
}
```

**Response Payload (200 OK):**
```json
{
  "topic": "water_into_acid",
  "intent": "WARNING",
  "safety": "WARNING",
  "source": "edgenet_onnx+llm_ollama",
  "lcd": [
    "ACID TO WATER   ",
    "NEVER REVERSE   "
  ],
  "led": "YELLOW",
  "arm": {
    "zone": "REAGENTS",
    "pan": -45,
    "tilt": 20,
    "reach_cm": 15
  },
  "tts": "Always add acid slowly to water while stirring. Adding water to concentrated acid causes violent exothermic boiling and dangerous acid splatter.",
  "latency_ms": {
    "guardrail": 0.35,
    "edge": 4.12,
    "llm": 182.4,
    "total": 186.87
  }
}
```

#### Field Definitions

| Field | Type | Description |
| :--- | :--- | :--- |
| `topic` | string | Internal classified domain topic key (e.g. `water_into_acid`, `resistor_code`, `short_circuit`). |
| `intent` | string | Pedagogical intention: `EXPLAIN`, `PROCEDURE`, `WARNING`, `CALCULATION`, `LOCATE`, `VERIFY`. |
| `safety` | string | Enforced safety state: `SAFE`, `WARNING`, or `CRITICAL`. |
| `source` | string | Processing pipeline source: `guardrail`, `edgenet_onnx`, `edgenet_torchscript`, or `+llm_ollama`. |
| `lcd` | array[string] | Exactly two strings representing Line 1 and Line 2 of a 16x2 character display (uppercase, padded to 16 chars). |
| `led` | string | RGB bench warning beacon color: `GREEN`, `YELLOW`, or `RED`. |
| `arm` | object | Computed inverse kinematics target: target `zone`, `pan` angle (-90° to +90°), `tilt` angle (0° to 90°), and `reach_cm`. |
| `tts` | string | Natural language speech synthesis string (max 45 words, optimized for clear spoken audio). |
| `latency_ms` | object | Latency breakdown across pipeline stages in milliseconds. |

---

## 2. Microcontroller Embedded C Integration

The IQO Bot training and export pipeline compiles the neural classifier into a self-contained, standalone C header file:
- `iqo_chem_embedded_config.h` (for Chemistry benches)
- `iqo_elec_embedded_config.h` (for Electronics benches)

This header eliminates the need for heavyweight runtime libraries (such as TensorFlow Lite for Microcontrollers or ONNX Runtime) and can be included directly in an **ESP-IDF** (C/C++) or **Arduino IDE** project.

### 2.1 Quantization Scheme
- **Weights ($W$):** 8-bit symmetric per-tensor integer quantization:
  $$W_{int8} = \text{clip}\left(\left\lfloor \frac{W_{fp32}}{S} \right\rceil, -127, 127\right), \quad S = \frac{\max(|W|)}{127}$$
- **Biases ($b$) & Normalization:** Preserved as 32-bit floating point (`float`) for numerical fidelity.
- **Flash Footprint:** Occupies less than 1.1 MB of microcontroller flash memory, easily fitting into ESP32-S3's 8MB/16MB flash space.

### 2.2 Embedded C Header Structure
```c
#pragma once
#include <stdint.h>

#define IQO_MAX_LEN 64
#define IQO_N_TOPICS 48
#define IQO_LCD_COLS 16

static const char IQO_CHARSET[] = " abcdefghijklmnopqrstuvwxyz0123456789-_.,+()[]/";
static const char* IQO_SAFETY[] = {"SAFE", "WARNING", "CRITICAL"};
static const char* IQO_LED[] = {"GREEN", "YELLOW", "RED"};
static const char* IQO_INTENT[] = {"EXPLAIN", "PROCEDURE", "WARNING", "CALCULATION", "LOCATE", "VERIFY"};
static const char* IQO_ARM_NAME[] = {"REST", "ZONE_A", "ZONE_B", "REAGENTS", "WASTE", "MULTIMETER"};
static const int16_t IQO_ARM_PAN_TILT_REACH[][3] = {
    {0, 0, 0}, {-30, 20, 15}, {30, 20, 15}, {-45, 20, 15}, {45, 10, 20}, {0, 15, 12}
};

/* Quantized 1D Convolution weights */
static const int8_t W_conv3_weight[12288] = { /* ... int8 values ... */ };
static const float W_conv3_weight_SCALE = 0.0078125f;
static const float W_conv3_bias[64] = { /* ... float values ... */ };
```

### 2.3 ESP32-S3 Execution Example (Arduino C++)

```cpp
#include "iqo_chem_embedded_config.h"

// Tokenize student input text string into character IDs
void tokenize_query(const char* text, int32_t* token_buffer) {
    for (int i = 0; i < IQO_MAX_LEN; i++) {
        token_buffer[i] = 0; // Pad token
    }
    int len = strlen(text);
    if (len > IQO_MAX_LEN) len = IQO_MAX_LEN;
    
    for (int i = 0; i < len; i++) {
        char c = tolower(text[i]);
        const char* p = strchr(IQO_CHARSET, c);
        if (p) {
            token_buffer[i] = (int32_t)(p - IQO_CHARSET) + 2; // Token index offset
        } else {
            token_buffer[i] = 1; // Unknown token
        }
    }
}

void setup() {
    Serial.begin(115200);
    int32_t tokens[IQO_MAX_LEN];
    tokenize_query("bleach and ammonia", tokens);
    
    // Run forward inference with quantized weights in flash
    // Direct pointer arm kinematic positioning:
    int zone_idx = 3; // Example: REAGENTS
    int16_t pan = IQO_ARM_PAN_TILT_REACH[zone_idx][0];
    int16_t tilt = IQO_ARM_PAN_TILT_REACH[zone_idx][1];
    int16_t reach = IQO_ARM_PAN_TILT_REACH[zone_idx][2];
    
    Serial.printf("Arm Coordinates -> Pan: %d, Tilt: %d, Reach: %d cm\n", pan, tilt, reach);
}

void loop() {
    // Sensor monitoring and I2S audio loop
}
```
