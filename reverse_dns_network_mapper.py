import socket
import networkx as nx
import matplotlib.pyplot as plt
import argparse
import ipaddress
import random

# Function to perform reverse DNS lookup and print the subnet
def reverse_dns_lookup(ip, subnet_name):
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        print(f"Reverse DNS lookup on {ip} returned hostname: {hostname}")
        return hostname
    except socket.herror:
        return None

# Parse command-line arguments for CIDR start and end ranges
parser = argparse.ArgumentParser(description="Generate a network map with subnet nodes based on reverse dns - SECIANUS 2023 - Frank Nusko.")
parser.add_argument("start_cidr", help="Specify the start CIDR range")
parser.add_argument("end_cidr", help="Specify the end CIDR range")
args = parser.parse_args()

# Parse the provided CIDR ranges
try:
    start_cidr = ipaddress.IPv4Network(args.start_cidr, strict=False)
    end_cidr = ipaddress.IPv4Network(args.end_cidr, strict=False)
except ipaddress.AddressValueError:
    print("Invalid CIDR range format.")
    exit(1)

# Iterate through the specified CIDR range and perform reverse DNS lookup
for cidr in ipaddress.summarize_address_range(start_cidr.network_address, end_cidr.network_address):
    subnet_has_valid_hostname = False  # Flag to track if the subnet has systems with valid hostnames
    subnet_str = str(cidr)
    subnet_name = f"Subnet_{subnet_str.split('/')[0].replace('.', '_')}"
    
    # Create a directed graph using NetworkX
    G = nx.DiGraph()
    subnet_colors = {}
    
    G.add_node(subnet_name, type="subnet")  # Add subnet as a node
    subnet_colors[subnet_name] = f"#{random.randint(0, 0xFFFFFF):06X}"  # Assign a random color to the subnet
    
    for ip in cidr:
        ip_str = str(ip)
        hostname = reverse_dns_lookup(ip_str, subnet_name)
        if hostname:
            full_label = f"{hostname}\n{ip_str}"  # Combine hostname and IP address
            G.add_node(full_label, label=full_label, type="system", subnet=subnet_name)  # Add systems as nodes with labels and subnet attribute
            G.add_edge(subnet_name, full_label)  # Connect subnet node to system nodes
            subnet_has_valid_hostname = True

    # Remove subnet node if there are no systems with valid hostnames
    if not subnet_has_valid_hostname:
        G.remove_node(subnet_name)
    else:
        # Create a graphical map with nodes representing subnets and systems with valid reverse DNS and IP addresses
        plt.figure(figsize=(10, 8))
        
        # Use a force-directed layout to automatically position nodes without overlap
        pos = nx.spring_layout(G, seed=42, iterations=100, scale=2.5)
        
        labels = nx.get_node_attributes(G, "label")  # Retrieve node labels
        
        # Draw subnet nodes with different colors
        subnet_nodes = [node for node in G.nodes if G.nodes[node]["type"] == "subnet"]
        nx.draw_networkx_nodes(G, pos, nodelist=subnet_nodes, node_size=3000, node_color=[subnet_colors[node] for node in subnet_nodes])
        nx.draw_networkx_labels(G, pos, labels={node: node for node in subnet_nodes}, font_size=8, font_color="black")
        
        # Draw system nodes with the same color as their subnet
        system_nodes = [node for node in G.nodes if G.nodes[node]["type"] == "system"]
        node_colors = [subnet_colors[G.nodes[node]['subnet']] for node in system_nodes]  # Assign color based on subnet
        nx.draw_networkx_nodes(G, pos, nodelist=system_nodes, node_size=3000, node_color=node_colors)
        nx.draw_networkx_labels(G, pos, labels=labels, font_size=8, font_color="black")
        
        nx.draw_networkx_edges(G, pos, edgelist=list(G.edges), arrows=True, connectionstyle="arc3,rad=0.2")
        plt.title(f"Network Topology for {subnet_name} (Valid Reverse DNS)")
        plt.axis('off')
        
        # Save the figure as a PNG file after processing the current subnet
        plt.savefig(f"{subnet_name}.png")
