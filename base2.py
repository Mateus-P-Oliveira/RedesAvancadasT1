import heapq
import sys
from collections import defaultdict, deque

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
                    interfaces = [(parts[i], int(parts[i+1])) for i in range(2, 2+numifs*2, 2)]
                    routers[rid] = interfaces
                elif current_section == 'mgroup':
                    parts = line.split(',')
                    mid = parts[0]
                    subnets_list = parts[1:]
                    multicast_groups[mid] = subnets_list
    
    return subnets, routers, multicast_groups

# Função para criar a tabela de roteamento unicast usando o algoritmo de Dijkstra
def dijkstra(routers):
    unicast_routes = defaultdict(dict)
    
    for rid, interfaces in routers.items():
        distances = {}
        previous_nodes = {}
        priority_queue = []
        
        distances[rid] = 0
        previous_nodes[rid] = None
        heapq.heappush(priority_queue, (0, rid))
        
        while priority_queue:
            current_distance, current_node = heapq.heappop(priority_queue)
            
            if current_distance > distances.get(current_node, float('inf')):
                continue
            
            for iface, weight in routers[current_node]:
                neighbor = iface.split('/')[0]
                new_distance = current_distance + weight
                
                if new_distance < distances.get(neighbor, float('inf')):
                    distances[neighbor] = new_distance
                    previous_nodes[neighbor] = current_node
                    heapq.heappush(priority_queue, (new_distance, neighbor))
        
        for node in distances:
            next_hop = previous_nodes.get(node, '0.0.0.0')
            if next_hop != '0.0.0.0':
                # Note: We need to track interface numbers properly in a real implementation
                ifnum = [i for i, (ip, _) in enumerate(routers[rid]) if ip.split('/')[0] == next_hop][0]
                unicast_routes[rid][node] = (next_hop, ifnum)
            else:
                unicast_routes[rid][node] = (next_hop, 0)
    
    return unicast_routes

# Função para criar a tabela de roteamento multicast
def create_multicast_routes(subnets, routers, multicast_groups):
    multicast_routes = defaultdict(dict)
    
    for mid, subnets_list in multicast_groups.items():
        for subnet in subnets_list:
            if subnet in routers:
                for rid, interfaces in routers.items():
                    # Simula o cálculo da árvore de roteamento multicast usando o algoritmo de Dijkstra
                    distances = {}
                    previous_nodes = {}
                    priority_queue = []
                    
                    distances[rid] = 0
                    previous_nodes[rid] = None
                    heapq.heappush(priority_queue, (0, rid))
                    
                    while priority_queue:
                        current_distance, current_node = heapq.heappop(priority_queue)
                        
                        if current_distance > distances.get(current_node, float('inf')):
                            continue
                        
                        for iface, weight in routers[current_node]:
                            neighbor = iface.split('/')[0]
                            new_distance = current_distance + weight
                            
                            if new_distance < distances.get(neighbor, float('inf')):
                                distances[neighbor] = new_distance
                                previous_nodes[neighbor] = current_node
                                heapq.heappush(priority_queue, (new_distance, neighbor))
                    
                    if subnet in distances:
                        next_hop = previous_nodes.get(subnet, '0.0.0.0')
                        if next_hop != '0.0.0.0':
                            ifnum = [i for i, (ip, _) in enumerate(routers[rid]) if ip.split('/')[0] == next_hop][0]
                            multicast_routes[rid][mid] = [(next_hop, ifnum)]
                        else:
                            multicast_routes[rid][mid] = [('0.0.0.0', 0)]
    
    return multicast_routes

# Função para simular o ping multicast
def simulate_multicast_ping(subnet_id, group_id, subnets, multicast_groups):
    print("#TRACE")
    if subnet_id in subnets and group_id in multicast_groups:
        visited = set()
        queue = deque([subnet_id])
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            if current in multicast_groups[group_id]:
                print(f"{current} => r1 : mping {group_id};")
                for neighbor in multicast_groups[group_id]:
                    if neighbor != current:
                        print(f"r1 => {neighbor} : mping {group_id};")
                    queue.append(neighbor)
                
        if subnet_id not in multicast_groups[group_id]:
            print(f"{subnet_id} => r1 : mping {group_id};")
    
# Função principal para executar o simulador
def main(filename, subnet_id, group_id):
    subnets, routers, multicast_groups = read_topology_file(filename)
    
    # Criação das tabelas de roteamento unicast
    unicast_routes = dijkstra(routers)
    print("#UROUTETABLE")
    for rid, routes in unicast_routes.items():
        for net, (nexthop, ifnum) in routes.items():
            print(f"{rid},{net},{nexthop},{ifnum}")
    
    # Criação das tabelas de roteamento multicast
    multicast_routes = create_multicast_routes(subnets, routers, multicast_groups)
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
