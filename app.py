# app.py
from web3 import Web3
import sys
from typing import List, Tuple

RPC_URL = "https://mainnet.infura.io/v3/your_api_key"

ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "owner", "type": "address"}], "name": "balanceOf",
     "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals",
     "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol",
     "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "name",
     "outputs": [{"name": "", "type": "string"}], "type": "function"},
]

def network_name(chain_id: int) -> str:
    return {
        1: "Ethereum Mainnet",
        11155111: "Sepolia Testnet",
        10: "Optimism",
        137: "Polygon",
        42161: "Arbitrum One",
    }.get(chain_id, f"Unknown (chain ID {chain_id})")

def to_hex(b: bytes) -> str:
    return "0x" + b.hex()

def pad32(b: bytes) -> bytes:
    return b.rjust(32, b"\x00")

def leaf_hash(address: str, balance_wei: int) -> bytes:
    addr_bytes = bytes.fromhex(address[2:])
    leaf = pad32(addr_bytes) + balance_wei.to_bytes(32, "big")
    return Web3.keccak(leaf)

def keccak_pair(left: bytes, right: bytes) -> bytes:
    return Web3.keccak(left + right)

def build_merkle_tree(leaves: List[bytes]) -> List[List[bytes]]:
    if not leaves:
        raise ValueError("No leaves to build Merkle tree")
    level = [pad32(x) for x in leaves]  # normalize width
    tree = [level]
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level), 2):
            L = level[i]
            R = level[i + 1] if i + 1 < len(level) else level[i]
            nxt.append(keccak_pair(L, R))
        tree.append(nxt)
        level = nxt
    return tree

def merkle_root(tree: List[List[bytes]]) -> bytes:
    return tree[-1][0]

def merkle_proof(tree: List[List[bytes]], index: int) -> List[Tuple[bytes, str]]:
    proof = []
    idx = index
    for level in tree[:-1]:
        sib_idx = idx ^ 1
        if sib_idx >= len(level):
            sibling = level[idx]
        else:
            sibling = level[sib_idx]
        pos = "right" if idx % 2 == 0 else "left"
        proof.append((sibling, pos))
        idx //= 2
    return proof

def verify_proof(leaf: bytes, proof: List[Tuple[bytes, str]], root: bytes) -> bool:
    cur = pad32(leaf)
    for sibling, pos in proof:
        sibling = pad32(sibling)
        if pos == "right":
            cur = keccak_pair(cur, sibling)
        else:
            cur = keccak_pair(sibling, cur)
    return cur == root

def main():
    if len(sys.argv) < 3:
        print("Usage: python app.py <erc20_address> <holder1> [holder2 ...] [--index N]")
        sys.exit(1)

    # Parse args
    args = sys.argv[1:]
    proof_index = 0
    if "--index" in args:
        idx_pos = args.index("--index")
        try:
            proof_index = int(args[idx_pos + 1])
        except Exception:
            print("Invalid --index value")
            sys.exit(1)
        args = args[:idx_pos]  # drop index flag and trailing items

    token_addr = Web3.to_checksum_address(args[0])
    holders_raw = args[1:]
    if not holders_raw:
        print("Provide at least one holder address")
        sys.exit(1)

    holders = [Web3.to_checksum_address(h) for h in holders_raw]
    if proof_index < 0 or proof_index >= len(holders):
        print("proof_index out of range for the number of holder addresses")
        sys.exit(1)

    # Web3 init
    if "your_api_key" in RPC_URL:
    print("⚠️ RPC_URL still has placeholder API key; set a real endpoint.")
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print("❌ RPC connection failed. Check RPC_URL or provider availability.")
        sys.exit(1)
    print("🌐 Network:", network_name(w3.eth.chain_id))

    # Token contract
    token = w3.eth.contract(address=token_addr, abi=ERC20_ABI)
    try:
        symbol = token.functions.symbol().call()
    except Exception:
        symbol = "UNKNOWN"
    try:
        decimals = token.functions.decimals().call()
    except Exception:
        decimals = 18
    try:
        name = token.functions.name().call()
    except Exception:
        name = "ERC20 Token"

    print(f"🪙 Token: {name} ({symbol}), Decimals: {decimals}")
    print(f"📦 Contract: {token_addr}")
    print(f"👥 Holders: {len(holders)}; Proof index: {proof_index}")

    # Fetch balances and build leaves
    balances = []
    leaves = []
    for h in holders:
        bal = token.functions.balanceOf(h).call()
        balances.append(bal)
        leaves.append(leaf_hash(h, bal))

    # Build Merkle commitment
    tree = build_merkle_tree(leaves)
    root = merkle_root(tree)

    # Choose target for proof
    target_idx = proof_index
    target_addr = holders[target_idx]
    target_bal = balances[target_idx]
    target_leaf = leaves[target_idx]
    proof = merkle_proof(tree, target_idx)
    ok = verify_proof(target_leaf, proof, root)

    # Output
    print("🌳 Merkle Root:", to_hex(root))
    print("—")
    for i, (addr, bal) in enumerate(zip(holders, balances)):
        bal_fmt = bal / (10 ** decimals)
        marker = "← PROOF TARGET" if i == target_idx else ""
        print(f"[{i}] {addr}  balance={bal_fmt} {symbol}  {marker}")
    print("—")
    print(f"🍃 Leaf (address {target_idx}): {to_hex(target_leaf)}")
    print("🧾 Proof (sibling, position):")
    for depth, (sib, pos) in enumerate(proof):
        print(f"  L{depth}: sibling={to_hex(sib)} position={pos}")
    print("🧩 Soundness (inclusion verifies root):", "✅ OK" if ok else "❌ FAIL")

if __name__ == "__main__":
    main()
