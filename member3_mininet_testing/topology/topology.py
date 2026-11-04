from mininet.topo import Topo
from mininet.link import TCLink


class LogTopology(Topo):

    def build(self):

        h1 = self.addHost('h1', ip='10.0.0.1/24')
        h2 = self.addHost('h2', ip='10.0.0.2/24')
        h3 = self.addHost('h3', ip='10.0.0.3/24')
        h4 = self.addHost('h4', ip='10.0.0.4/24')

        s1 = self.addSwitch('s1')

        self.addLink(h1, s1, cls=TCLink, bw=10)
        self.addLink(h2, s1, cls=TCLink, bw=10)
        self.addLink(h3, s1, cls=TCLink, bw=10)

        self.addLink(
            s1, h4,
            cls=TCLink,
            bw=2,
            delay='10ms',
            max_queue_size=50
        )


topos = {
    'logtopo': (lambda: LogTopology())
}



