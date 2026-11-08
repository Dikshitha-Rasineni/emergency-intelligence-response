#include <cassert>
#include <cstdio>
#include <map>
#include "alert_store.h"

struct MemStorage {  // stands in for ESP32 NVS
  std::map<std::string, std::string> s; std::map<std::string, uint32_t> u;
  uint32_t getU(const char* k) { return u.count(k) ? u[k] : 0; }
  void putU(const char* k, uint32_t v) { u[k] = v; }
  std::string getS(const std::string& k) { return s.count(k) ? s[k] : ""; }
  void putS(const std::string& k, const std::string& v) { s[k] = v; }
  void remove(const std::string& k) { s.erase(k); }
};

int main() {
  MemStorage nvs;
  {
    AlertStore<MemStorage> q(nvs, 3);
    assert(q.empty());
    assert(q.push("A") && q.push("B"));
    std::string out; assert(q.peek(out) && out == "A");
    // failed delivery: peek again, nothing removed
    assert(q.peek(out) && out == "A" && q.size() == 2);
  }
  {  // "reboot": a new store object over the same NVS keeps pending alerts in order
    AlertStore<MemStorage> q(nvs, 3);
    std::string out; assert(q.size() == 2 && q.peek(out) && out == "A");
    q.pop(); assert(q.peek(out) && out == "B");
    assert(q.push("C") && q.push("D"));       // B C D (full)
    assert(!q.push("E"));                      // overwrites oldest (B), reports the drop
    assert(q.peek(out) && out == "C" && q.size() == 3);
    q.pop(); q.pop(); q.pop(); assert(q.empty() && !q.peek(out));
  }
  std::puts("alert_store_test: all cases passed");
}
