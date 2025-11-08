import hashlib
from dataclasses import dataclass
import logging

# Configure basic logging for visibility into server assignments
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s][%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# frozen=True makes the class immutable and hashable, required for using Node objects in a Python set.
@dataclass(frozen=True)
class Node:
    name: str
    ip: str


# --- 1. NORMAL HASHING (MODULO HASHING) ---
# Used as a baseline to demonstrate the high re-mapping cost when nodes change.
class NormalHashing:
    def __init__(self, nodes: list[Node]):
        self.nodes = nodes

    def get_node(self, key: str) -> int:
        # Standard modulo hashing: Hash the key and take modulo N (number of nodes).
        # H(key) % N
        hash_value = hashlib.sha256(key.encode("utf-8")).hexdigest()
        server_index = int(hash_value, 16) % len(self.nodes)
        logging.info(f"{key} falls into server {server_index}")
        return server_index

    def add_node(self, node: Node) -> None:
        # Appending changes N, causing massive re-mapping of all keys.
        self.nodes.append(node)


# --- 2. CONSISTENT HASHING ---
# Minimizes key re-mapping when nodes are added or removed.
class ConsistentHashing:
    def __init__(self, nodes: list[Node], virtual_nodes=3):
        # virtual_nodes: The replication factor for each physical node on the hash ring.
        self.virtual_nodes = virtual_nodes
        # self.nodes: Tracks the set of real, physical Node objects.
        self.nodes = set()
        # self.hash_ring: The core data structure - a sorted list of (hash_value, Node) tuples.
        self.hash_ring: list[tuple[int, Node]] = []
        for node in nodes:
            self.add_node(node)

    def _hash(self, key: str) -> int:
        # Uses SHA-256 for a uniform, large 2^256 hash space.
        return int(hashlib.sha256(key.encode("utf-8")).hexdigest(), 16)

    # Helper function: Binary search for the 'lower bound'.
    # Finds the index of the first hash value in the ring that is >= target.
    def _lower_bound(self, target: int) -> int:
        left = 0
        right = len(self.hash_ring) - 1
        # Loop continues until left > right. Upon termination, 'left' is the index of the smallest element >= target.
        while left <= right:
            mid = (left + right) // 2
            if self.hash_ring[mid][0] >= target:
                right = (
                    mid - 1
                )  # Potential match found (mid >= target), search left for the true lower bound.
            else:
                left = mid + 1  # Target is larger, move search window to the right.
        return left

    def add_node(self, node: Node) -> None:
        self.nodes.add(node)
        # Create 'virtual_nodes' to improve key distribution and load balancing.
        for i in range(self.virtual_nodes):
            # Create a unique hash key for each virtual node representation.
            hash_value = self._hash(f"{node.name}:{i}")
            # Find the correct sorted position using binary search (O(log N)).
            idx = self._lower_bound(hash_value)
            # O(N) operation due to list shifting. This is the bottleneck for large rings.
            self.hash_ring.insert(idx, (hash_value, node))

    def remove_node(self, node: Node) -> None:
        if node not in self.nodes:
            return
        self.nodes.remove(node)
        # Rebuild the hash ring by filtering out all entries associated with the removed node.
        # Filtering is O(N*V) where N*V is the ring size. Requires a full rebuild.
        self.hash_ring = [(h, n) for (h, n) in self.hash_ring if n != node]

    def get_node(self, key: str) -> Node | None:
        if not self.hash_ring:
            return None

        # 1. Hash the key to find its position on the ring.
        hash_value = self._hash(key)

        # 2. Find the index of the first node hash >= key hash.
        # This implements the "walk clockwise" rule of consistent hashing.
        idx = self._lower_bound(hash_value)

        # 3. Handle wrap-around: If idx is out of bounds (key hash > all node hashes),
        # the key wraps back to the first node (index 0).
        node_idx = 0 if idx >= len(self.hash_ring) else idx

        return self.hash_ring[node_idx][1]


def main():
    nodes: list[Node] = [
        Node(name="A", ip="192.168.0.1"),
        Node(name="B", ip="192.168.0.2"),
        Node(name="C", ip="192.168.0.3"),
    ]
    keys = ["user_1", "user_2", "user_3", "user_4", "user_5", "user_6", "user_7"]

    # --- 1. Normal Hashing Demonstration ---
    print("\n" + "=" * 10 + " Normal Hashing " + "=" * 10)
    normalHashing = NormalHashing(nodes.copy())  # Use a copy for clean start

    # Store initial mappings (N=3)
    normal_initial_mappings = {
        # Using get_node and accessing nodes[index]
        key: nodes[normalHashing.get_node(key)].name
        for key in keys
    }
    print(f"Initial Mappings: {normal_initial_mappings}")

    # Add a server
    new_server = Node(name="D", ip="192.168.0.4")
    normalHashing.add_node(new_server)  # Using add_node
    logging.info(
        f"--- ADDED SERVER D (Total: {len(normalHashing.nodes)}) ---"
    )  # Using .nodes

    # Check new mappings (N=4) - Expect many re-mappings
    normal_final_mappings = {
        # Using .nodes and get_node
        key: normalHashing.nodes[normalHashing.get_node(key)].name
        for key in keys
    }
    print(f"Final Mappings: {normal_final_mappings}")

    # Calculate re-mappings
    normal_remap_count = sum(
        1 for key in keys if normal_initial_mappings[key] != normal_final_mappings[key]
    )
    print(f"Normal Hashing Re-mapped Keys: {normal_remap_count} / {len(keys)}")

    # --- 2. Consistent Hashing Demonstration ---
    print("\n" + "=" * 10 + " Consistent Hashing " + "=" * 10)
    # virtual_nodes=100 ensures much better load distribution.
    consistentHashing = ConsistentHashing(nodes.copy(), virtual_nodes=100)

    # Store initial mappings (N=3)
    # getattr is used for a safe access, preventing Pylance/runtime errors if get_node returns None.
    consistent_initial_mappings = {
        key: getattr(consistentHashing.get_node(key), "name", "NO_SERVER")
        for key in keys
    }
    print(f"Initial Mappings: {consistent_initial_mappings}")

    # Add a node
    consistentHashing.add_node(new_server)
    logging.info(f"--- ADDED NODE D ---")

    # Check new mappings (N=4) - Expect few re-mappings
    consistent_final_mappings = {
        key: getattr(consistentHashing.get_node(key), "name", "NO_SERVER")
        for key in keys
    }
    print(f"Final Mappings: {consistent_final_mappings}")

    # Calculate re-mappings
    # Expect this number to be much lower than the Normal Hashing count.
    consistent_remap_count = sum(
        1
        for key in keys
        if consistent_initial_mappings[key] != consistent_final_mappings[key]
    )
    print(f"Consistent Hashing Re-mapped Keys: {consistent_remap_count} / {len(keys)}")


if __name__ == "__main__":
    main()


# --- EXPECTED OUTPUT DEMONSTRATING HASHING EFFICIENCY ---
# The re-mapped key counts below show Consistent Hashing requires far less data migration (1/7 keys)
# than Normal Hashing (4/7 keys) when a server is added.
# ========== Normal Hashing ==========
# [2025-11-09 01:57:33][INFO] user_1 falls into server 0
# [2025-11-09 01:57:33][INFO] user_2 falls into server 2
# [2025-11-09 01:57:33][INFO] user_3 falls into server 0
# [2025-11-09 01:57:33][INFO] user_4 falls into server 1
# [2025-11-09 01:57:33][INFO] user_5 falls into server 1
# [2025-11-09 01:57:33][INFO] user_6 falls into server 2
# [2025-11-09 01:57:33][INFO] user_7 falls into server 1
# Initial Mappings: {'user_1': 'A', 'user_2': 'C', 'user_3': 'A', 'user_4': 'B', 'user_5': 'B', 'user_6': 'C', 'user_7': 'B'}
# [2025-11-09 01:57:33][INFO] --- ADDED SERVER D (Total: 4) ---
# [2025-11-09 01:57:33][INFO] user_1 falls into server 3
# [2025-11-09 01:57:33][INFO] user_2 falls into server 1
# [2025-11-09 01:57:33][INFO] user_3 falls into server 0
# [2025-11-09 01:57:33][INFO] user_4 falls into server 1
# [2025-11-09 01:57:33][INFO] user_5 falls into server 1
# [2025-11-09 01:57:33][INFO] user_6 falls into server 0
# [2025-11-09 01:57:33][INFO] user_7 falls into server 2
# Final Mappings: {'user_1': 'D', 'user_2': 'B', 'user_3': 'A', 'user_4': 'B', 'user_5': 'B', 'user_6': 'A', 'user_7': 'C'}
# Normal Hashing Re-mapped Keys: 4 / 7

# ========== Consistent Hashing ==========
# Initial Mappings: {'user_1': 'B', 'user_2': 'A', 'user_3': 'B', 'user_4': 'B', 'user_5': 'C', 'user_6': 'C', 'user_7': 'B'}
# [2025-11-09 01:57:33][INFO] --- ADDED NODE D ---
# Final Mappings: {'user_1': 'B', 'user_2': 'A', 'user_3': 'B', 'user_4': 'B', 'user_5': 'C', 'user_6': 'C', 'user_7': 'D'}
# Consistent Hashing Re-mapped Keys: 1 / 7
