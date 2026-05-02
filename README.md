# Cryptalyse

A Python toolkit for cryptocurrency wallet forensics, reconstruction, and transaction analysis built on top of BitcoinLib.

Cryptalyse extends BitcoinLib's wallet functionality with blockchain analysis capabilities designed for auditing, investigation, and portfolio tracking. It helps you go from a handful of known addresses to a fuller picture of wallet activity.

## Key Features

* Wallet Reconstruction - Given one or more known addresses, Cryptalyse identifies correlated input addresses using on-chain heuristics (e.g., common-input-ownership). Discovered addresses can be iteratively imported and rescanned to progressively reconstruct a partially known wallet.
* Transaction Export - Export all wallet transactions to CSV, with support for address tagging. Assign human-readable labels to addresses (e.g., "Olaf", "Exchange") so exports are readable and auditable instead of opaque hash strings.
* Input & Output Summaries - Aggregate transaction inputs and outputs by address or tag, making it easy to see who you received from and who you paid, with totals broken down by counterparty.
* Yearly Balance Reports — View opening balances by year for a quick historical overview of wallet activity.
Address Clustering — Group addresses likely controlled by the same entity, leveraging transaction graph analysis.

## Quick Example

```python
from pprint import pprint
from bitcoinlib.keys import Address
from datetime import datetime
from cryptalyse.cryptalyse import CryptalyseWallet

# Create a wallet from a known address
my_address = 'bc1q...234'
w = CryptalyseWallet.create('my_wallet', my_address, witness_type='segwit')

# Discover additional addresses belonging to this wallet
w.scan()
correlated = w.inputs_correlated

# Import discovered addresses and rescan
for addr in correlated:
    w.import_key(Address.import_address(addr))
w.scan()

# Tag known counterparts and export
tagged_addresses = {'bc1q...': 'Alice', 'bc1q...': 'Exchange'}
date_from = datetime(2022, 1, 1)
date_to = datetime.today()
w.export_to_excel('filename', tagged_addresses, date_from, date_to)
```

## Requirements

* Python 3
* [BitcoinLib](https://github.com/1200wd/bitcoinlib)
