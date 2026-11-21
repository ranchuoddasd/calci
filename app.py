import ipaddress
import json
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

def analyze_subnet_allocation(big_block_str, allocated_subnets_str):
    """Analyze allocated and free IPv4 ranges within a parent CIDR block."""
    parent = ipaddress.ip_network(big_block_str, strict=False)
    if not isinstance(parent, ipaddress.IPv4Network):
        raise ValueError("Only IPv4 networks are supported.")
    if not isinstance(allocated_subnets_str, list):
        raise ValueError("allocated_subnets must be a list of CIDR strings.")

    networks = []
    for value in allocated_subnets_str:
        network = ipaddress.ip_network(value, strict=False)
        if not isinstance(network, ipaddress.IPv4Network):
            raise ValueError(f"IPv6 subnet is not supported: {value}")
        if not network.subnet_of(parent):
            raise ValueError(f"Allocated subnet {network} is outside parent block {parent}")
        networks.append(network)

    merged = list(ipaddress.collapse_addresses(sorted(networks, key=lambda n: int(n.network_address))))
    allocated_count = sum(n.num_addresses for n in merged)
    total_count = parent.num_addresses
    free_blocks = []
    cursor = int(parent.network_address)
    parent_end = int(parent.broadcast_address)
    for network in merged:
        start, end = int(network.network_address), int(network.broadcast_address)
        if cursor < start:
            free_blocks.extend(ipaddress.summarize_address_range(ipaddress.IPv4Address(cursor), ipaddress.IPv4Address(start - 1)))
        cursor = max(cursor, end + 1)
    if cursor <= parent_end:
        free_blocks.extend(ipaddress.summarize_address_range(ipaddress.IPv4Address(cursor), ipaddress.IPv4Address(parent_end)))

    return {
        "total_ips_in_big_block": total_count,
        "total_allocated_ips": allocated_count,
        "total_free_ips": total_count - allocated_count,
        "allocated_subnets": merged,
        "free_blocks": list(free_blocks),
    }

def format_results(parent, results):
    return {
        "big_block": str(parent),
        "total_ips_in_big_block": results["total_ips_in_big_block"],
        "total_allocated_ips": results["total_allocated_ips"],
        "total_free_ips": results["total_free_ips"],
        "allocated_subnets": [{"subnet": str(n), "ip_count": n.num_addresses} for n in results["allocated_subnets"]],
        "free_blocks": [{"subnet": str(n), "ip_count": n.num_addresses} for n in results["free_blocks"],
    }

@app.get("/")
def index():
    return send_from_directory(".", "index.html")

@app.post("/api/analyze")
def analyze_uploads():
    if "big_block_file" not in request.files or "allocated_subnets_file" not in request.files:
        return jsonify({"error": "Both JSON files are required."}), 400
    try:
        big_data = json.load(request.files["big_block_file"])
        allocated_data = json.load(request.files["allocated_subnets_file"])
        parent = big_data.get("big_block") if isinstance(big_data, dict) else big_data
        allocated = allocated_data.get("allocated_subnets") if isinstance(allocated_data, dict) else allocated_data
        if not isinstance(parent, str) or not parent.strip():
            return jsonify({"error": "big_block must be a non-empty CIDR string."}), 400
        if not isinstance(allocated, list):
            return jsonify({"error": "allocated_subnets must be a list."}), 400
        return jsonify(format_results(parent, analyze_subnet_allocation(parent, allocated)))
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"Unexpected analysis error: {exc}"}), 500

@app.post("/api/analyze-json")
def analyze_json():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "A JSON object is required."}), 400
    parent, allocated = data.get("big_block"), data.get("allocated_subnets")
    if not isinstance(parent, str) or not parent.strip():
        return jsonify({"error": "big_block is required and must be a CIDR string."}), 400
    if not isinstance(allocated, list):
        return jsonify({"error": "allocated_subnets is required and must be a list."}), 400
    try:
        return jsonify(format_results(parent, analyze_subnet_allocation(parent, allocated)))
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=False)
