# -*- coding: utf-8 -*-
#
#    Blockchain analyser based on Python Bitcoinlib
#
#    To reconstruct, analyze and represent cryptocurrency wallets
#
#    © 2019 December - 1200 Web Development <http://1200wd.com/>
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
from bitcoinlib.wallets import HDWallet, wallet_exists
from bitcoinlib.encoding import to_hexstring


class CryptalyseWallet(HDWallet):

    def __init__(self, *args, **kwargs):
        self._inputs_correlated = []
        self._totals_year_open = {}
        HDWallet.__init__(self, *args, **kwargs)

    def input_totals(self, tagged_addresses=None):
        totals = {}
        wlt_addresses = self.addresslist()
        self._inputs_correlated = []
        if not tagged_addresses:
            tagged_addresses = {}
        for t in self.transactions():
            wallet_inputs_tots = [o.value for o in t.outputs if o.address in wlt_addresses]
            total_wallet_input = sum(wallet_inputs_tots)
            own_wallet_tx = bool([i.address for i in t.inputs if i.address in wlt_addresses])
            counted_wlt_input = False
            for i in t.inputs:
                prev_tx = "%s:%s" % (to_hexstring(i.prev_hash), i.output_n_int)
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
                    print(totals[i_addr])
                    t.info()
            if own_wallet_tx:
                cont_inps = [i.address for i in t.inputs if i.address not in wlt_addresses]
                if cont_inps:
                    self._inputs_correlated += cont_inps
        self._inputs_correlated = list(set(self._inputs_correlated))
        return totals

    def output_totals(self, tagged_addresses=None):
        totals = {}
        wlt_addresses = self.addresslist()
        if not tagged_addresses:
            tagged_addresses = {}
        for t in self.transactions_full():
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
                    totals[o_addr] = (new_value, totals[o_addr][1], [t.hash], set([i.address for i in t.inputs]))
                else:
                    totals[o_addr] = (o.value, o.address, [t.hash], set([i.address for i in t.inputs]))
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

    # def transactions(self, account_id=None, network=None, include_new=False, key_id=None, as_dict=False):
    #     txs = HDWallet.transactions(self, account_id, network, include_new, key_id, as_dict)
    #     return txs

    def balance_year_open(self):
        if not self._totals_year_open:
            self.transactions_export_csv(file=os.devnull)
        return self._totals_year_open

    def transactions_export_csv(self, tagged_addresses=None, date_from=None, date_to=None, file=sys.stdout):
        if not tagged_addresses:
            tagged_addresses = []
        denominator = self.network.denominator
        wlt_addresses = self.addresslist()
        year_old = 0

        print("transaction_date, transaction_hash, in/out, value_in, value_out, "
              "value_in_hr, value_out_hr, value_cumulative, value_cumulative_hr, "
              "in_name, out_name, in_addresses, out_addresses", file=file)
        for tei in self.transactions_export():
            if (date_from and tei[0] < date_from) or (date_to and tei[0] > date_to):
                continue

            value_in = 0 if tei[5] < 0 else tei[5]
            value_out = 0 if tei[5] > 0 else -tei[5]

            year = tei[0].year
            if year_old != year:
                year_balance = tei[6] - value_in + value_out
                self._totals_year_open.update({str(year): year_balance})
                year_old = year

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

            print("%s,%s,%s,%d,%d,%.8f,%.8f,%d,%.8f,%s,%s,%s,%s" %
                  (tei[0].strftime("%Y-%m-%d %H:%M:%S"), tei[1], tei[2],
                   value_in, value_out, value_in*denominator, value_out*denominator,
                   tei[6], tei[6]*denominator,
                   ";".join(addresses_in_tagged), ";".join(addresses_out_tagged),
                   ";".join(list(set(tei[3]))), ";".join(list(set(tei[4])))),
                  file=file)

    def export_balance_totals(self):
        raise Exception("Errors in HDWallet class for self.transactions(as_dict=True), see todo's")
        value_out = 0
        value_in = 0
        total_out = 0
        total_in = 0
        year = 0
        year_old = 0
        balance_end = 0
        year_first = None
        count = 0

        txs = self.transactions(as_dict=True)
        for tx in txs:
            count += 1
            year = tx['date'].year
            if year_old == 0:
                year_first = year
            last_tx = False
            if len(txs) == count:
                last_tx = True
            if year_old != year or last_tx:
                if last_tx:
                    if tx['is_output']:
                        value_out += -tx['value']
                    else:
                        value_in += tx['value']
                balance = balance_end + value_in - value_out
                if year_old:
                    print("Year %d" % year_old)
                    print("Total in: %s, Total out: %s, Balance %s" % (self.network.print_value(value_in),
                                                                       self.network.print_value(value_out),
                                                                       self.network.print_value(balance)))
                total_in += value_in
                total_out += value_out
                value_in = 0
                value_out = 0
                year_old = year
                balance_end = balance
            if tx['is_output']:
                value_out += -tx['value']
                if tx['value'] == 0:
                    print("null")
                print('out ', -tx['value'] / 100000000)
            else:
                value_in += tx['value']
                print('in ', tx['value'] / 100000000)

        print("Wallet active from %d to %d" % (year_first, year))
        print("Grand Total in: %s, Grand Total out: %s, End Balance %s" %
              (self.network.print_value(total_in), self.network.print_value(total_out),
               self.network.print_value(total_in - total_out)))