---
name: arbitrum
description: Query Arbitrum One blockchain data with USD pricing — wallet balances, token info, transaction details, gas analysis, contract inspection, whale detection, and live network stats. Uses Arbitrum RPC + CoinGecko. No API key required.
version: 0.1.0
author: dieutx
license: MIT
metadata:
  hermes:
    tags: [Arbitrum, Blockchain, Crypto, Web3, RPC, DeFi, EVM, L2, Nitro]
    related_skills: [base, solana, ethereum, optimism]
---

# Arbitrum One Blockchain Skill

Query Arbitrum One on-chain data enriched with USD pricing via CoinGecko.
8 commands: wallet portfolio, token info, transactions, gas analysis,
contract inspection, whale detection, network stats, and price lookup.

No API key needed. Uses only Python standard library (urllib, json, argparse).

---

## When to Use

- User asks for an Arbitrum wallet balance, token holdings, or portfolio value
- User wants to inspect a specific transaction by hash
- User wants ERC-20 token metadata, price, supply, or market cap
- User wants to understand Arbitrum gas costs (Nitro model)
- User wants to inspect a contract (ERC type detection, proxy resolution)
- User wants to find large ETH transfers (whale detection)
- User wants Arbitrum network health, gas price, or ETH price
- User asks "what's the price of ARB/GMX/LINK/ETH?"

---

## Prerequisites

The helper script uses only Python standard library (urllib, json, argparse).
No external packages required.

Pricing data comes from CoinGecko's free API (no key needed, rate-limited
to ~10-30 requests/minute). For faster lookups, use `--no-prices` flag.

---

## Quick Reference

RPC endpoint (default): https://arb1.arbitrum.io/rpc
Override: export ARBITRUM_RPC_URL=https://your-private-rpc.com

Helper script path: ~/.hermes/skills/blockchain/arbitrum/scripts/arbitrum_client.py

```
python3 arbitrum_client.py wallet   <address> [--limit N] [--all] [--no-prices]
python3 arbitrum_client.py tx       <hash>
python3 arbitrum_client.py token    <contract_address>
python3 arbitrum_client.py gas
python3 arbitrum_client.py contract <address>
python3 arbitrum_client.py whales   [--min-eth N]
python3 arbitrum_client.py stats
python3 arbitrum_client.py price    <contract_address_or_symbol>
```

---

## Procedure

### 0. Setup Check

```bash
python3 --version

# Optional: set a private RPC for better rate limits
export ARBITRUM_RPC_URL="https://arb1.arbitrum.io/rpc"

# Confirm connectivity
python3 ~/.hermes/skills/blockchain/arbitrum/scripts/arbitrum_client.py stats
```

### 1. Wallet Portfolio

Get ETH balance and ERC-20 token holdings with USD values.
Checks ~15 well-known Arbitrum tokens (USDC, USDT, DAI, WBTC, ARB, GMX, etc.)
via on-chain `balanceOf` calls. Tokens sorted by value, dust filtered.

```bash
python3 ~/.hermes/skills/blockchain/arbitrum/scripts/arbitrum_client.py \
  wallet 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
```

Flags:
- `--limit N` — show top N tokens (default: 20)
- `--all` — show all tokens, no dust filter, no limit
- `--no-prices` — skip CoinGecko price lookups (faster, RPC-only)

### 2. Transaction Details

```bash
python3 ~/.hermes/skills/blockchain/arbitrum/scripts/arbitrum_client.py \
  tx 0xabc123...your_tx_hash_here
```

### 3. Token Info

```bash
python3 ~/.hermes/skills/blockchain/arbitrum/scripts/arbitrum_client.py \
  token 0xaf88d065e77c8cc2239327c5edb3a432268e5831
```

### 4. Gas Analysis

Arbitrum uses the Nitro execution model where L1 data costs are reflected
in the effective gas price — there is no separate L1 fee field like on
OP Stack chains.

```bash
python3 ~/.hermes/skills/blockchain/arbitrum/scripts/arbitrum_client.py gas
```

### 5. Contract Inspection

```bash
python3 ~/.hermes/skills/blockchain/arbitrum/scripts/arbitrum_client.py \
  contract 0xaf88d065e77c8cc2239327c5edb3a432268e5831
```

### 6. Whale Detector

```bash
python3 ~/.hermes/skills/blockchain/arbitrum/scripts/arbitrum_client.py \
  whales --min-eth 1.0
```

### 7. Network Stats

```bash
python3 ~/.hermes/skills/blockchain/arbitrum/scripts/arbitrum_client.py stats
```

### 8. Price Lookup

```bash
python3 ~/.hermes/skills/blockchain/arbitrum/scripts/arbitrum_client.py price ARB
python3 ~/.hermes/skills/blockchain/arbitrum/scripts/arbitrum_client.py price GMX
python3 ~/.hermes/skills/blockchain/arbitrum/scripts/arbitrum_client.py price ETH
```

Known symbols: ETH, WETH, USDC, USDC.e, USDT, DAI, WBTC, ARB, wstETH,
rETH, GMX, LINK, UNI, CRV, AAVE, STG.

---

## Pitfalls

- **CoinGecko rate-limits** — free tier allows ~10-30 requests/minute.
  Use `--no-prices` for speed.
- **Public RPC rate-limits** — for production use, set ARBITRUM_RPC_URL
  to a private endpoint (Alchemy, QuickNode, Infura).
- **Wallet shows known tokens only** — checks ~15 popular tokens.
  Use `token` command for any specific contract.
- **Nitro gas model** — L1 data costs are baked into the effective gas
  price, unlike OP Stack chains which show a separate L1 fee field.
- **Whale detector scans latest block only** — point-in-time snapshot.
- **Retry on 429** — both RPC and CoinGecko calls retry up to 2 times
  with exponential backoff.

---

## Verification

```bash
python3 ~/.hermes/skills/blockchain/arbitrum/scripts/arbitrum_client.py stats
```
