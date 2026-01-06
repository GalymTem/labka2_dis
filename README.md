# Distributed Key-Value Store with Eventual Consistency (Lab 2)

**Student Name:** [Your Name]  
**Date:** [06.01.26]

## Overview
This lab implements a replicated key-value store across 3 nodes (A, B, C) using eventual consistency, Lamport logical clocks, and Last-Writer-Wins (LWW) conflict resolution.  
Replication is done via direct HTTP calls between nodes. Anti-entropy/catch-up is handled on restart (or via gossip/status).

## Topology and Configuration

- **Node A**: Private IP `172.31.28.165`, Port `8000`, ID `A`
- **Node B**: Private IP `172.31.20.250`, Port `8001`, ID `B`
- **Node C**: Private IP `172.31.16.147`, Port `8002`, ID `C`

All nodes use private IPs for peer communication inside the VPC.

**Screenshot 1** – Three nodes running  
<img width="636" height="124" alt="Снимок экрана 2026-01-06 213720" src="https://github.com/user-attachments/assets/3becc986-7a28-49cc-9d59-710f7d599ffe" />
<img width="586" height="120" alt="Снимок экрана 2026-01-06 213723" src="https://github.com/user-attachments/assets/1c3956bb-ac04-4292-9508-335045a3148f" />
<img width="477" height="90" alt="Снимок экрана 2026-01-06 213727" src="https://github.com/user-attachments/assets/4014a4f5-bbc2-4c12-9d89-7b00e978643d" />


**Screenshot 2** – Connectivity check from Node A  
<img width="744" height="91" alt="Снимок экрана 2026-01-06 215304" src="https://github.com/user-attachments/assets/2aff0eb1-2a04-4221-a32d-35406646cc1c" />

## Basic Functionality (PUT / GET / STATUS)

1. PUT key `x` value `1` to Node A  
   Command:  
   python3 client.py --node http://172.31.28.165:8000 put x 1
   
   <img width="657" height="180" alt="Снимок экрана 2026-01-06 221227" src="https://github.com/user-attachments/assets/67adc41b-0a12-41a0-91da-e9b028d17d07" />

   GET key x from Node B
  Command:
  python3 client.py --node http://172.31.16.147:8002 status
<img width="919" height="174" alt="Снимок экрана 2026-01-06 221312" src="https://github.com/user-attachments/assets/b0092777-aded-4523-a9ee-536cf7c874ee" />

STATUS from Node C
Command:
python3 client.py --node http://172.31.16.147:8002 status
<img width="480" height="240" alt="Снимок экрана 2026-01-06 221327" src="https://github.com/user-attachments/assets/08cec9ab-fc4c-47a3-8570-41507fdabed6" />

**Scenario B: Concurrent Writes (Conflict Resolution)
Two near-simultaneous writes to the same key:
A: python3 client.py --node http://172.31.28.165:8000 put z 1
<img width="609" height="118" alt="image" src="https://github.com/user-attachments/assets/96f095b4-3461-4dcb-a06b-1b9843c14a01" />

B: python3 client.py --node http://172.31.20.250:8001 put z 2
<img width="199" height="119" alt="image" src="https://github.com/user-attachments/assets/a6e031a1-330b-4b08-8775-6825b353c12e" />

C: python3 client.py --node http://172.31.16.147:8002 status
<img width="627" height="248" alt="image" src="https://github.com/user-attachments/assets/7f0ff4fe-bffe-4496-81b4-6f29af3df243" />

**Results:
C:
<img width="469" height="113" alt="image" src="https://github.com/user-attachments/assets/df66c47d-254a-4667-801e-7df90393253b" />
B:
<img width="512" height="70" alt="image" src="https://github.com/user-attachments/assets/563a6e4f-8b14-4f66-92d2-b22b134addfb" />
C:
<img width="358" height="63" alt="image" src="https://github.com/user-attachments/assets/d253e869-74c2-4b2b-a45a-6b99499fef9a" />

** Stopped C
<img width="552" height="345" alt="image" src="https://github.com/user-attachments/assets/6b554faf-2671-4cba-8475-ea0a5fc0dcdc" />


A python3 client.py --node http://172.31.28.165:8000 put k 10
<img width="554" height="107" alt="image" src="https://github.com/user-attachments/assets/3ad2e0ed-8539-47ed-bce8-c30aae5b90fe" />

B python3 client.py --node http://172.31.20.250:8001 put m 20
<img width="540" height="101" alt="image" src="https://github.com/user-attachments/assets/9f90aa66-b640-4735-9cd0-40b50ce0c6e3" />

