import sys
import heapq
from collections import defaultdict

class Router:
    def __init__(self, rid):
        self.rid = rid
        self.interfaces = []
        self.unicast_routes = {}
        self.multicast_routes = defaultdict(list)

    def add_interface(self, netaddr, weight):
        self.interfaces.append((netaddr, weight))

class Subnet:
    def __init__(self, sid, netaddr):
        self.sid = sid
        self.netaddr = netaddr

class MulticastGroup:
    def __init__(self, mid, subnets):
        self.mid = mid
        self.subnets = subnets

def dijkstra(routers, start_router):
    unicast_routes = {}
    priority_queue = [(0, start_router)]
    visited = set()

    while priority_queue:
        current_weight, current_router = heapq.heappop(priority_queue)

        if current_router in visited:
            continue

        visited.add(current_router)
        unicast_routes[current_router] = current_weight

        for interface, weight in routers[current_router].interfaces:
            next_router = interface[0]  # Assumindo que a interface contém o endereço do próximo roteador
            if next_router not in visited:
                heapq.heappush(priority_queue, (current_weight + weight, next_router))

    return unicast_routes

def build_unicast_tables(routers):
    for router in routers:
        routers[router].unicast_routes = dijkstra(routers, router)

def build_multicast_tables(routers, multicast_groups):
    for mg in multicast_groups:
        mid = mg.mid
        for subnet in mg.subnets:
            for router in routers:
                # Lógica para construir a tabela de roteamento multicast
                # Utiliza-se a tabela unicast como referência
                pass  # Completar com lógica de construção

def ping(source_subnet, multicast_group, routers):
    trace = []
    for router in routers:
        if multicast_group in routers[router].multicast_routes:
            for nexthop, ifnum in routers[router].multicast_routes[multicast_group]:
                trace.append(f"{router} => {nexthop} : mping {multicast_group};")

    return trace

def read_topology(file):
    routers = {}
    subnets = {}
    multicast_groups = []

    with open(file) as f:
        lines = f.readlines()

    for line in lines:
        if line.startswith("#SUBNET"):
            continue
        elif line.startswith("#ROUTER"):
            parts = line.strip().split(',')
            rid = parts[0]
            numifs = int(parts[1])
            router = Router(rid)

            for i in range(numifs):
                ip_mask = parts[2 + i * 2]
                weight = int(parts[2 + i * 2 + 1])
                router.add_interface(ip_mask, weight)

            routers[rid] = router
        elif line.startswith("#MGROUP"):
            parts = line.strip().split(',')
            mid = parts[0]
            group_subnets = parts[1:]
            multicast_groups.append(MulticastGroup(mid, group_subnets))

    return routers, subnets, multicast_groups

def main():
    if len(sys.argv) != 4:
        print("Uso: simulador <topofile> <subnet> <multicast_group>")
        return

    topofile, subnet_id, multicast_group_id = sys.argv[1:]

    routers, subnets, multicast_groups = read_topology(topofile)
    build_unicast_tables(routers)
    build_multicast_tables(routers, multicast_groups)

    # Exibir as tabelas de roteamento unicast
    print("#UROUTETABLE")
    for router in routers:
        for netaddr, nexthop in routers[router].unicast_routes.items():
            print(f"{router},{netaddr},{nexthop},<ifnum>")  # <ifnum> a ser definido

    # Exibir as tabelas de roteamento multicast
    print("#MROUTETABLE")
    for router in routers:
        for mid in multicast_groups:
            if mid.mid in routers[router].multicast_routes:
                nexthops = routers[router].multicast_routes[mid.mid]
                print(f"{router},{mid.mid}," + ",".join([f"{nexthop},{ifnum}" for nexthop, ifnum in nexthops]))

    # Simular o ping
    trace = ping(subnet_id, multicast_group_id, routers)
    print("#TRACE")
    print("\n".join(trace))

if __name__ == "__main__":
    main()
