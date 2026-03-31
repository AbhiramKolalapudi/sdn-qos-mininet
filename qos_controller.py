from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, tcp


class QoSController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(QoSController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Table-miss flow
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(
            ofproto.OFPIT_APPLY_ACTIONS, actions)]

        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=inst,
            idle_timeout=15,   # flow removed if idle
            hard_timeout=60    # removed after 60 sec max
        )
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth.ethertype == 0x88cc:
            return

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        in_port = msg.match['in_port']
        dst = eth.dst
        src = eth.src

        # Learn MAC
        self.mac_to_port[dpid][src] = in_port

        # Decide output port
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # ---------------- QoS LOGIC ----------------
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        tcp_pkt = pkt.get_protocol(tcp.tcp)

        priority = 10  # default

        if ip_pkt and tcp_pkt:
            if tcp_pkt.dst_port == 80:
                self.logger.info("HTTP → HIGH PRIORITY")
                priority = 50
                match = parser.OFPMatch(
                    in_port=in_port,
                    eth_type=0x0800,
                    ip_proto=6,
                    tcp_dst=80
                )

            elif tcp_pkt.dst_port == 5001:
                self.logger.info("IPERF → LOW PRIORITY")
                priority = 5
                match = parser.OFPMatch(
                    in_port=in_port,
                    eth_type=0x0800,
                    ip_proto=6,
                    tcp_dst=5001
                )

            else:
                self.logger.info("Other TCP → MEDIUM PRIORITY")
                priority = 20
                match = parser.OFPMatch(
                    in_port=in_port,
                    eth_type=0x0800,
                    ip_proto=6
                )

        else:
            self.logger.info("Non-TCP → LOW PRIORITY")
            priority = 1
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)

        # Install flow
        if out_port != ofproto.OFPP_FLOOD:
            self.add_flow(datapath, priority, match, actions)

        # Send packet
        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=msg.data if msg.buffer_id == ofproto.OFP_NO_BUFFER else None
        )
        datapath.send_msg(out)
