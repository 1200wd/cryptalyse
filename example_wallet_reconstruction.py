# -*- coding: utf-8 -*-
#
#    Cryptalyse - Analyse cryptocurrency wallets
#    Reconstruct partially known wallet example
#    © 2020 January - 1200 Web Development <http://1200wd.com/>

from bitcoinlib.wallets import wallet_delete_if_exists
from bitcoinlib.keys import Address
from cryptalyse.cryptalyse import CryptalyseWallet


from bitcoinlib.main import BCL_DATABASE_DIR
test_database = BCL_DATABASE_DIR + '/cryptalyse.sqlite'

wallet_name = 'example_wallet_reconstruction'
known_addresses = ['tb1qe7h6l8sg7nf8z0rz6a4kfgavatjjac5qardt5z', 'tb1q35cc0y9tfp0mswskpkka7cxqpap4st4wpzkewv']

wallet_delete_if_exists(wallet_name, db_uri=test_database)
w = CryptalyseWallet.create(wallet_name, known_addresses[0], witness_type='segwit', db_uri=test_database)
for addr in known_addresses[1:]:
    key = Address.import_address(addr)
    w.import_key(key)
w.scan()

print("Created wallet '%s' with the following known addresses:" % w.name)
print(', '.join(known_addresses))

found_addrs = w.inputs_correlated
print("\nFound %d correlated input addresses: %s" % (len(found_addrs), ', '.join(found_addrs)))
print("\nAdd them to wallet and rescan")
for addr in found_addrs:
    key = Address.import_address(addr)
    w.import_key(key)
w.scan()
w.info()
