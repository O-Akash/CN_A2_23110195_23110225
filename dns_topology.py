from mininet.net import Mininet
from mininet.node import Controller, OVSSwitch, Host
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from mininet.cli import CLI

def custom_topology():
    info('*** Creating network\n')
    net = Mininet(controller=Controller, link=TCLink, switch=OVSSwitch, build=False)
    info('*** Adding controller\n')
    net.addController('c0')
    info('*** Adding hosts\n')
    h1 = net.addHost('h1', ip='10.0.0.1/24')
    h2 = net.addHost('h2', ip='10.0.0.2/24')
    h3 = net.addHost('h3', ip='10.0.0.3/24')
    h4 = net.addHost('h4', ip='10.0.0.4/24')
    dns = net.addHost('dns', ip='10.0.0.5/24')
    info('*** Adding switches\n')
    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')
    s3 = net.addSwitch('s3')
    s4 = net.addSwitch('s4')
    info('*** Creating links with bandwidth and delay\n')
    net.addLink(h1, s1, bw=100, delay='2ms')
    net.addLink(h2, s2, bw=100, delay='2ms')
    net.addLink(h3, s3, bw=100, delay='2ms')
    net.addLink(h4, s4, bw=100, delay='2ms')
    net.addLink(s2, dns, bw=100, delay='1ms')
    net.addLink(s1, s2, bw=100, delay='5ms')
    net.addLink(s2, s3, bw=100, delay='8ms')
    net.addLink(s3, s4, bw=100, delay='10ms')
    info('*** Adding and configuring NAT\n')
    net.addNAT(ip='10.0.0.254').configDefault()
    net.build()
    net.start()
    info('*** Setting default routes for hosts\n')
    for h in [h1, h2, h3, h4, dns]:
        h.cmd('ip route add default via 10.0.0.254')
    info('*** Running CLI\n')
    CLI(net)
    info('*** Stopping network\n')
    net.stop()
if __name__ == '__main__':
    setLogLevel('info')
    custom_topology()