import argparse
import ipaddress
import random
from pyvis.network import Network
import dns.resolver

# Function to perform reverse DNS lookup using a specific DNS server
def reverse_dns_lookup(ip, dns_server):
    try:
        resolver = dns.resolver.Resolver(configure=False)
        resolver.nameservers = [dns_server]
        qname = dns.reversename.from_address(ip)
        answers = resolver.resolve(qname, "PTR")
        hostname = str(answers[0])
        print(f"Reverse DNS lookup on {ip} using DNS server {dns_server} returned hostname: {hostname}")
        return hostname
    except (dns.resolver.NXDOMAIN, dns.resolver.Timeout, dns.resolver.NoNameservers):
        return None

# Parse command-line arguments for CIDR start and end ranges and DNS server
parser = argparse.ArgumentParser(description="Generate a network map with subnet nodes based on reverse DNS - SECIANUS 2023 - Frank Nusko.")
parser.add_argument("start_cidr", help="Specify the start CIDR range")
parser.add_argument("end_cidr", help="Specify the end CIDR range")
parser.add_argument("dns_server", help="Specify the DNS server for reverse DNS lookup")
args = parser.parse_args()

# Parse the provided CIDR ranges
try:
    start_cidr = ipaddress.IPv4Network(args.start_cidr, strict=False)
    end_cidr = ipaddress.IPv4Network(args.end_cidr, strict=False)
except ipaddress.AddressValueError:
    print("Invalid CIDR range format.")
    exit(1)

# Create a pyvis network
network = Network(height="750px", notebook=True, filter_menu=True, select_menu=True)

# Create the DNS server node
dns_server_node = f"DNS Server ({args.dns_server})"
network.add_node(dns_server_node, label=dns_server_node, shape="ellipse", color="green")

# Iterate through the specified CIDR range and perform reverse DNS lookup
for cidr in ipaddress.summarize_address_range(start_cidr.network_address, end_cidr.network_address):
    subnet_has_valid_hostname = False  # Flag to track if the subnet has systems with valid hostnames
    subnet_str = str(cidr)
    subnet_name = f"Subnet_{subnet_str.split('/')[0].replace('.', '_')}"
    
    # Create a list to store valid nodes
    valid_nodes = []

    for ip in cidr:
        ip_str = str(ip)
        hostname = reverse_dns_lookup(ip_str, args.dns_server)
        if hostname:
            full_label = f"{hostname}\n{ip_str}"  # Combine hostname and IP address
            valid_nodes.append((full_label, ip_str))
            subnet_has_valid_hostname = True

    if subnet_has_valid_hostname:
        network.add_node(subnet_name, label=subnet_name, shape="square", color=f"#{random.randint(0, 0xFFFFFF):06X}")  # Add subnet as a node
        network.add_edge(dns_server_node, subnet_name, color="blue")  # Connect DNS server node to subnet nodes
        for (full_label, ip_str) in valid_nodes:
            network.add_node(full_label, label=full_label, shape="box", color="lightblue")  # Add systems as nodes
            network.add_edge(subnet_name, full_label, color="gray")  # Connect subnet node to system nodes

# Uncomment to change the physics and generate code for set_options
#network.show_buttons(filter_=['physics'])

# Visualize the network
options = """
const options = {
  "physics": {
    "forceAtlas2Based": {
      "springLength": 100,
      "damping": 0.09
    },
    "minVelocity": 0.75,
    "solver": "forceAtlas2Based"
  }
}
"""
network.set_options(options)
network.show("subnet_network.html")
