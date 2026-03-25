---
name: optimism
description: Query Optimism blockchain data with USD pricing — wallet balances, token info, transaction details, gas analysis, contract inspection, whale detection, and live network stats. Uses Optimism RPC + CoinGecko. No API key required.
version: 0.1.0
author: dieutx
license: MIT
metadata:
  hermes:
    tags: [Optimism, Blockchain, Crypto, Web3, RPC, DeFi, EVM, L2, OP Stack]
    related_skills: [base, solana, ethereum, arbitrum]
---

# Optimism Blockchain Skill

Query Optimism on-chain data enriched with USD pricing via CoinGecko.
8 commands: wallet portfolio, token info, transactions, gas analysis,
contract inspection, whale detection, network stats, and price lookup.

No API key needed. Uses only Python standard library (urllib, json, argparse).

---

## When to Use

- User asks for an Optimism wallet balance, token holdings, or portfolio value
- User wants to inspect a specific transaction by hash
- User wants ERC-20 token metadata, price, supply, or market cap
- User wants to understand Optimism gas costs (OP Stack L2 + L1 data fees)
- User wants to inspect a contract (ERC type detection, proxy resolution)
- User wants to find large ETH transfers (whale detection)
- User wants Optimism network health, gas price, or ETH price
- User asks "what's the price of OP/SNX/VELO/ETH?"

---

## Prerequisites

The helper script uses only Python standard library (urllib, json, argparse).
No external packages required.

Pricing data comes from CoinGecko's free API (no key needed, rate-limited
to ~10-30 requests/minute). For faster lookups, use `--no-prices` flag.

---

## Quick Reference

RPC endpoint (default): https://mainnet.optimism.io
Override: export OPTIMISM_RPC_URL=https://your-private-rpc.com

Helper script path: ~/.hermes/skills/blockchain/optimism/scripts/optimism_client.py

```
python3 optimism_client.py wallet   <address> [--limit N] [--all] [--no-prices]
python3 optimism_client.py tx       <hash>
python3 optimism_client.py token    <contract_address>
python3 optimism_client.py gas
python3 optimism_client.py contract <address>
python3 optimism_client.py whales   [--min-eth N]
python3 optimism_client.py stats
python3 optimism_client.py price    <contract_address_or_symbol>
```

---

## Procedure

### 0. Setup Check

```bash
python3 --version

# Optional: set a private RPC for better rate limits
export OPTIMISM_RPC_URL="https://mainnet.optimism.io"

# Confirm connectivity
python3 ~/.hermes/skills/blockchain/optimism/scripts/optimism_client.py stats
```

### 1. Wallet Portfolio

Get ETH balance and ERC-20 token holdings with USD values.
Checks ~15 well-known Optimism tokens (USDC, USDT, DAI, OP, SNX, VELO, etc.)
via on-chain `balanceOf` calls. Tokens sorted by value, dust filtered.

```bash
python3 ~/.hermes/skills/blockchain/optimism/scripts/optimism_client.py \
  wallet 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
```

Flags:
- `--limit N` — show top N tokens (default: 20)
- `--all` — show all tokens, no dust filter, no limit
- `--no-prices` — skip CoinGecko price lookups (faster, RPC-only)

### 2. Transaction Details

```bash
python3 ~/.hermes/skills/blockchain/optimism/scripts/optimism_client.py \
  tx 0xabc123...your_tx_hash_here
```

### 3. Token Info

```bash
python3 ~/.hermes/skills/blockchain/optimism/scripts/optimism_client.py \
  token 0x0b2c639c533813f4aa9d7837caf62653d097ff85
```

### 4. Gas Analysis

Optimism is an OP Stack L2. Total transaction cost = L2 execution fee + L1
data posting fee. The L1 data fee depends on calldata size and L1 gas prices.

```bash
python3 ~/.hermes/skills/blockchain/optimism/scripts/optimism_client.py gas
```

### 5. Contract Inspection

```bash
python3 ~/.hermes/skills/blockchain/optimism/scripts/optimism_client.py \
  contract 0x0b2c639c533813f4aa9d7837caf62653d097ff85
```

### 6. Whale Detector

```bash
python3 ~/.hermes/skills/blockchain/optimism/scripts/optimism_client.py \
  whales --min-eth 1.0
```

### 7. Network Stats

```bash
python3 ~/.hermes/skills/blockchain/optimism/scripts/optimism_client.py stats
```

### 8. Price Lookup

```bash
python3 ~/.hermes/skills/blockchain/optimism/scripts/optimism_client.py price OP
python3 ~/.hermes/skills/blockchain/optimism/scripts/optimism_client.py price SNX
python3 ~/.hermes/skills/blockchain/optimism/scripts/optimism_client.py price ETH
```

Known symbols: ETH, WETH, USDC, USDC.e, USDT, DAI, OP, wstETH, rETH,
SNX, LINK, WBTC, AAVE, sUSD, PERP, VELO.

---

## Pitfalls

- **CoinGecko rate-limits** — free tier allows ~10-30 requests/minute.
  Use `--no-prices` for speed.
- **Public RPC rate-limits** — for production use, set OPTIMISM_RPC_URL
  to a private endpoint (Alchemy, QuickNode, Infura).
- **Wallet shows known tokens only** — checks ~15 popular tokens.
  Use `token` command for any specific contract.
- **OP Stack L1 data fees** — total tx cost includes an L1 data posting
  fee not shown in gas estimates. Actual costs may be higher.
- **Whale detector scans latest block only** — point-in-time snapshot.
- **Retry on 429** — both RPC and CoinGecko calls retry up to 2 times
  with exponential backoff.

---

## Verification

```bash
python3 ~/.hermes/skills/blockchain/optimism/scripts/optimism_client.py stats
```
