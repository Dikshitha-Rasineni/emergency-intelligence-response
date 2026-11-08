#pragma once
#include <Arduino.h>
// SIM800L GPRS fallback (plain HTTP only; see config.h). Uses TinyGSM on UART2.
namespace GsmLink {
  void begin();
  bool ready();  // modem registered and GPRS attached
  bool post(const String& body, int& httpCode, String& response);
}
