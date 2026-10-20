#pragma once
#include <stdint.h>

// Verify these provisional ESP32 DevKit V1 assignments against the actual board/wiring.
static constexpr char DEVICE_ID[] = "RESQ-ESP32-001";
static constexpr char FIRMWARE_VERSION[] = "1.0.0";
static constexpr uint32_t SERIAL_BAUD = 115200;
static constexpr int PIN_I2C_SDA = 21, PIN_I2C_SCL = 22;
static constexpr uint8_t MPU6050_ADDRESS = 0x68;
static constexpr int PIN_MQ2_ADC = 32; // ADC1; input must be <= 3.3 V (prefer <= 3.1 V)
static constexpr int PIN_DHT22 = 4;
static constexpr int PIN_STATUS_LED = -1; // disabled until board/wiring verified
static constexpr int PIN_BUZZER = -1; // disabled until board/wiring verified

// Set only to a real, trusted fixed installation location. Zero/zero means unknown.
static constexpr double FIXED_LATITUDE = 0.0;
static constexpr double FIXED_LONGITUDE = 0.0;
inline bool hasConfiguredLocation() { return FIXED_LATITUDE>=-90.0 && FIXED_LATITUDE<=90.0 && FIXED_LONGITUDE>=-180.0 && FIXED_LONGITUDE<=180.0 && !(FIXED_LATITUDE==0.0 && FIXED_LONGITUDE==0.0); }

static constexpr uint32_t SENSOR_TICK_MS = 20;
static constexpr uint32_t MPU_SAMPLE_MS = 50;
static constexpr uint32_t MQ2_SAMPLE_MS = 250;
static constexpr uint32_t DHT_SAMPLE_MS = 2500;
static constexpr uint32_t TELEMETRY_INTERVAL_MS = 30000;
static constexpr uint32_t MQ2_WARMUP_MS = 60000; // increase to the module maker's full preheat time
static constexpr uint16_t MQ2_BASELINE_SAMPLES = 120;
static constexpr uint32_t MQ2_BASELINE_WINDOW_MS = 30000;
static constexpr uint16_t MQ2_WARNING_DELTA_ADC = 350;
static constexpr uint16_t MQ2_CRITICAL_DELTA_ADC = 800;
static constexpr uint16_t MQ2_HYSTERESIS_ADC = 100;
static constexpr uint32_t MQ2_PERSIST_MS = 5000;
static constexpr float TEMP_WARNING_C = 50.0f;
static constexpr float TEMP_CRITICAL_C = 60.0f;
static constexpr float TEMP_HYSTERESIS_C = 3.0f;
static constexpr uint32_t TEMP_PERSIST_MS = 10000;
static constexpr float IMPACT_THRESHOLD_G = 5.0f; // filtered total acceleration, including gravity
static constexpr float VIBRATION_THRESHOLD_G = 1.8f;
static constexpr uint8_t IMPACT_CONFIRM_SAMPLES = 3;
static constexpr uint32_t ALERT_REPEAT_COOLDOWN_MS = 60000;
static constexpr uint8_t OFFLINE_QUEUE_CAPACITY = 8;
static constexpr uint32_t WIFI_RETRY_BASE_MS = 1000;
static constexpr uint32_t WIFI_RETRY_MAX_MS = 60000;
static constexpr uint32_t HTTP_TIMEOUT_MS = 5000;
static constexpr uint32_t API_MIN_INTERVAL_MS = 1000;

// Copy secrets.example.h to secrets.h. HTTP is permitted only for an explicit local
// development URL; remote URLs must use HTTPS with certificate validation.
static constexpr bool ALLOW_INSECURE_LOCAL_HTTP = true;
static constexpr bool SIMULATION_MODE = false;
static constexpr bool ALLOW_SIMULATION_UPLOAD = false;
