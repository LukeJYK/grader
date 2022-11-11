from simulator.node import Node


class Generic_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.logging.debug("new node %d" % self.id)

    def __str__(self):
        return "A Generic Node: " + str(self.id) + "\n"

    def link_has_been_updated(self, neighbor, latency):
        # latency = -1 if delete a link
        if latency == -1 and neighbor in self.neighbors:

            self.neighbors.remove(neighbor)
        else:
            self.neighbors.append(neighbor)
            # self.send_to_neighbors("hello")
            self.send_to_neighbor(neighbor, "hello")

        self.logging.debug('link update, neighbor %d, latency %d, time %d' % (neighbor, latency, self.get_time()))

    def process_incoming_routing_message(self, m):
        self.logging.debug("receive a message at Time %d. " % self.get_time() + m)

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        if self.neighbors != []:
            return self.neighbors[0]

            # FALSE-NEGATIVES FIXED for trees: upon ties, a correct answer isn't necessarily a tree -- see test_tie.event:
            # return [4, 0, 1 if destination < 2 else 3, 0, 0][self.id] # in real life, node 2 would actually boast load balance

            # FALSE-POSITIVES FIXED for trees: same set of edges does not necessarily mean a correct answer -- see test_chain.event:
            # return ([1] + [(self.id + 1) if destination == 4 else (self.id - 1)] * 3 + [3])[self.id]

            # VALID JUDGEMENT: simply check for each and every pair of src and dst -- and compare lengths

        return -1
