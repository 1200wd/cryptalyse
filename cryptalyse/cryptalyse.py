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
from bitcoinlib.wallets import HDWallet, wallet_exists
from bitcoinlib.encoding import to_hexstring


class CryptalyseWallet(HDWallet):

    def __init__(self, *args, **kwargs):
        self._inputs_correlated = []
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
                    totals[i_addr] = (i.value, total_wallet_input, set([i.address]), [prev_tx])
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

    def transactions_export_csv(self, tagged_addresses=None, date_from=None, date_to=None, file=sys.stdout):
        if not tagged_addresses:
            tagged_addresses = []
        denominator = self.network.denominator
        wlt_addresses = self.addresslist()

        print("transaction_date, transaction_hash, in/out, addresses_in, addresses_out, "
              "addresses_in_tagged, addresses_out_tagged, value_in, value_out, "
              "value_human_in, value_human_out, value_cumulative, value_cumulative_human", file=file)
        for tei in self.transactions_export():
            if tei[0] < date_from or tei[0] > date_to:
                pass

            value_in = 0 if tei[5] < 0 else tei[5]
            value_out = 0 if tei[5] > 0 else -tei[5]

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

            print("%s,%s,%s,%s,%s,%s,%s,%d,%d,%.8f,%.8f,%d,%.8f" %
                  (tei[0].strftime("%Y-%m-%d %H:%M:%S"), tei[1], tei[2],
                   ";".join(list(set(tei[3]))), ";".join(list(set(tei[4]))),
                   ";".join(addresses_in_tagged), ";".join(addresses_out_tagged),
                   value_in, value_out, value_in*denominator, value_out*denominator,
                   tei[6], tei[6]*denominator), file=file)
