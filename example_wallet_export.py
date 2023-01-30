# -*- coding: utf-8 -*-
#
#    Cryptalyse - Analyse cryptocurrency wallets
#    Export all wallets transactions and summarize inputs and outputs
#    © 2020 January - 1200 Web Development <http://1200wd.com/>

from pprint import pprint
from bitcoinlib.wallets import wallet_delete_if_exists
from cryptalyse.cryptalyse import CryptalyseWallet

from bitcoinlib.main import BCL_DATABASE_DIR
test_database = BCL_DATABASE_DIR + '/cryptalyse.sqlite'

wallet_name = 'example_wallet_export'
wif = \
    'vpub5ZfErkiB4Aqwd22o7yQzhk8juBRV9GbXEZtyBAE7Bv9BvSxnRgk26K51LuK4mkGGikTwzJBLYgnFDvjEkqioZ7ZtNsqiQYFrMvjNB5sPYRT'

wallet_delete_if_exists(wallet_name, db_uri=test_database)
w = CryptalyseWallet.create(wallet_name, wif, witness_type='segwit', db_uri=test_database)
w.scan(scan_gap_limit=1)

tagged_addresses = {
    '2NGZrVvZG92qGYqzTLjCAewvPZ7JE8S8VxE': 'Olaf',
    'mv4rnyY3Su5gjcDNzbMLKBQkBicCtHUtFB': 'Otto',
    'tb1q2m8pzuq8q4mqgdu43pv89wldx35kqkae42l7pr': 'Ingrid',
    'tb1q8zh0xnnjswzg8vw4wt3j0x8crf0fr3g94gw2k5': 'Iris',
    'tb1qcszk36t09h8m6sj2k7deklt9qkx46vt97mvlcv': 'Ingrid',
}

print("Created wallet '%s' with the following addresses:" % w.name)
pprint(tagged_addresses)

print("\nWallet's transactions as CSV:")
print(w.transactions_export_csv())

print("\nExport all wallet's transactions to comma separated file")
w.transactions_export_csv(tagged_addresses, file=open('%s.csv' % wallet_name, 'w'))
print("Done, exported to %s" % '%s.csv' % wallet_name)

print("\nShow yearly totals for this wallet")
pprint(w.balance_year_open())

print("\nTotals of all inputs for this wallet. Sums up inputs with same address or address-tag")
pprint(w.input_totals(tagged_addresses))
print("The item with the wallet's keyname (%s) accounts for internal transfers and change outputs" % wallet_name)

print("\nTotals of all outputs for this wallet. Sums up outputs with the same address or address-tag")
pprint(w.output_totals(tagged_addresses))
