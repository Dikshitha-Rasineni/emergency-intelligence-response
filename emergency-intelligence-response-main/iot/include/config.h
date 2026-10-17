#pragma once

#include <Arduino.h>

// Detected hardware: ESP32 DevKit V1 / ESP32-D0WD-V3 rev 3.1.
static constexpr char DEVICE_ID[] = "RESQ-ESP32-001";
static constexpr char FIRMWARE_VERSION[] = "0.2.0";
// Re-check with `ipconfig` whenever the backend PC receives a new DHCP address.
static constexpr char API_BASE_URL[] = "http://10.3.213.89:8000";
static constexpr char API_PATH[] = "/api/v1/iot/events";

// Pin map is based on the supplied RESQ.AI wiring diagram.
static constexpr int I2C_SDA_PIN = 21;
static constexpr int I2C_SCL_PIN = 22;
static constexpr uint8_t MPU6050_PRIMARY_ADDRESS = 0x68;
static constexpr uint8_t MPU6050_ALT_ADDRESS = 0x69;
static constexpr int DHT_PIN = 4;
static constexpr int FSR_PIN = 34;             // analog pressure/force sensor
static constexpr int SOUND_PIN = 35;           // analog sound module output
static constexpr int MQ2_PIN = 32;             // MQ-2 AO; must be <=3.3 V
static constexpr int WATER_PIN = -1;           // no water sensor shown in diagram
static constexpr int SIM800L_RX_PIN = 16;      // ESP32 RX2 <- SIM800L TXD
static constexpr int SIM800L_TX_PIN = 17;      // ESP32 TX2 -> SIM800L RXD
static constexpr uint32_t SIM800L_BAUD = 9600;
static constexpr int SOS_PIN = 5;
static constexpr int STATUS_LED_PIN = -1;      // GPIO2 is used by DIP SW3 in the diagram
static constexpr int BUZZER_PIN = 12;
static constexpr bool HAS_DHT = true;
static constexpr bool HAS_FSR = true;
static constexpr bool HAS_SOUND = true;
static constexpr bool HAS_MQ2 = true;
static constexpr bool HAS_WATER_SENSOR = false;
static constexpr bool HAS_SIM800L = true;
static constexpr bool HAS_SOS = false;
static constexpr bool HAS_STATUS_LED = false;
static constexpr bool HAS_BUZZER = true;

// Set genuine fixed installation coordinates for a stationary testbed.
static constexpr double FIXED_LATITUDE = 0.0;
static constexpr double FIXED_LONGITUDE = 0.0;

static constexpr uint32_t IMPACT_SAMPLE_MS = 10;
static constexpr uint32_t DHT_SAMPLE_MS = 2200;
static constexpr uint32_t ANALOG_SAMPLE_MS = 100;
static constexpr uint32_t TELEMETRY_INTERVAL_MS = 30000;
static constexpr uint32_t WIFI_RETRY_MS = 10000;
static constexpr uint32_t HTTP_TIMEOUT_MS = 5000;
static constexpr uint32_t EMERGENCY_COOLDOWN_MS = 60000;
static constexpr uint8_t IMPACT_QUALIFYING_SAMPLES = 2;
static constexpr float IMPACT_THRESHOLD_G = 5.0f;
static constexpr float FIRE_SMOKE_THRESHOLD_PPM = 1500.0f;
static constexpr float FIRE_TEMPERATURE_C = 60.0f;
static constexpr float FLOOD_WATER_CM = 50.0f;

// MQ-2 raw ADC is not ppm. These coefficients are placeholders for calibration.
static constexpr float MQ2_SLOPE_PPM_PER_ADC = 1.0f;
static constexpr float MQ2_BASELINE_ADC = 0.0f;
static constexpr uint32_t MQ2_WARMUP_MS = 60000;

static constexpr float WATER_CM_PER_ADC = 0.1f;
static constexpr float WATER_ADC_OFFSET = 0.0f;
static constexpr uint32_t SIM800L_POLL_MS = 30000;
static constexpr uint32_t SIM800L_TIMEOUT_MS = 1200;
static constexpr uint8_t EVENT_QUEUE_CAPACITY = 8;
static constexpr uint32_t QUEUE_DRAIN_INTERVAL_MS = 5000;
static constexpr bool SIMULATION_MODE = false;