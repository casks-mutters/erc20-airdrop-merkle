# README.md
# erc20-airdrop-merkle

## Overview
This repo demonstrates a Web3 “soundness” workflow akin to zk/rollup systems (e.g., Aztec-style commitments): we fetch ERC-20 balances for a set of addresses, commit to the dataset with a Keccak-based Merkle root, and verify an inclusion proof for one holder. While this script doesn’t produce a true zero-knowledge proof, it models the commitment-and-proof pattern used by ZK systems where soundness guarantees ensure that invalid statements cannot be proven.

## Files
- app.py — CLI tool that:
  - Connects to an Ethereum RPC
  - Reads ERC-20 balances for provided holders
  - Builds a Merkle tree of leaves hash(address || balance_wei)
  - Prints the Merkle root
  - Emits and verifies an inclusion proof for a selected holder
- README.md — this documentation

## Requirements
- Python 3.10+
- web3.py
- An Ethereum RPC endpoint (Infura/Alchemy/local node)

## Installation
1) Create and activate a virtual environment (optional).
2) Install dependency:
   pip install web3
3) Open app.py and replace your_api_key in RPC_URL with your Infura key or set a full RPC URL you control.

## Usage
Basic:
   python app.py <erc20_address> <holder1> [holder2 ...] [--index N]

Parameters:
- erc20_address: Contract address of the ERC-20 token
- holderN: One or more Ethereum addresses to include in the Merkle set
- --index N: Optional, which holder to generate and verify a proof for (0-based; default 0)

## Examples
1) Single holder (USDC on Mainnet example address, replace RPC key first):
   python app.py 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 0x742d35Cc6634C0532925a3b844Bc454e4438f44e

2) Multiple holders with a proof for the 2nd address (index 1):
   python app.py 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48 0x742d35Cc6634C0532925a3b844Bc454e4438f44e 0x53d284357ec70ce289d6d64134dfac8e511c8a3d --index 1

3) Testnet token (Sepolia) with three addresses:
   python app.py <sepolia_token_address> <addr1> <addr2> <addr3> --index 2

## What you’ll see
- Detected network name (e.g., Ethereum Mainnet)
- Token metadata (name, symbol, decimals)
- Each holder with formatted balance
- Merkle root for the dataset
- The chosen leaf and a step-by-step proof list (sibling hash + position)
- Final verification of proof against the root (soundness check)

## How it relates to Aztec/ZK soundness
- ZK rollups and privacy systems (Aztec-like designs) rely on succinct commitments (roots) over large datasets
- Users prove statements like “I’m in this set” using short inclusion proofs without revealing the entire set
- This demo mirrors that pattern using ERC-20 balances as the committed data, demonstrating the soundness aspect of proofs of inclusion

## Notes
- Works on any EVM network; plug in an RPC for Mainnet, Sepolia, Polygon, Optimism, Arbitrum, etc.
- Balances are read live from the chain; large holder lists may hit rate limits. Start with small sets (e.g., 4–32).
- The Merkle construction uses Keccak(left || right) and duplicates the last node on odd levels, a common approach in rollups and airdrop snapshots.
- Security tip: for production-grade airdrops, persist the root and publish proofs; verify on-chain in a MerkleDistributor-style contract, or integrate with actual ZK circuits for privacy.
