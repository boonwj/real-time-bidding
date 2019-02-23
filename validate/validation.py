#!/usr/env/python3

import pandas as pd
import sys
import argparse 

class Auction:
    def __init__(self, val_files):
        self.val = pd.load_csv(val_files)
        return super().__init__(*args, **kwargs)
    pass

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
    parser.add_argument('-c', '--criterion', type=int, default=1, 
                        help='(1) Second price or (2) Second price & other bids')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    main(parse_args())
