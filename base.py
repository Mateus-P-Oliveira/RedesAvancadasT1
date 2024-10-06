import heapq
import sys
from collections import defaultdict

# Função para ler o arquivo de descrição de topologia
def read_topology_file(filename):
    subnets = {}
    routers = {}
    multicast_groups = {}

    with open(filename, 'r') as file:
        lines = file.readlines()

        current_section = None
        for line in lines:
            line = line.strip()
            if line.startswith("#SUBNET"):
                current_section = 'subnet'
            elif line.startswith("#ROUTER"):
                current_section = 'router'
            elif line.startswith("#MGROUP"):
                current_section = 'mgroup'
            elif line and not line.startswith("#"):
                if current_section == 'subnet':
                    sid, netinfo = line.split(',', 1)
                    subnets[sid] = netinfo
                elif current_section == 'router':
                    parts = line.split(',')
                    rid = parts[0]
                    numifs = int(parts[1])
                    interfaces = [(parts[i].split('/')[0], int(parts[i + 1])) for i in range(2, 2 + numifs * 2, 2)]
                    routers[rid] = interfaces
                elif current_section == 'mgroup':
                    parts = line.split(',')
                    mid = parts[0]
                    subnets_list = parts[1:]
                    multicast_groups[mid] = subnets_list

    print("Subnets:", subnets)  # Verifica as sub-redes
    print("Routers:", routers)  # Verifica a estrutura dos roteadores
    print("Multicast Groups:", multicast_groups)  # Verifica os grupos multicast

    return subnets, routers, multicast_groups


# Função para criar a tabela de roteamento unicast usando o algoritmo de Dijkstra
def dijkstra(routers, subnets):
    unicast_routes = defaultdict(dict)
    graph = defaultdict(list)

    # Criar o grafo a partir dos routers e suas interfaces
    for rid, interfaces in routers.items():
        for iface, weight in interfaces:
            graph[rid].append((iface.split('/')[0], weight))  # Pega apenas o IP

    for rid in routers.keys():
        distances = {rid: 0}
        previous_nodes = {rid: None}
        priority_queue = [(0, rid)]

        while priority_queue:
            current_distance, current_router = heapq.heappop(priority_queue)

            if current_distance > distances.get(current_router, float('inf')):
                continue

            for neighbor, weight in graph[current_router]:
                if neighbor not in distances:
                    distances[neighbor] = float('inf')

                new_distance = current_distance + weight

                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    previous_nodes[neighbor] = current_router
                    heapq.heappush(priority_queue, (new_distance, neighbor))

        # Montar as rotas unicast
        for node in distances:
            if node in previous_nodes and previous_nodes[node] is not None:
                next_hop = previous_nodes[node]

                # Encontrar a sub-rede correspondente
                subnet = next((sub for sub in subnets.keys() if subnets[sub].startswith(node)), None)

                if subnet is not None:
                    # Encontrar o índice da interface correspondente ao next_hop
                    ifnum = None
                    for i, (iface, _) in enumerate(routers[rid]):
                        if iface.split('/')[0] == next_hop:
                            ifnum = i
                            break  # Saia do loop assim que encontrar

                    if ifnum is not None:
                        unicast_routes[rid][subnet] = (next_hop, ifnum)

    return unicast_routes




# Função para criar a tabela de roteamento multicast
def create_multicast_routes(subnets, routers, multicast_groups, unicast_routes):
    multicast_routes = defaultdict(dict)

    for mid, subnets_list in multicast_groups.items():
        for subnet_id in subnets_list:
            # Aqui, vamos procurar os roteadores que têm rotas para as sub-redes de interesse
            for rid, routes in unicast_routes.items():
                if subnet_id in routes:
                    nexthop, ifnum = routes[subnet_id]
                    if mid not in multicast_routes[rid]:
                        multicast_routes[rid][mid] = []
                    multicast_routes[rid][mid].append((nexthop, ifnum))

    return multicast_routes



# Função para simular o ping multicast
def simulate_multicast_ping(subnet_id, group_id, subnets, multicast_groups):
    print("#TRACE")
    if subnet_id in subnets and group_id in multicast_groups:
        print(f"{subnet_id} => r1 : mping {group_id};")
        for target in multicast_groups[group_id]:
            print(f"r1 => {target} : mping {group_id};")


# Função principal para executar o simulador
def main(filename, subnet_id, group_id):
    subnets, routers, multicast_groups = read_topology_file(filename)

    # Criação das tabelas de roteamento unicast
    unicast_routes = dijkstra(routers, subnets)
    print("#UROUTETABLE")
    for rid, routes in unicast_routes.items():
        for net, (nexthop, ifnum) in routes.items():
            print(f"{rid},{net},{nexthop},{ifnum}")

    # Criação das tabelas de roteamento multicast
    multicast_routes = create_multicast_routes(subnets, routers, multicast_groups, unicast_routes)
    print("#MROUTETABLE")
    for rid, routes in multicast_routes.items():
        for mid, nexthops in routes.items():
            nexthop_list = ','.join(f"{nh},{ifnum}" for nh, ifnum in nexthops)
            print(f"{rid},{mid},{nexthop_list}")

    # Simulação do ping multicast
    simulate_multicast_ping(subnet_id, group_id, subnets, multicast_groups)



if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python simulator.py <topology_file> <subnet_id> <group_id>")
        sys.exit(1)
    
    topology_file = sys.argv[1]
    subnet_id = sys.argv[2]
    group_id = sys.argv[3]
    
    main(topology_file, subnet_id, group_id)
