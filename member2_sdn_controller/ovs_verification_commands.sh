# Open vSwitch / OpenFlow 1.3 verification and setup notes

# Set bridge protocol to OpenFlow 1.3 (replace s1 if needed)
sudo ovs-vsctl set bridge s1 protocols=OpenFlow13

# Show switch ports and OpenFlow port numbers
sudo ovs-ofctl -O OpenFlow13 show s1

# Show installed flow rules
sudo ovs-ofctl -O OpenFlow13 dump-flows s1

# Inspect QoS/queues
sudo ovs-vsctl list Port <BOTTLENECK_PORT_NAME>
sudo ovs-vsctl list QoS
sudo ovs-vsctl list Queue

# Remove QoS from a port if you need to reset/reconfigure (careful: this removes that port's QoS attachment)
sudo ovs-vsctl --if-exists clear Port <BOTTLENECK_PORT_NAME> qos
