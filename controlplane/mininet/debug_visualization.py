import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import os
import threading
import re
import subprocess
import time

from mininet.node import Host
from switch_p4 import SwitchP4
from linux_bridge import LinuxBridge

PORT_STATE_DISABLED = 0
PORT_STATE_BLOCKING = 1
PORT_STATE_LISTENING = 2
PORT_STATE_LEARNING = 3
PORT_STATE_FORWARDING = 4

class DebugVisualization:
    def __init__(self):
        self.g = nx.Graph()
        self.switch_port_to_remote = {}
        self.port_states = {}

    def add_edge(self, node1, node2, port1, port2):
        self.g.add_edge(node1, node2)
        self.switch_port_to_remote[node1, port1] = node2
        self.switch_port_to_remote[node2, port2] = node1

        if self.net.get(node1).__class__ == Host:
            self.port_states[node1, node2] = PORT_STATE_FORWARDING
        else:
            self.port_states[node1, node2] = PORT_STATE_BLOCKING
        if self.net.get(node2).__class__ == Host:
            self.port_states[node2, node1] = PORT_STATE_FORWARDING
        else:
            self.port_states[node2, node1] = PORT_STATE_BLOCKING

    def set_port_state(self, node, port, state):
        remote = self.switch_port_to_remote[node, port]
        self.port_states[node, remote] = state

    def draw(self, i):
        self.fig.clear()
        plt.axis("off")

        forwarding_links = []
        pending_links = []
        blocked_links = []
        disabled_links = []

        hosts = []
        running_switches = []
        stopped_switches = []

        for node in self.g.nodes():
            node_obj = self.net.get(node)
            if not node_obj: continue

            if node_obj.__class__ == Host:
                hosts.append(node)
                continue

            if node_obj.running == False:
                for n1, n2 in self.g.edges():
                    if n1 == node:
                        self.port_states[n1, n2] = PORT_STATE_FORWARDING
                    elif n2 == node:
                        self.port_states[n2, n1] = PORT_STATE_FORWARDING
                stopped_switches.append(node)
            else:
                running_switches.append(node)
                if node_obj.__class__ == LinuxBridge:
                    # Parse port states from command line.
                    lines = subprocess.check_output(["brctl", "showstp", "{}".format(node)]).splitlines()
                    current_port = None
                    for line in lines:
                        match = re.search("\((\d+)\)", line)
                        if match:
                            current_port = int(match.group(1))
                        else:
                            match = re.search("state[ \t]+([^ \t]+)", line)
                            if match:
                                assert current_port != None
                                state = None
                                state_str = match.group(1)
                                if state_str == "disabled":
                                    state = PORT_STATE_DISABLED
                                elif state_str == "blocking":
                                    state = PORT_STATE_BLOCKING
                                elif state_str == "listening":
                                    state = PORT_STATE_LISTENING
                                elif state_str == "learning":
                                    state = PORT_STATE_LEARNING
                                elif state_str == "forwarding":
                                    state = PORT_STATE_FORWARDING
                                assert state != None

                                remote = self.switch_port_to_remote[node, current_port]
                                self.port_states[node, remote] = state
                elif node_obj.__class__ == SwitchP4:
                    for port_no, interface in node_obj.intfs.items():
                        if not interface.IP():
                            remote = self.switch_port_to_remote[node, port_no]
                            state = node_obj.get_port_state(port_no)
                            if state == SwitchP4.PORT_STATE_FORWARDING:
                                translated_state = PORT_STATE_FORWARDING
                            elif state == SwitchP4.PORT_STATE_LEARNING:
                                translated_state = PORT_STATE_LEARNING
                            elif state == SwitchP4.PORT_STATE_DISCARDING:
                                translated_state = PORT_STATE_BLOCKING
                            else:
                                assert False
                            self.port_states[node, remote] = translated_state
                else:
                    assert False

        for n1, n2 in self.g.edges():
            first_state = self.port_states[n1, n2]
            second_state = self.port_states[n2, n1]

            if first_state == PORT_STATE_DISABLED or second_state == PORT_STATE_DISABLED:
                disabled_links.append((n1, n2))
                continue

            node1 = self.net.get(n1)

            try:
                with open(os.devnull, 'w') as devnull:
                    if not "UP" in subprocess.check_output(["ip", "link", "show", "{}-{}".format(n1, n2)], stderr=devnull):
                        disabled_links.append((n1, n2))
                        continue
                    if not "UP" in subprocess.check_output(["ip", "link", "show", "{}-{}".format(n2, n1)], stderr=devnull):
                        disabled_links.append((n1, n2))
                        continue
            except Exception as e:
                pass

            if first_state == PORT_STATE_BLOCKING or second_state == PORT_STATE_BLOCKING:
                blocked_links.append((n1, n2))
                continue

            if first_state == PORT_STATE_FORWARDING and second_state == PORT_STATE_FORWARDING:
                forwarding_links.append((n1, n2))
                continue

            pending_links.append((n1, n2))

        nx.draw_networkx_edges(self.g, self.pos, edgelist=disabled_links, style="dotted", width=1)
        nx.draw_networkx_edges(self.g, self.pos, edgelist=blocked_links, edge_color="#FF0000", width=2)
        nx.draw_networkx_edges(self.g, self.pos, edgelist=pending_links, edge_color="#FC8403", width=2)
        nx.draw_networkx_edges(self.g, self.pos, edgelist=forwarding_links, width=2)
        nx.draw_networkx_nodes(self.g, self.pos, nodelist=hosts, node_color="#0000FF")
        nx.draw_networkx_nodes(self.g, self.pos, nodelist=running_switches, node_color="#00FF00")
        nx.draw_networkx_nodes(self.g, self.pos, nodelist=stopped_switches, node_color="#808080")
        nx.draw_networkx_labels(self.g, self.pos)

    def run(self):
        self.fig = plt.figure()
        self.fig.canvas.toolbar.pack_forget()
        self.pos = nx.drawing.layout.spring_layout(self.g)
        anim = FuncAnimation(self.fig, self.draw, interval=500)
        plt.show()

    def start(self, net):
        self.net = net
        for src, dst in net.topo.links():
            ports = net.topo.port(src, dst)
            self.add_edge(src, dst, ports[0], ports[1])

        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        # Wait for user to close window.
        self.thread.join()
        time.sleep(0.5) # Workaround to weird matplotlib crash.



