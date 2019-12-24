from pprint import pprint
from bitcoinlib.wallets import wallet_exists
from cryptalyse.cryptalyse import CryptalyseWallet

from bitcoinlib.main import BCL_DATABASE_DIR
import os
test_database = BCL_DATABASE_DIR + '/bitcoinlib.tmp.sqlite'

wallet_name = 'example_wallet_reconstruction'

wif = \
    'vpub5ZfErkiB4Aqwd22o7yQzhk8juBRV9GbXEZtyBAE7Bv9BvSxnRgk26K51LuK4mkGGikTwzJBLYgnFDvjEkqioZ7ZtNsqiQYFrMvjNB5sPYRT'


if wallet_exists(wallet_name, db_uri=test_database):
    w = CryptalyseWallet(wallet_name, db_uri=test_database)
else:
    w = CryptalyseWallet.create(wallet_name, wif, witness_type='segwit', db_uri=test_database)
# w.scan(scan_gap_limit=1)

tagged_addresses = {
    '2NGZrVvZG92qGYqzTLjCAewvPZ7JE8S8VxE': 'Olaf',
    'mv4rnyY3Su5gjcDNzbMLKBQkBicCtHUtFB': 'Otto',
    'tb1q2m8pzuq8q4mqgdu43pv89wldx35kqkae42l7pr': 'Ingrid',
    'tb1q8zh0xnnjswzg8vw4wt3j0x8crf0fr3g94gw2k5': 'Iris',
    'tb1qcszk36t09h8m6sj2k7deklt9qkx46vt97mvlcv': 'Ingrid',
}

print("\nExport all wallet's transactions to comma seperated file")
w.transactions_export_csv(tagged_addresses, file=open('%s.csv' % wallet_name, 'w'))
print("Done, exported to %s" % '%s.csv' % wallet_name)

print("\nShow yearly totals for this wallet")
pprint(w.balance_year_open())

print("\nTotals of all inputs for this wallet. Sums up inputs with same address or address-tag")
pprint(w.input_totals(tagged_addresses))

print("\nTotals of all outputs for this wallet. Sums up outputs with the same address or address-tag")
pprint(w.output_totals())
