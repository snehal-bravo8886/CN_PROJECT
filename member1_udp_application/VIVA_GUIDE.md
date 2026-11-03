# Member 1 — viva / code walk-through

## Explain the project in two sentences

Several UDP clients produce application logs and send them to one centralized server. An SDN controller (developed separately) should prioritize critical/error log traffic when the simulated network becomes congested, while Mininet supplies the isolated test environment.

## Explain your work

**Client:** \`app/client.py\` generates timestamped severity-tagged JSON logs and sends them with Python's \`socket.SOCK_DGRAM\` to one of five severity-specific destination ports. A sequence number increments separately for each severity, and a UUID separates multiple runs of the same client. Sender-summary JSON records how many packets the client successfully attempted.

**Server:** \`app/server.py\` binds five UDP sockets concurrently through \`selectors\`. Each arriving datagram is decoded and checked against the expected severity for that port; malformed, mismatched or duplicate logs are rejected. Valid new messages are stored persistently in SQLite with source address, arrival time and calculated delivery delay.

**Measurements:** \`app/query_logs.py\` filters stored logs; \`app/compare_results.py\` joins sender-summary counts to uniquely stored records so it can report loss (including missing last packets) by severity, plus mean delay.

## Key viva questions

**Why UDP instead of TCP?** It has low transport overhead and is explicitly the project protocol; UDP does not guarantee packet delivery or ordering. Under congestion, drops can happen, so we measure them.

**How does SDN identify which logs are critical?** Our client uses a fixed destination port per severity. Member 2 can match the UDP destination port in an OpenFlow rule; parsing JSON in the switch is unnecessary.

**Why sequence numbers?** They identify duplicates, out-of-order arrivals and apparent gaps within a stream. A sender summary is still required to detect packets dropped at the *end* of a stream.

**How do we know the server isn't receiving duplicate data?** The database enforces a uniqueness constraint on \`(host_id, session_id, severity, sequence)\` and the server maintains per-stream state.

**What does the database store?** Client/host, session, severity, sequence, sender timestamp, receiver timestamp, apparent delay, source IP/port and message.

**Why five UDP ports?** It makes severity visible to an OpenFlow controller with an ordinary port match, even though log contents are application JSON.

**Does OpenFlow's 'priority' field automatically give critical packets a faster queue?** No. Flow priority chooses which flow entry matches; actual egress service depends on configured queues and output actions. Member 2/3 must handle those.

**Why is loss zero locally?** The sample test ran over uncongested localhost. It is not proof of packet delivery under Mininet congestion or QoS success.

**How is delay measured?** \`(receive_ns - sent_ns) / 1e6\` milliseconds. With unsynchronized machines, this one-way timestamp subtraction can be misleading.

**What's not done?** Controller implementation, Mininet network, congestion detection demonstration and baseline vs priority measurements are pending the other two members.

## Commands to remember

\`\`\`bash
python3 -m unittest discover -s tests -v
python3 -m scripts.run_local_demo
python3 -m app.query_logs --db demo_output/logs.db --stats
python3 -m app.query_logs --db demo_output/logs.db --severity CRITICAL
\`\`\`
