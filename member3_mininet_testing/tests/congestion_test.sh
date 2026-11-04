
#!/bin/bash

echo "Starting congestion test..."

echo "Starting UDP server on H4"

iperf3 -s -p 5201 &

sleep 2

echo "Starting traffic from H1"

iperf3 -c 10.0.0.4 -u -b 1M -t 30 -p 5201 &

echo "Starting traffic from H2"

iperf3 -c 10.0.0.4 -u -b 2M -t 30 -p 5201 &

echo "Starting traffic from H3"

iperf3 -c 10.0.0.4 -u -b 3M -t 30 -p 5201 &

wait

echo "Congestion test completed."



