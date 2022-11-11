from simulator.node import Node
import json
import math


class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.costs = {self.id: [0, [self.id]]}  # the cost to each neighbor {id: cost}
        self.dv = {self.id: [0, [self.id]]}  # distance vector of itself
        self.dvs = {}
        self.seq = 0
        # dvs = {id: [seq, dv]}
        # dv = {id: [latency, [paths]]}
        # msg = {id: str, seq: str, dv: array}

    # Return a string
    def __str__(self):
        return json.dumps({'id': self.id, 'dv': self.dv})

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        if latency == -1:
            latency = math.inf
        self.costs[neighbor] = [latency, [self.id, neighbor]]
        self.update_dv()

    # Fill in this function
    def process_incoming_routing_message(self, m):
        msg = json.loads(m)
        src_id, src_seq, src_dv = int(msg['id']), int(msg['seq']), msg['dv']
        if src_id not in self.dvs or self.dvs[src_id][0] < src_seq:
            self.dvs[src_id] = [src_seq, src_dv]
            self.update_dv()

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        if destination in self.dv:
            return self.dv[destination][1][1]
        else:
            return -1

    def update_dv(self):
        new_dv = dict(self.costs)
        for neighbor, neighbor_seq_dv in self.dvs.items():
            seq, neighbor_dv = neighbor_seq_dv
            for dest_id, (latency, path) in neighbor_dv.items():
                dest_id = int(dest_id)
                assert dest_id == path[-1], 'the last node in path is the destination'
                if self.id in path:
                    continue

                dist = self.costs[neighbor][0] + latency
                if dest_id not in new_dv or dist < new_dv[dest_id][0]:
                    new_dv[dest_id] = [dist, [self.id] + path]

        if new_dv != self.dv:
            self.dv = new_dv
            self.seq += 1
            self.send_to_neighbors(json.dumps({'id': self.id, 'seq': self.seq, 'dv': self.dv}))
