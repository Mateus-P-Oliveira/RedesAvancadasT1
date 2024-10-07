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
                    interfaces = [(parts[i].split('/')[0], int(parts[i + 1]))
                                  for i in range(2, 2 + numifs * 2, 2)]
                    routers[rid] = interfaces
                elif current_section == 'mgroup':
                    parts = line.split(',')
                    mid = parts[0]
                    subnets_list = parts[1:]
                    multicast_groups[mid] = subnets_list

    return subnets, routers, multicast_groups

# Função para criar a tabela de roteamento unicast usando o algoritmo de Dijkstra


def dijkstra(routers, subnets):
    unicast_routes = defaultdict(dict)

    for rid, interfaces in routers.items():
        print(f"Starting Dijkstra for router: {rid}")
        distances = {rid: 0}  # Inicializa a distância do próprio roteador
        previous_nodes = {rid: None}  # Armazena o nó anterior
        nodes = set(routers.keys())  # Conjunto de nós para visitar

        while nodes:
            current_node = min(nodes, key=lambda node: distances.get(node, float('inf')))
            nodes.remove(current_node)

            print(f"Current Node: {current_node}, Distances: {distances}")

            # Iterando sobre as interfaces do roteador
            for iface, weight in interfaces:
                neighbor_ip = iface.split('/')[0]  # Pega o IP da interface
                print(neighbor_ip)
                print(f"Interface: {iface}, Neighbor IP: {neighbor_ip}, Weight: {weight}")

                if neighbor_ip not in distances:  # Adiciona vizinho à lista de distâncias
                    
                    distances[neighbor_ip] = float('inf')
                new_distance = distances[current_node] + weight

                # Atualiza a distância se for menor
                if new_distance < distances[neighbor_ip]:
                    distances[neighbor_ip] = new_distance
                    previous_nodes[neighbor_ip] = current_node

            print(f"Updated Distances: {distances}")

        # Registrar rotas unicast
        # Registrar rotas unicast
       # Registrar rotas unicast
        # Registrar rotas unicast
        for node in distances:
            print(f"Node: {node}")  # Log para depuração
            print("~~~~~~~~")
            print(f"Distances: {distances}")  # Log para depuração
            print("________________")

            if node != rid:  # Ignora o próprio roteador
                print(f"Checking node: {node}")  # Log para depuração
                next_hop = previous_nodes[node]
                
                if next_hop is not None:
                    # Verifica se o node é um IP correspondente a uma sub-rede
                    subnet = next((sub for sub in subnets if node.startswith(subnets[sub].split('/')[0])), None)
                    print(f"Found subnet: {subnet}")  # Log para depuração
                    
                    if subnet is not None:
                        ifnum = next((i for i, (iface, _) in enumerate(routers[rid]) if iface.split('/')[0] == next_hop), None)
                        if ifnum is not None:
                            unicast_routes[rid][subnet] = (next_hop, ifnum)
                            print(f"Added route: {rid} -> {subnet} via {next_hop} on interface {ifnum}")

        print(f"Unicast routes for {rid}: {unicast_routes[rid]}")  # Log da tabela de rotas




    return unicast_routes






# Função para criar a tabela de roteamento multicast


def create_multicast_routes(subnets, routers, multicast_groups, unicast_routes):
    multicast_routes = defaultdict(dict)

    for mid, subnets_list in multicast_groups.items():
        for subnet_id in subnets_list:
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
        # Assume que o roteador é r1
        print(f"{subnet_id} => r1 : mping {group_id};")
        for target in multicast_groups[group_id]:
            print(f"r1 => {target} : mping {group_id};")


# Função principal para executar o simulador
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
    multicast_routes = create_multicast_routes(
        subnets, routers, multicast_groups, unicast_routes)
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
