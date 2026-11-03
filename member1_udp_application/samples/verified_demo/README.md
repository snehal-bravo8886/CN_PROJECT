# Local verification snapshot

These are **representative recorded outputs from a real localhost run** of Member 1's UDP application and its tests, **not** results of an SDN/Mininet congestion experiment.

- \`automated_test_results.txt\`: 10/10 tests passed.
- \`terminal_output.txt\`: two clients h1/h2 send 15+10 UDP logs, server stores 25/25.
- \`h1_summary.json\` and \`h2_summary.json\`: sender-side counts.
- \`metrics.csv\`: received and loss/delay per severity.

The generated SQLite database is **not committed**; re-create your own reproducibly with:

\`\`\`bash
cd member1_udp_application
python3 -m scripts.run_local_demo
\`\`\`

Actual delays depend on the system and are *not* predictions of network performance. Some paths in historical terminal output show the environment where the sample was recorded.
