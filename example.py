import os
from pprint import pprint
from bitcoinlib.keys import Address
from bitcoinlib.wallets import wallet_exists, wallet_delete_if_exists
from bitcoinlib.config.config import BCL_DATABASE_DIR
from cryptalyse.cryptalyse import CryptalyseWallet

test_database = BCL_DATABASE_DIR + '/bitcoinlib.tmp.sqlite'
# if os.path.isfile(test_database):
#     os.remove(test_database)

wallet_name = 'old_wallet_reconstruction'

wif = \
    'vpub5ZfErkiB4Aqwd22o7yQzhk8juBRV9GbXEZtyBAE7Bv9BvSxnRgk26K51LuK4mkGGikTwzJBLYgnFDvjEkqioZ7ZtNsqiQYFrMvjNB5sPYRT'

# addr = 'tb1q35cc0y9tfp0mswskpkka7cxqpap4st4wpzkewv'

# wallet_delete_if_exists(wallet_name, force=True, db_uri=test_database)
if wallet_exists(wallet_name, db_uri=test_database):
    w = CryptalyseWallet(wallet_name, db_uri=test_database)
else:
    w = CryptalyseWallet.create(wallet_name, wif, witness_type='segwit', db_uri=test_database)
    # w.import_key(Address.import_address('tb1qq0k9jh4npm5y7dgy5uj759ysgq6uzv7sp857np'))
# w.transactions_update()
# w.scan(scan_gap_limit=1)
w.info()

tagged_addresses = {
    '2NGZrVvZG92qGYqzTLjCAewvPZ7JE8S8VxE': 'Olaf',
    'mv4rnyY3Su5gjcDNzbMLKBQkBicCtHUtFB': 'Otto',
    'tb1q2m8pzuq8q4mqgdu43pv89wldx35kqkae42l7pr': 'Ingrid',
    'tb1q8zh0xnnjswzg8vw4wt3j0x8crf0fr3g94gw2k5': 'Iris',
    'tb1qcszk36t09h8m6sj2k7deklt9qkx46vt97mvlcv': 'Ingrid',
}

# Export all wallet's transactions as Comma seperated file
w.transactions_export_csv(tagged_addresses, file=open('%s.csv' % wallet_name, 'w'))

pprint(w.input_totals(tagged_addresses))
# pprint(w.output_totals())
# print(w.clusters())
# print(w.inputs_correlated)
