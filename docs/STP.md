# Software Test Plan (STP)

**QoS Traffic Management System (UDP)** — TP-QOS-001 | Version 1.2 (repository edition)

PES University, Computer Networks | Team 10: SNEHAL AGRAWAL, TEJAS DIWAKAR, SIDDHANT CHAWLA

Repository edition adapted from the updated IEEE 829-format test plan (v1.1, November 2026). This edition corrects the recovery case status to reflect the current archived evidence; no new live Mininet execution is claimed.

## 1. Test plan identifier
TP-QOS-001 | QoS Traffic Management System (UDP) | Version 1.2

## 2. References
- [SRS-QOS-001](SRS.md), IEEE 829 Software Test Documentation (reference format), Team 10 requirements.
- [Integration report](integration/FINAL_INTEGRATION_REPORT.md), [application verification](../member1_udp_application/samples/verified_demo/), [baseline results](../member3_mininet_testing/results/).
- OpenFlow 1.3, OS-Ken, Mininet and OVS documentation.

## 3. Introduction
Verify the distributed UDP log aggregation system and its congestion-aware SDN QoS behavior. Cover the UDP application, Mininet topology, controller, OVS queues and analysis pipeline; separate documented results from additional evidence required for full evaluation.

## 4. Test items

| Module | Items under test |
| --- | --- |
| Member 1 | app/protocol.py, client.py, server.py, query_logs.py, compare_results.py; scripts/run_local_demo.py; tests/ |
| Member 2 | sdn_controller.py, setup_queues.sh, run_controller.sh, requirements.txt; OVS inspection |
| Member 3 | topology/topology.py, tests/congestion_test.sh, analysis/analyze.py, CSVs and graphs |
| Integration | H1–H4, S1, TCP 6653 controller, port 4 QoS, SQLite collection |

## 5. Software risk issues
- UDP loss or late arrivals can be confused with duplicates or missing trailing packets.
- Clock skew, buffering, VM speed or insufficient warm-up can distort latency and timing.
- Incorrect OpenFlow port, HTB setup or stale flows can invalidate evidence.
- Unequal baseline and QoS loads can produce misleading comparisons.

## 6. Features to be tested
- UDP generation, reception, validation, storage and loss (FR-1–6, FR-15, NFR-1).
- Topology, controlled load, OpenFlow forwarding (FR-7–9).
- Queue configuration, classification and policy (FR-10–14, NFR-2).
- Metrics, fairness and matched comparison (FR-16–17, NFR-3–4).

## 7. Features not to be tested
Internals of Python, SQLite, Mininet, OS-Ken, OVS; physical hardware; authentication, encryption, production deployment, TCP reliability, retransmission and multi-switch routing.

## 8. Approach
Run application, resilience, network and performance tests. Introduce H3 iperf3 load; compare matched FIFO (no HTB differentiation) and adaptive QoS trials at equal rates, packet sizes, durations and topology. Capture controller logs and OVS state before, during and after congestion.

| Scenario | Background offered rate | Purpose |
| --- | --- | --- |
| No load | 0 Mbps | Connectivity and delivery |
| Light | 0.5 Mbps | Recorded light baseline |
| Moderate | 1.5 Mbps | Recorded medium baseline |
| Heavy | 3 Mbps | Overload 2 Mbps bottleneck |
| Recovery | Stop background load | Verify return to baseline |

Archived baseline rates: 0.5, 1.5, 3 Mbps for approximately 30 s. Each application host attempted 300 logs (60/class). Preserve matching start offsets and workload. Follow the [integration guide](INTEGRATION.md).

## 9. Item pass/fail criteria
PASS: recorded or reported execution meets expectation. PARTIAL: some evidence or implementation is available but not the complete observed result. FAIL: observed result contradicts criteria. Evidence needed: insufficient execution evidence. A full evaluation pass requires all mandatory cases to pass.

## 10. Suspension and resumption
Suspend on controller startup failure, switch connection failure, server bind failure, Mininet crash or incorrect queue configuration. Stop test processes, clean the isolated Mininet lab with sudo mn -c, restart, verify port 4, connectivity and queues.

## 11. Test deliverables
Test plan and cases; application test output, demo CSV, sender summaries and SQLite query output; controller utilization/transition logs, OVS flows and queues; iperf logs, per-host/class CSVs and graphs; fairness/comparison results; final integration report and execution summary.

## 12. Remaining tasks
Repeat regression after changes. Archive absent-receiver and filtering results, raw policy recovery trace, matched FIFO/QoS measurements, per-class throughput/jitter and QoS fairness.

## 13. Environmental needs

| Category | Requirement |
| --- | --- |
| Hardware | Linux VM supporting concurrent Mininet processes; recommended ≥2 vCPU, ≥4 GB RAM |
| Software | Python 3.10+ app, Python 3.11 controller, os-ken==3.1.1, Mininet, OVS, iperf3, Matplotlib, SQLite |
| Network | H1–H4, DPID 1, port 4, 2 Mbps bottleneck, 10 ms delay, OpenFlow 1.3 TCP 6653 |
| Data | Fresh DB or session-isolated trials; sender summaries; matched rate, duration and workload; shared clock |

## 14. Staffing and training
Three team members execute tests in their areas. Familiarity with Python sockets, SQLite, Mininet CLI, iperf3 and OpenFlow/OVS inspection is required.

## 15. Responsibilities

| Role | Member | Responsibility |
| --- | --- | --- |
| UDP application | SNEHAL AGRAWAL | TC-01–06 |
| SDN controller | TEJAS DIWAKAR | TC-08–11 |
| Topology/evaluation | SIDDHANT CHAWLA | TC-07, TC-12–15 |
| Joint integration | Team 10 | TC-16–18 |

## 16. Schedule

| Activity | Planned duration |
| --- | --- |
| Plan and case design | 1 day |
| Module testing | 1 day |
| Integration and congestion tests | 1 day |
| Regression, comparison and documentation | 1 day |

Indicative repeat-execution schedule; historical dates/durations not supplied.

## 17. Risks and contingencies
Clean stale Mininet state and restart on setup failure; verify switch port and OpenFlow 1.3. Use pinned OS-Ken environment, not legacy Ryu instructions. Reconcile host/session/severity and unique rows if loss counts disagree. Discard comparisons with unequal offered loads.

## 18. Test case specification

| ID / SRS | Procedure | Expected result | Recorded result / status |
| --- | --- | --- | --- |
| TC-01 / FR-2 | Encode/decode valid record; check five ports | Round-trip; exact mapping | PASS: recorded tests OK |
| TC-02 / FR-5 | Feed malformed/oversized JSON, wrong severity, invalid host/sequence, overlong message | Invalid input rejected | PASS: recorded tests OK |
| TC-03 / FR-5 | Observe 1, 3, 2, 2; run resilience test | Gap closes; duplicate/late detected | PASS: 6 datagrams; 3 stored, 2 invalid, 1 duplicate |
| TC-04 / FR-1,3,4,6,15; NFR-1 | Run local demo and two-client suite | 25 valid logs, 5/class, zero lost | PASS: 25/25 |
| TC-05 / FR-6,15 | Query stats/filter CRITICAL; reconcile sender summaries | Correct count and loss/delay CSV | PARTIAL: demo CSV confirms 5/class; filter output not archived |
| TC-06 / FR-3 | Send UDP without receiver; examine counts | No false delivery claim; local errors if raised | Evidence needed |
| TC-07 / FR-7,8 | Launch Mininet; check H1–H4, port 4 and link settings | 2 Mbps, 10 ms, hosts reachable | PASS: final report confirms topology and delivery |
| TC-08 / FR-9 | Start OS-Ken; check OpenFlow and flows | OpenFlow 1.3 DPID 1, forwarding/classification | PASS: report confirms connection and five mappings |
| TC-09 / FR-10,11 | Apply HTB; inspect OVSDB and congested flows | Queues 0–4; SetQueue before output | PASS: report confirms mapping and HTB |
| TC-10 / FR-12,13,14; NFR-2 | Raise utilization to ≥80%; inspect logs | Congestion entered; priority active | PASS: report records ~100% and severity mode |
| TC-11 / FR-13,14; NFR-2 | Stop load; observe ≤60% and dump flows | Congestion cleared; baseline restored | PARTIAL: policy implemented; raw recovery trace or observed recovery result not archived |
| TC-12 / FR-8,15,16 | Light baseline at 0.5 Mbps | 600 logs; no background loss | PASS: 600/600, iperf 0% loss |
| TC-13 / FR-8,15,16 | Medium baseline at 1.5 Mbps | Record loss, delay, throughput and jitter | PASS: 600/600, 1.5 Mbps, 0.655 ms jitter |
| TC-14 / FR-8,15,16 | Heavy baseline at 3 Mbps | Saturation; loss and delay recorded | PASS: 343/600, 1.94 Mbps, 35% iperf loss |
| TC-15 / FR-16 | Analyze DB and summaries | Per-class latency/loss and iperf CSV/graphs | PASS: archived outputs; original DB not committed |
| TC-16 / FR-1–14 | Run all modules; query H4 | Five classes received; queue mappings confirmed | PASS: report records 50 logs, 10/class, ~12 ms, mappings |
| TC-17 / FR-17; NFR-3,4 | Repeat matched FIFO/QoS no/light, moderate and heavy | Compare per-class throughput, latency, jitter and loss | Evidence needed |
| TC-18 / FR-17; NFR-4 | Calculate Jain's index per trial | Class-level interpretation | PARTIAL: baseline J 1.0000, 1.0000, 0.9986; QoS counterpart not archived |

## 19. Test execution summary

| Metric | Recorded status |
| --- | --- |
| Cases designed | 18 |
| Recorded/reported PASS | 13 |
| Partially supported | 3 (TC-05, TC-11, TC-18) |
| Evidence needed | 2 (TC-06, TC-17) |
| Documented FAIL | 0 in reviewed evidence |
| Separate automated application suite | 10/10 passed in archived transcript |

The earlier v1.1 plan counted TC-11 as a pass; the current integration report confirms implementation of the recovery policy, not an archived observed recovery. This edition does not count it as a full pass.

| Baseline load | Application received/sent | iperf throughput | iperf jitter | iperf loss |
| --- | --- | --- | --- | --- |
| Light | 600/600 | 0.50 Mbps | 0.717 ms | 0% |
| Medium | 600/600 | 1.50 Mbps | 0.655 ms | 0% |
| Heavy | 343/600 | 1.94 Mbps | 2.173 ms | 35% |

## 20. Conclusion
The archived tests and integration report demonstrate UDP collection, Mininet connectivity, congestion activation and queue selection. Recovery behavior is implemented but needs independent execution evidence. Baseline experiments quantify congestion; matched QoS improvement requires corresponding measurements.

## 21. Approvals

| Name / role | Signature / date |
| --- | --- |
| SNEHAL AGRAWAL — Developer | |
| TEJAS DIWAKAR — Developer | |
| SIDDHANT CHAWLA — Developer | |
| Course instructor / evaluator | |

## Appendix A: Baseline evidence and fairness
The separate integrated run records 50 stored logs, approximately 12 ms per severity, and approximately 1.96 Mbps background throughput.

| Heavy baseline severity | Received/sent | Loss | Weighted mean delay | Delivery ratio |
| --- | --- | --- | --- | --- |
| DEBUG | 69/120 | 42.50% | 83.25 ms | 0.5750 |
| INFO | 69/120 | 42.50% | 80.09 ms | 0.5750 |
| WARNING | 72/120 | 40.00% | 86.68 ms | 0.6000 |
| ERROR | 64/120 | 46.67% | 59.97 ms | 0.5333 |
| CRITICAL | 69/120 | 42.50% | 76.20 ms | 0.5750 |

Jain's fairness index J = (sum x)² / (5 × sum x²), where x is each class's unique received/sent ratio. Light and medium: 1.0000; heavy: 0.9986. Heavy application loss is 257/600 = 42.83%. High delivery-ratio fairness does not imply low loss or successful prioritization.

Evidence: [per-class results](../member3_mininet_testing/results/log_analysis.csv), [host summary](../member3_mininet_testing/results/host_summary.csv), [iperf summary](../member3_mininet_testing/results/iperf_analysis.csv), [local automated results](../member1_udp_application/samples/verified_demo/automated_test_results.txt). Weighted delays are calculated from recorded per-host averages and received counts. The analysis script expects final-baseline.db, not committed. Use the [integration guide](INTEGRATION.md) for repeat trials; keep equal workload, duration and offsets; verify FIFO control separately, and record class-specific bytes, delays and jitter.
