#!/usr/env/python3

import pandas as pd
import sys
import argparse 

from collections import defaultdict

class Auction:
    def __init__(self, auction_file, criterion=1):
        self.auction_items = pd.read_csv(auction_file)
        self.criterion = criterion
        self.current_item = None
        self.payprice = None
        self.bids = []

    def next_item(self):
        for i, row in self.auction_items.iterrows():
            self.current_item = row['bidid']
            self.payprice = row['payprice']
            self.bids = []
            yield row.to_dict()

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

def main(args):
    pass

def parse_args():
    parser = argparse.ArgumentParser(description='Validate auction results')
    parser.add_argument('bidfile', type=str, 
                        help='Bid file')
    parser.add_argument('valfile', type=str, 
                        help='CSV file of validation data')
    parser.add_argument('-d', '--biddir', type=str, required=False, 
                        help='Directory of other bids')
    parser.add_argument('-b', '--budget', type=int, default=6250, 
                        help='Total budget to spend')
    parser.add_argument('-c', '--criterion', type=int, default=1, choices=(1, 2),
                        help='(1) Second price or (2) Second price & other bids')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    main(parse_args())
