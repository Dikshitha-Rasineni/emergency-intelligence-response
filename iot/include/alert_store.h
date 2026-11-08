#pragma once
// Persistent FIFO of serialized alert payloads. Survives reboot; an entry is removed only
// after the backend acknowledges it. Storage is abstracted so the logic is host-testable
// (NVS/Preferences on the ESP32, an in-memory map in host tests).
#include <stdint.h>
#include <stdio.h>
#include <string>

template <typename Storage>
class AlertStore {
 public:
  AlertStore(Storage& s, uint8_t slots) : st(s), cap(slots) {}
  uint32_t size() { return st.getU("tail") - st.getU("head"); }
  bool empty() { return size() == 0; }
  // Returns false if an older alert had to be overwritten (store full).
  bool push(const std::string& payload) {
    bool dropped = false;
    if (size() >= cap) { pop(); dropped = true; }
    uint32_t tail = st.getU("tail");
    st.putS(key(tail), payload);
    st.putU("tail", tail + 1);
    return !dropped;
  }
  bool peek(std::string& out) {
    if (empty()) return false;
    out = st.getS(key(st.getU("head")));
    return true;
  }
  void pop() {
    if (empty()) return;
    uint32_t head = st.getU("head");
    st.remove(key(head));
    st.putU("head", head + 1);
  }
 private:
  Storage& st; uint8_t cap;
  std::string key(uint32_t i) { char k[12]; snprintf(k, sizeof k, "a%u", (unsigned)(i % cap)); return k; }
};
