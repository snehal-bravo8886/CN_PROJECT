"""
Distributed UDP Log Aggregation — Member 2 SDN controller
Framework: Ryu, OpenFlow 1.3

UDP destination-port contract (must match Member 1):
  10000 DEBUG     -> OVS queue 0 (lowest)
  10001 INFO      -> OVS queue 1
  10002 WARNING   -> OVS queue 2
  10003 ERROR     -> OVS queue 3
  10004 CRITICAL  -> OVS queue 4 (highest)

IMPORTANT:
- Set BOTTLENECK_DPID and BOTTLENECK_PORT below to the actual switch/egress port.
- OVS queues are created separately by setup_queues.sh on that egress port.
- OpenFlow flow priority controls rule matching, NOT packet scheduling priority.
- The controller only selects OVS queues while congestion is detected.
"""

import os
import time
from collections import defaultdict

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, udp
from ryu.lib.packet import ether_types
from ryu.lib import hub


# ----------------------- TEAM CONFIGURATION -----------------------
# These values must come from live OVS/Mininet inspection. Never guess the port.
def _required_int_env(name):
    value = os.environ.get(name)
    if value is None or not value.strip():
        raise RuntimeError(
            f"Missing {name}. Inspect the live topology; see README_MEMBER2.md."
        )
    try:
        parsed = int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer, got {value!r}") from exc
    if parsed <= 0:
        raise RuntimeError(f"{name} must be greater than zero")
    return parsed

BOTTLENECK_DPID = _required_int_env("BOTTLENECK_DPID")
BOTTLENECK_PORT = _required_int_env("BOTTLENECK_PORT")
LINK_CAPACITY_BPS = _required_int_env("LINK_CAPACITY_BPS")
POLL_INTERVAL_SECONDS = 2
CONGESTION_ENTER_PERCENT = 80.0
CONGESTION_CLEAR_PERCENT = 60.0
# ------------------------------------------------------------------

UDP_PORT_TO_QUEUE = {
    10000: 0,  # DEBUG
    10001: 1,  # INFO
    10002: 2,  # WARNING
    10003: 3,  # ERROR
    10004: 4,  # CRITICAL
}

UDP_PORT_TO_SEVERITY = {
    10000: "DEBUG",
    10001: "INFO",
    10002: "WARNING",
    10003: "ERROR",
    10004: "CRITICAL",
}


class DistributedLogSDNController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(DistributedLogSDNController, self).__init__(*args, **kwargs)
        self.mac_to_port = defaultdict(dict)
        self.datapaths = {}
        self.last_port_bytes = {}
        self.last_port_sample_time = {}
        self.congested = False
        self.last_utilization = 0.0
        self.monitor_thread = hub.spawn(self._monitor)

    # ----------------------- OpenFlow helpers -----------------------

    def _add_flow(self, datapath, priority, match, actions, idle_timeout=0, cookie=0):
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        instructions = [
            parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)
        ]
        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            cookie=cookie,
            match=match,
            instructions=instructions,
            idle_timeout=idle_timeout
        )
        datapath.send_msg(mod)

    def _delete_dynamic_flows(self, datapath):
        """Delete learned/classification flows; preserve table-miss priority 0."""
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        mod = parser.OFPFlowMod(
            datapath=datapath,
            cookie=1,
            cookie_mask=0xffffffffffffffff,
            command=ofproto.OFPFC_DELETE,
            out_port=ofproto.OFPP_ANY,
            out_group=ofproto.OFPG_ANY,
            match=parser.OFPMatch()
        )
        datapath.send_msg(mod)

    def _install_table_miss(self, datapath):
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(
            ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER
        )]
        self._add_flow(datapath, 0, match, actions)

    def _queue_for_packet(self, udp_dst_port, out_port, datapath):
        if not self.congested:
            return None
        if datapath.id != BOTTLENECK_DPID or out_port != BOTTLENECK_PORT:
            return None
        return UDP_PORT_TO_QUEUE.get(udp_dst_port)

    # ----------------------- Switch lifecycle -----------------------

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            self.datapaths[datapath.id] = datapath
            self.logger.info("SWITCH_CONNECTED dpid=%s", datapath.id)
        elif ev.state == DEAD_DISPATCHER:
            self.datapaths.pop(datapath.id, None)
            self.logger.info("SWITCH_DISCONNECTED dpid=%s", datapath.id)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def _switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        self.datapaths[datapath.id] = datapath
        self._install_table_miss(datapath)
        self.logger.info("OPENFLOW_READY dpid=%s version=1.3", datapath.id)

    # ----------------------- Packet forwarding -----------------------

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match["in_port"]

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        if eth is None or eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        self.mac_to_port[datapath.id][eth.src] = in_port
        out_port = self.mac_to_port[datapath.id].get(eth.dst, ofproto.OFPP_FLOOD)

        actions = []
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        udp_pkt = pkt.get_protocol(udp.udp)
        queue_id = None
        severity = None

        if ip_pkt is not None and udp_pkt is not None:
            severity = UDP_PORT_TO_SEVERITY.get(udp_pkt.dst_port)
            queue_id = self._queue_for_packet(udp_pkt.dst_port, out_port, datapath)
            if severity:
                self.logger.info(
                    "LOG_PACKET severity=%s udp_dst=%s dpid=%s out_port=%s congested=%s queue=%s",
                    severity, udp_pkt.dst_port, datapath.id, out_port,
                    self.congested, queue_id if queue_id is not None else "baseline"
                )

        # Queue selection must precede output and only applies to the bottleneck egress.
        if queue_id is not None:
            actions.append(parser.OFPActionSetQueue(queue_id))
        actions.append(parser.OFPActionOutput(out_port))

        if out_port != ofproto.OFPP_FLOOD:
            fields = {
                "in_port": in_port,
                "eth_src": eth.src,
                "eth_dst": eth.dst
            }
            if ip_pkt is not None:
                fields.update({
                    "eth_type": ether_types.ETH_TYPE_IP,
                    "ipv4_src": ip_pkt.src,
                    "ipv4_dst": ip_pkt.dst
                })
                if udp_pkt is not None:
                    fields["ip_proto"] = 17
                    fields["udp_dst"] = udp_pkt.dst_port

            # Rule priority 100 is merely a flow-table match precedence.
            # The actual service differentiation is OVS queue selection.
            self._add_flow(
                datapath, 100, parser.OFPMatch(**fields), actions,
                idle_timeout=30, cookie=1
            )

        data = None if msg.buffer_id != ofproto.OFP_NO_BUFFER else msg.data
        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=data
        )
        datapath.send_msg(out)

    # ----------------------- Congestion monitoring -----------------------

    def _monitor(self):
        while True:
            for datapath in list(self.datapaths.values()):
                if datapath.id == BOTTLENECK_DPID:
                    parser = datapath.ofproto_parser
                    req = parser.OFPPortStatsRequest(
                        datapath, 0, BOTTLENECK_PORT
                    )
                    datapath.send_msg(req)
                    datapath.send_msg(parser.OFPFlowStatsRequest(datapath))
            hub.sleep(POLL_INTERVAL_SECONDS)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        datapath = ev.msg.datapath
        now = time.time()
        for stat in ev.msg.body:
            if datapath.id != BOTTLENECK_DPID or stat.port_no != BOTTLENECK_PORT:
                continue

            key = (datapath.id, stat.port_no)
            previous_bytes = self.last_port_bytes.get(key)
            previous_time = self.last_port_sample_time.get(key)
            self.last_port_bytes[key] = stat.tx_bytes
            self.last_port_sample_time[key] = now

            if previous_bytes is None or previous_time is None:
                continue

            elapsed = now - previous_time
            if elapsed <= 0:
                continue

            byte_delta = max(0, stat.tx_bytes - previous_bytes)
            tx_bps = (byte_delta * 8.0) / elapsed
            utilization = min(100.0, (tx_bps / LINK_CAPACITY_BPS) * 100.0)
            self.last_utilization = utilization

            self.logger.info(
                "BOTTLENECK_STATS dpid=%s port=%s tx_bps=%.0f utilization=%.1f%%",
                datapath.id, stat.port_no, tx_bps, utilization
            )

            if not self.congested and utilization >= CONGESTION_ENTER_PERCENT:
                self._set_congestion(True, utilization)
            elif self.congested and utilization <= CONGESTION_CLEAR_PERCENT:
                self._set_congestion(False, utilization)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        # Flow counters are logged for evidence/diagnostics. Port utilization
        # drives the congestion state transition in this starter controller.
        for stat in ev.msg.body:
            if stat.priority == 100 and stat.packet_count:
                self.logger.debug(
                    "FLOW_STATS dpid=%s priority=%s packets=%s bytes=%s",
                    ev.msg.datapath.id, stat.priority,
                    stat.packet_count, stat.byte_count
                )

    def _set_congestion(self, enabled, utilization):
        self.congested = enabled
        state = "CONGESTION_ENTERED" if enabled else "CONGESTION_CLEARED"
        self.logger.warning(
            "%s utilization=%.1f%% threshold_enter=%.1f%% threshold_clear=%.1f%%",
            state, utilization, CONGESTION_ENTER_PERCENT, CONGESTION_CLEAR_PERCENT
        )
        # Reinstall flows on the next packets using the new policy.
        for datapath in list(self.datapaths.values()):
            self._delete_dynamic_flows(datapath)
        self.logger.warning(
            "POLICY_CHANGED policy=%s queues=severity_based_on_bottleneck_only",
            "severity_priority" if enabled else "baseline"
        )
