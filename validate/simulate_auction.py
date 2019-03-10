#!/usr/env/python3

import pandas as pd
import sys
import csv 
import argparse 
import glob
import os
import logging 

from collections import defaultdict

class Auction:
    def __init__(self, auction_file, criterion=1):
        self.auction_items = pd.read_csv(auction_file)
        self.criterion = criterion
        self.current_item = None
        self.payprice = None
        self.bids = []
        self.item_num = 0

    def next_item(self):
        for i, row in self.auction_items.iterrows():
            self.current_item = row['bidid']
            self.payprice = row['payprice']
            self.bids = []
            self.item_num = i+1
            yield i+1, row.to_dict()

    def bid(self, name, price):
        if name not in self.bids:
            self.bids.append((name, price))

    def winner(self):
        # Sort bids by their bid price
        self.bids = sorted(self.bids, reverse=True, key=lambda a : a[1])
        if not self.current_item:
            raise RuntimeError('There are no running auctions')
        if self.bids and self.bids[0][1] >= self.payprice:
            return (self.bids[0][0], self._get_price(self.criterion))
        else:
            return None

    def _get_price(self, criterion):
        # Winning criterion #1: 
        # The winning is determined if bid ≥ payprice and the actual paid price is the payprice from the data.
        price = self.payprice / 1000

        # Winning criterion #2: 
        # The winning is determined if bid ≥ payprice&otherSubmittedBids, and pay the highest among payprice&otherSubmittedBids.
        # If no other bids, payment will be similar to winning criterion 1
        if criterion == 2 and len(self.bids) > 1:
            price += self.bids[1][1] / 1000

        return price 

class AutomatedAuction(Auction):
    def __init__(self, auction_file, criterion=1):
        self.players = defaultdict(dict) # {name : { bids: {id : bidprice}, budget: amount, clicks: num, impressions: num) } }
        self.bidders = None
        return super().__init__(auction_file, criterion=criterion)

    def add_player(self, name, budget, bidfile):
        if name not in self.players:
            self.players[name]['budget'] = budget
            self.players[name]['cost'] = 0.0
            self.players[name]['clicks'] = 0
            self.players[name]['imps'] = 0
            self.players[name]['out_round'] = 0
            bids = {}
            with open(bidfile) as csvf:
                for row in csv.DictReader(csvf):
                    bids[row['bidid']] = float(row['bidprice'])
            self.players[name]['bids'] = bids
        else:
            raise ValueError(f'{name} has already been added')

    def run_auction(self):
        self._setup_bidders()
        logging.info(f'Players: {len(self.players)}')

        for item, row in self.next_item():
            if not self.bidders:
                break

            for bidder in self.bidders:
                bid = self._get_bid(bidder, self.current_item)
                if bid:
                    self.bid(bidder, bid)

            win_details = self.winner()
            if win_details:
                winner, payprice = win_details
                self._update_player(winner, payprice, row['click'])

    def _setup_bidders(self):
        self.bidders = set([x for x in self.players.keys()])

    def _get_bid(self, player, bidid):
        if player not in self.players:
            raise ValueError(f'{player} is not found within auction')
        try:
            return self.players[player]['bids'][bidid]
        except KeyError as exp:
            return None

    def stats(self, player):
        clicks = self.players[player]['clicks']
        imps = self.players[player]['imps']
        cost = self.players[player]['cost']
        out_round = self.players[player]['out_round']
        stats = {
            'clicks': clicks,
            'imps': imps,
            'ctr': float(clicks) / imps if imps != 0 else 0,
            'cpc': float(cost) / clicks if clicks != 0 else 99999,
            'cost': cost,
            'out_round': out_round
        }
        return stats

    def _update_player(self, winner, payprice, click):
        self.players[winner]['imps'] += 1
        self.players[winner]['clicks'] += click
        self.players[winner]['budget'] -= payprice
        self.players[winner]['cost'] += payprice
        if self.players[winner]['budget'] <= 0:
            self.players[winner]['out_round'] = self.item_num
            logging.info(f'OOB: {winner} is out on item {self.item_num}')
            self.bidders.remove(winner)

class ConstantAuction(AutomatedAuction):
    def __init__(self, auction_file, criterion=1):
        return super().__init__(auction_file, criterion=criterion)

    def add_player(self, name, budget, constant):
        if name not in self.players:
            self.players[name]['budget'] = budget
            self.players[name]['cost'] = 0.0
            self.players[name]['clicks'] = 0
            self.players[name]['imps'] = 0
            self.players[name]['bidamt'] = constant
        else:
            raise ValueError(f'{name} has already been added')

    def _get_bid(self, player, bidid):
        return self.players[player]['bidamt']

def main(args):
    players = []
    bidfiles = []
    if args.constant:
        auction = ConstantAuction(args.valfile, args.criterion)
        auction.add_player('you', args.budget, args.constant)
    else:
        auction = AutomatedAuction(args.valfile, args.criterion)

    if args.bidfile:
        bidfiles.extend(args.bidfile)

    if args.biddir:
        for f in glob.glob(os.path.join(args.biddir, '*.csv')):
            bidfiles.append(f)

    for bidfile in bidfiles:
        name = os.path.basename(bidfile)
        players.append(name)
        auction.add_player(name, args.budget, bidfile)
        logging.info(f'Added: {name}, {bidfile}')

    logging.info(f'Running auction: file: {args.valfile}, criterion: {args.criterion}, players: {players}')
    auction.run_auction()
    
    results = {}
    for player in players:
        results[player] = auction.stats{player}
        logging.info(results)
        print(results)

def parse_args():
    parser = argparse.ArgumentParser(description='Validate auction results')
    parser.add_argument('valfile', type=str, 
                        help='CSV file of validation data')
    parser.add_argument('-c', '--constant', type=int, 
                        help='Constant bid value')
    parser.add_argument('-f', '--bidfile', type=str, action='append',
                        help='Your bid file')
    parser.add_argument('-d', '--biddir', type=str, required=False, 
                        help='Directory of other bids')
    parser.add_argument('-b', '--budget', type=int, default=6250, 
                        help='Total budget to spend')
    parser.add_argument('-t', '--criterion', type=int, default=1, choices=(1, 2),
                        help='(1) Second price or (2) Second price & other bids')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(parse_args())
