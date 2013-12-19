
class ServiceDefinitionValidator(object):

    """ Class that inspects service components to ensure their validity.
    """

    def __init__(self, servicedefs):
        """ Construct a ServiceDefinitionValidator from a dictionary where
            the keys are service URIs and the values are service objects.
        """
        service_edges = {}
        only_service_uris = lambda needed_component_uri: 'service' in needed_component_uri
        for service_uri, servicedef in servicedefs.iteritems():
            outgoing_edges = filter(
                only_service_uris, servicedef.needs)
            service_edges[service_uri] = outgoing_edges

        self.edges = service_edges

    def assert_no_cycles_present(self):
        """ Will raise an exception if the service definitions contain cycles
        """
        cycles = []
        strongly_connected_components = tarjan_scc(self.edges)
        for component in strongly_connected_components:
            if len(component) > 1:
                cycles.append("\t\t%s" % Cycle(component))

        if len(cycles) > 0:
            error_message = """Found cycle(s) in service definition : \n%s""" % "\n".join(
                cycles)
            raise EnvironmentError(error_message)


class Cycle(object):

    def __init__(self, nodes_involved):
        self.nodes_involved = nodes_involved

    def __str__(self):
        return "Cycle of %s" % (self.nodes_involved,)


def tarjan_scc(graph):
    """ Tarjan's partitioning algorithm for finding strongly
        connected components in a graph.
    """

    index_counter = [0]
    stack = []
    low_links = {}
    index = {}
    result = []

    def strong_connect(node):
        index[node] = index_counter[0]
        low_links[node] = index_counter[0]
        index_counter[0] += 1
        stack.append(node)

        try:
            successors = graph[node]
        except:
            successors = []
        for successor in successors:
            if successor not in low_links:
                strong_connect(successor)
                low_links[node] = min(low_links[node], low_links[successor])
            elif successor in stack:
                low_links[node] = min(low_links[node], index[successor])

        if low_links[node] == index[node]:
            connected_component = []

            while True:
                successor = stack.pop()
                connected_component.append(successor)
                if successor == node:
                    break
            component = tuple(connected_component)
            result.append(component)

    for node in graph:
        if node not in low_links:
            strong_connect(node)

    return result
