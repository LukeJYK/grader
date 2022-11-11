from simulator.node import Node
import json, math, pprint

pp = pprint.PrettyPrinter(indent=4)


class Link_State_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        # will map from frozenset((source, destination)) -> (sequence #, latency)
        # The use of frozenset makes the order of the 2 nodes irrelevant
        self.link_states = {}

    # Return a string
    def __str__(self):
        return "\n" + pp.pformat(self.link_states) + "\n"

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        # latency = -1 if delete a link
        link = frozenset((self.id, neighbor))
        # update local link_state
        new_seq_no = 0
        if link in self.link_states:
            past_seq, past_latency = self.link_states[link]
            new_seq_no = past_seq + 1
        self.link_states[link] = (new_seq_no, latency)
        # tell neighbors
        self.broadcast_update(self.id, neighbor, new_seq_no, latency)
        # If link connects to a node that I've never seen, ## or to a once-isolated node that connects back
        # then send it my full list of linkstates.
        # This allows new nodes to catch up on past broadcasts.
        if new_seq_no == 0 or past_latency == -1:
            for old_link, seq_and_latency in self.link_states.items():
                if old_link != link:
                    ll = list(old_link)
                    self.broadcast_update(ll[0], ll[1],
                                          seq_and_latency[0], seq_and_latency[1],
                                          neighbor)

    # Fill in this function
    def process_incoming_routing_message(self, m):
        # decode message
        src, dst, seq_no, latency = json.loads(m)
        # check whether it's new
        link = frozenset((src, dst))
        if link in self.link_states:
            past_seq, null = self.link_states[link]
            if seq_no <= past_seq:
                # stop because it's an old message
                return
        # if we got here, the message is new
        # record it locally
        self.link_states[link] = (seq_no, latency)
        # send to neighbors
        self.broadcast_update(src, dst, seq_no, latency)

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        """Solve shortest path using Dijkstra's algorithm, using current link_states."""
        # build set of vertices
        nodes = set()
        for l in self.link_states:
            nodes.update(l)
        # build adjacency list for each node:  node -> set((neighbor1, latency1),...)
        adjacent_nodes = {n: set() for n in nodes}
        for l, value in self.link_states.items():
            for n in l:  # for both of the two nodes in the link
                other_node, = l.difference([n])
                latency = value[1]
                if latency >= 0:
                    adjacent_nodes[n].update([(other_node, latency)])
        # Dijkstra's algorithm initialization
        dist = {n: 0 if n == self.id else math.inf for n in nodes}
        prev = {n: None for n in nodes}
        unvisited = set(nodes)

        while len(unvisited) > 0:
            # get closest unvisisted node (not the most efficient implementation)
            unvisited_dist = {n: dist[n] for n in unvisited}
            visit = min(unvisited_dist, key=unvisited_dist.get)
            # relax edges adjacent to the visited node
            for neighbor, latency in adjacent_nodes[visit]:
                # try both forward and backward directions
                for u, v in ((visit, neighbor), (neighbor, visit)):
                    candidate_len = dist[u] + latency
                    if candidate_len < dist[v]:
                        dist[v] = candidate_len
                        prev[v] = u
            # remove visited node
            unvisited.remove(visit)

            # trace back path from the destination
        if len(prev) == 0 or prev[destination] == None:
            return -1
        p = destination
        while prev[p] != self.id:
            p = prev[p]
        return p

    def broadcast_update(self, src, dst, seq_no, latency, neighbor="all"):
        message = json.dumps([src, dst, seq_no, latency])
        if neighbor == "all":
            self.send_to_neighbors(message)
        else:
            self.send_to_neighbor(neighbor, message)