# Distributed Log Aggregation System (UDP + SDN)

**Computer Networks team project** — Python UDP sockets · Open vSwitch · Software-Defined Networking · Mininet

## Project goal

Multiple computers send DEBUG, INFO, WARNING, ERROR, and CRITICAL logs over UDP to a central log collector. When network congestion happens, an SDN controller should prioritize important logs. The team will compare loss and delay with and without prioritization.

## Member ownership and current status

| Folder | Member | Responsibilities | Status |
|---|---|---|---|
| [member1_udp_application/](member1_udp_application/) | **Member 1** | UDP clients/server, timestamped logs, sequence tracking, SQLite, statistics, unit/integration tests | **Implemented; 10/10 tests passed locally** |
| [member2_sdn_controller/](member2_sdn_controller/) | **Member 2** | Controller, congestion monitoring, OpenFlow 1.3 rules, OVS QoS queue assignment | **Pending implementation** |
| [member3_mininet_testing/](member3_mininet_testing/) | **Member 3** | Topology, bottleneck and congestion experiments, integration, performance graphs | **Pending implementation** |
| [docs/](docs/) | Shared | Protocol specification, integration and acceptance checklist | Prepared |

**Important:** The successful local UDP demonstration does not establish that SDN prioritization or Mininet integration works. Those are separate team tasks.

## Running Member 1 locally

Requires Python 3.10+ (standard library only). Open a terminal at the repository root:

```bash
cd member1_udp_application
python3 -m unittest discover -s tests -v
python3 -m scripts.run_local_demo
python3 -m app.query_logs --db demo_output/logs.db --stats
python3 -m app.query_logs --db demo_output/logs.db --severity CRITICAL
```

The local demo runs two clients and stores 25 messages from five severities. It uses UDP ports **18000–18004** locally. The default ports for integration are **10000–10004**.

## Agreed severity-to-port mapping

| Severity | UDP destination port | Priority |
|---|---:|---|
| DEBUG | 10000 | Lowest |
| INFO | 10001 | Low |
| WARNING | 10002 | Medium |
| ERROR | 10003 | High |
| CRITICAL | 10004 | Highest |

One UDP datagram carries a JSON object with `version`, `host_id`, `session_id`, `severity`, `sequence`, `sent_ns`, and `message`. See [docs/INTEGRATION.md](docs/INTEGRATION.md) for the handoff contract and full-team verification requirements.

## How teammates contribute

Each member changes files in **their own folder**, preferably on separate branches such as `member2-controller` or `member3-mininet`. Open pull requests to merge with `main`. Discuss IP addressing, controller versions, OVS queue IDs and link port selection before running the combined demo.

**Commit source, docs and small representative outputs.** Do not commit generated SQLite databases, Python caches or temporary output directories.
