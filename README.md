# SDN QoS Controller using Mininet and Ryu

## 📌 Objective

To implement a Software Defined Networking (SDN) controller that provides Quality of Service (QoS) by prioritizing different types of network traffic using OpenFlow rules.

---

## ⚙️ Requirements

* Ubuntu (20.04/22.04)
* Mininet
* Ryu Controller
* Python 3

---

## 🏗️ Topology

Single switch topology with 3 hosts:

* h1 (Server)
* h2 (Client - iperf)
* h3 (Client - HTTP)

---

## 🚀 How to Run

### 1. Start Ryu Controller

```bash
ryu-manager qos_controller.py
```

### 2. Start Mininet

```bash
sudo mn --topo single,3 --controller remote
```

### 3. Setup Servers (inside Mininet)

```bash
h1 iperf -s &
```

---

## 🔬 Test Scenarios

### 🔹 Scenario 1: Low Priority Traffic (iperf)

```bash
h2 iperf -c h1
```

### 🔹 Scenario 2: High Priority Traffic (HTTP)

```bash
h3 wget -O- http://10.0.0.1
```

### 🔹 Combined Test (QoS Demo)

```bash
h2 iperf -c h1 &
h3 wget -O- http://10.0.0.1
```

---

## 📊 QoS Logic

* HTTP traffic (port 8080) → HIGH PRIORITY (50)
* iperf traffic (port 5001) → LOW PRIORITY (5)
* Other traffic → MEDIUM PRIORITY (20)

Flow rules are installed dynamically using the controller.

---

## 📈 Observations

* HTTP traffic receives faster response compared to iperf traffic
* iperf throughput is reduced when HTTP traffic is active
* Flow rules with different priorities are visible in the switch

---

## 🔍 Flow Table Verification

```bash
sudo ovs-ofctl dump-flows s1
```

---

## 📸 Proof of Execution

Include screenshots of:

* Ryu controller logs
* Mininet terminal outputs (ping, iperf, wget)
* Flow table entries

---

## ⚠️ Notes

* Mininet hosts do not have internet access by default
* Always run `sudo mn -c` before starting a new session
* HTTP server uses port 8080 to avoid conflicts

---

## ✅ Conclusion

QoS is successfully implemented using SDN by classifying traffic based on port numbers and assigning different priorities through OpenFlow rules.
