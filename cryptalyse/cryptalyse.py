# -*- coding: utf-8 -*-
#
#    Analyse and Export Crypto wallets
#
#    To reconstruct, analyze and represent cryptocurrency wallets
#
#    © 2019 - 2021 June - 1200 Web Development <http://1200wd.com/>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import sys
import os
from copy import deepcopy
from datetime import datetime
from bitcoinlib.wallets import Wallet


# Old price history (2013-2020), extracted from https://www.CryptoDataDownload.com
file_price_history = 'cryptalyse/cryptalyse/price_history_kraken.csv'

# Price history (2020+), fetched from Kraken API. Update with kraken_fetch_price_history.py
file_price_history2 = 'cryptalyse/cryptalyse/Kraken_BTCEUR_day.csv'


class CryptalyseWallet(Wallet):

    def __init__(self, *args, **kwargs):
        self._inputs_correlated = []
        self.columns_transactions_export = \
            ["transaction_date", "txid", "in/out", "value_in_btc", "value_out_btc", "fee_btc", "value_cumulative_btc",
            "value_eur", "value_cumulative_eur", "in_name", "out_name", "in_addresses",
            "out_addresses"]
        self._price_history = {}
        self.total_in = None
        self.total_out = None
        Wallet.__init__(self, *args, **kwargs)

    def _fetch_price_history(self):
        fp = open(file_price_history)
        self._price_history = {}
        for l in fp.readlines():
            pl = l.split(',')
            l_rate = 0
            try:
                l_rate = float(pl[6].strip())
            except:
                pass
            self._price_history.update({pl[0]: l_rate})
        fp2 = open(file_price_history2)
        for l in fp2.readlines():
            pl = l.split(',')
            l_rate = 0
            try:
                l_rate = float(pl[4].strip())
            except:
                pass
            self._price_history.update({pl[8]: l_rate})

    def price_history(self, date):
        if not self._price_history:
            self._fetch_price_history()
        return self._price_history[date]

    def input_totals(self, tagged_addresses=None, date_from=None, date_to=None):
        totals = {}
        wlt_addresses = self.addresslist()
        self._inputs_correlated = []
        if not tagged_addresses:
            tagged_addresses = {}
        for t in self.transactions():
            if t.date and (date_from and t.date < date_from) or (date_to and t.date > date_to):
                continue
            wallet_inputs_tots = [o.value for o in t.outputs if o.address in wlt_addresses]
            total_wallet_input = sum(wallet_inputs_tots)
            own_wallet_tx = bool([i.address for i in t.inputs if i.address in wlt_addresses])
            counted_wlt_input = False
            for i in t.inputs:
                prev_tx = "%s:%s" % (i.prev_txid.hex(), i.output_n_int)
                if i.address in wlt_addresses:
                    own_wallet_tx = True
                    i_addr = self.name
                else:
                    i_addr = tagged_addresses.get(i.address, i.address)
                if i_addr in totals:
                    if own_wallet_tx and i.address in wlt_addresses:
                        new_value = totals[i_addr][0] - i.value
                    else:
                        new_value = totals[i_addr][0] + i.value
                    if isinstance(totals[i_addr][2], set):
                        totals[i_addr][2].add(i.address)
                    if isinstance(totals[i_addr][3], list):
                        totals[i_addr][3].append(prev_tx)
                    new_total_wallet_input = totals[i_addr][1]
                    if not counted_wlt_input:
                        new_total_wallet_input = totals[i_addr][1] + total_wallet_input
                        counted_wlt_input = True
                    totals[i_addr] = (new_value, new_total_wallet_input, totals[i_addr][2], totals[i_addr][3])
                else:
                    counted_wlt_input = True
                    totals[i_addr] = (i.value, total_wallet_input, {i.address}, [prev_tx])
            if own_wallet_tx:
                cont_inps = [i.address for i in t.inputs if i.address not in wlt_addresses]
                if cont_inps:
                    self._inputs_correlated += cont_inps
        self._inputs_correlated = list(set(self._inputs_correlated))
        return totals

    def output_totals(self, tagged_addresses=None, date_from=None, date_to=None):
        totals = {}
        wlt_addresses = self.addresslist()
        if not tagged_addresses:
            tagged_addresses = {}
        for t in self.transactions_full():
            if t.date and (date_from and t.date < date_from) or (date_to and t.date > date_to):
                continue
            own_wallet_tx = bool([i.address for i in t.inputs if i.address in wlt_addresses])
            if not own_wallet_tx:
                continue
            for o in t.outputs:
                if o.address in wlt_addresses:
                    continue
                else:
                    o_addr = tagged_addresses.get(o.address, o.address)
                if o_addr in totals:
                    new_value = totals[o_addr][0] + o.value
                    if isinstance(totals[o_addr][1], list):
                        totals[o_addr][1].append(o.address)
                    totals[o_addr] = (new_value, totals[o_addr][1], totals[o_addr][2] + [t.txid],
                                      set([i.address for i in t.inputs]))
                else:
                    totals[o_addr] = (o.value, o.address, [t.txid], set([i.address for i in t.inputs]))
        return totals

    @property
    def inputs_correlated(self):
        self.input_totals()
        return self._inputs_correlated

    def clusters(self):
        outputs = self.output_totals()
        clusters = [r[3] for r in outputs.values()]
        normalized = False
        while not normalized:
            new_clusters = []
            normalized = True
            if len(clusters) < 2:
                break
            while len(clusters) > 1:
                c1 = clusters.pop()
                for c2 in clusters:
                    if c1 & c2:
                        c3 = c1.union(c2)
                        if c1 in new_clusters: new_clusters.remove(c1)
                        if c2 in new_clusters: new_clusters.remove(c2)
                        new_clusters.append(c3)
                        normalized = False
                        break
                    else:
                        new_clusters.append(c1) if c1 not in new_clusters else new_clusters
                        new_clusters.append(c2) if c2 not in new_clusters else new_clusters
            clusters = new_clusters
        return clusters

    def transactions_export_tuples(self, tagged_addresses=None, date_from=None, date_to=None, seperator2=","):
        if not date_from:
            date_from = datetime(2009, 1, 1)
        if not date_to:
            date_to = datetime.today()
        if not tagged_addresses:
            tagged_addresses = []
        denominator = self.network.denominator
        wlt_addresses = self.addresslist()
        if not self._price_history:
            self._fetch_price_history()

        tx_list = []
        prev_value_cumulative = 0
        for tei in self.transactions_export(skip_change=False):
            if (date_from and tei[0] < date_from) or (date_to and tei[0] > date_to):
                continue

            value_in = 0 if tei[5] < 0 else tei[5]
            value_out = 0 if tei[5] > 0 else -tei[5]
            if not (value_in or value_out):
                continue

            addresses_in_tagged = []
            for addr in tei[3]:
                if addr in wlt_addresses:
                    addresses_in_tagged.append("This wallet")
                elif addr in tagged_addresses:
                    addresses_in_tagged.append(tagged_addresses[addr])
                else:
                    addresses_in_tagged.append(addr)
            addresses_in_tagged = list(set(addresses_in_tagged))

            addresses_out_tagged = []
            for addr in tei[4]:
                if addr in wlt_addresses:
                    addresses_out_tagged.append("This wallet")
                elif addr in tagged_addresses:
                    addresses_out_tagged.append(tagged_addresses[addr])
                else:
                    addresses_out_tagged.append(addr)
            addresses_out_tagged = list(set(addresses_out_tagged))

            value_eur = 0
            value_date = tei[0].strftime("%Y-%m-%d")
            if value_date in self._price_history:
                value_eur = self.price_history(value_date) * ((value_in - value_out) * denominator)
            value_eur_cum = 0
            value_date = tei[0].strftime("%Y-%m-%d")
            if value_date in self._price_history:
                value_eur_cum = self.price_history(value_date) * tei[6]*denominator

            # Derive fee from value_in/out and cumulative values
            tx_fee = (value_in - value_out) + prev_value_cumulative - tei[6]
            prev_value_cumulative = tei[6]

            tx_list.append((tei[0], tei[1], tei[2],
                            (value_in * denominator), (value_out * denominator), tx_fee * denominator,
                            (tei[6] * denominator), value_eur, value_eur_cum,
                            seperator2.join(addresses_in_tagged), seperator2.join(addresses_out_tagged),
                            seperator2.join(list(set(tei[3]))), seperator2.join(list(set(tei[4])))))

        return tx_list

    def transactions_export_csv(self, tagged_addresses=None, date_from=None, date_to=None, file=sys.stdout,
                                seperator=";", seperator2=","):
        if not date_from:
            date_from = datetime(2009, 1, 1)
        if not date_to:
            date_to = datetime.today()
        if not tagged_addresses:
            tagged_addresses = []

        print(seperator.join(self.columns_transactions_export), file=file)
        for tp in self.transactions_export_tuples(tagged_addresses, date_from, date_to, seperator2):
            tx_item = (tp[0].strftime("%Y-%m-%d %H:%M:%S"), tp[1], tp[2],
                            "%.8f" % tp[3], "%.8f" % tp[4],
                            "%.2f" % tp[5], "%.8f" % tp[6], "%2f" % tp[7], tp[8], tp[9], tp[10], tp[11])
            print(seperator.join(tx_item), file=file)

    def export_balance_totals(self, last_year=None):
        txs = self.transactions_export()
        txs_totals = [(tei[0].year, 0 if tei[5] < 0 else tei[5], 0 if tei[5] > 0 else -tei[5], tei[6]) for tei in txs]
        dt_year_totals = {}
        if not last_year:
            last_year = datetime.today().year
        last_balance = 0
        total_in = total_out = 0
        if txs_totals:
            # txs_totals[len(txs_totals) - 1][0] + 1
            for year in range((txs_totals[0][0]), last_year + 1):
                if not year in [l[0] for l in txs_totals]:
                    dt_year_totals.update({year: (0, 0, 0, last_balance)})
                else:
                    balance = [l[3] for l in txs_totals if l[0] == year][-1]
                    yr_total_in = sum([l[1] for l in txs_totals if l[0] == year])
                    yr_total_out = sum([l[2] for l in txs_totals if l[0] == year])
                    fees = (yr_total_in - yr_total_out) - (balance - last_balance)
                    dt_year_totals.update({year: (yr_total_in, yr_total_out, fees, balance)})
                    last_balance = balance
                    total_in += yr_total_in
                    total_out += yr_total_out

        return dt_year_totals

    def export_utxos_year(self, last_year=None):
        utxos = {}
        year_old = 0
        year = 0
        utxos_year = {}
        if not last_year:
            last_year = datetime.today().year
        txs = self.transactions()
        for tx in txs:
            year = tx.date.year
            utxos_old = deepcopy(utxos)
            if tx.outgoing_tx:
                for i in tx.inputs:
                    del(utxos[(i.prev_txid.hex(), i.output_n_int)])
                for o in tx.outputs:
                    if o.address in self.addresslist():
                        utxos.update({(tx.txid, o.output_n): (o.value, o.address)})
            else:
                for o in tx.outputs:
                    if o.address not in self.addresslist():
                        continue
                    utxos.update({(tx.txid, o.output_n): (o.value, o.address)})
            if year != year_old:
                if year_old != 0:
                    for yr in range(year_old, year):
                        utxos_year.update({yr: utxos_old})
                year_old = year
        if year and year < last_year:
            for yr in range(year, last_year+1):
                utxos_year.update({yr: utxos})

        return utxos_year



