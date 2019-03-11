import unittest
import simulate_auction
import pandas as pd
class TestAuction(unittest.TestCase):
    def setUp(self):
        self.auction = simulate_auction.Auction('test/test_auction.csv')

    def test_items(self):
        expect_bidids = [
            'bbcb813b6166538503d8b33a5602d7d72f6019dc',
            '5a07316c49477cb5d9b4d5aa39c27d6c3be7f92d',
            'f6ece71dae81d6b16bfb24ad6dd5611472d4c673',
            'b4d5c57c9b38ff5a12954fa01e11931b4e6bfbbb',
            '0899bf144249458ea9c89188473694bf44c7ca15',
            'f4c6a9a3b1db6da035c7e2a36d4f5e389095beca',
            '786a2940f225482dc04d455dc7a7fea436b02e03', 
            '17ada861c6ed0616f88312ba0d3d76c0f95b4940',
            '6abd8ef3eb678b1afe67dc0cff0aa58413fbf29a',
        ]

        expect_payprice = [23, 75, 65, 6, 5, 22, 31, 20, 58,]

        for i, x in enumerate(self.auction.next_item()):
            self.assertEqual(expect_bidids[i], self.auction.current_item)
            self.assertEqual(expect_payprice[i], self.auction.payprice)

    def test_auction_item_data(self):
        data = next(self.auction.next_item())
        self.assertEqual(0, self.auction.click)
        self.assertEqual('bbcb813b6166538503d8b33a5602d7d72f6019dc', self.auction.current_item)
        self.assertEqual(23, self.auction.payprice)

    def test_bids(self):
        self.auction.bid('player1', 100)
        self.auction.bid('player2', 120)
        self.assertListEqual(self.auction.bids, [('player1', 100), ('player2', 120)])

    def test_winner_bad_bids(self):
        data = next(self.auction.next_item())
        self.auction.bid('p1', 1)
        self.auction.bid('p2', 2)
        self.assertEqual(None, self.auction.winner()) 

    def test_winner_criterion_1(self):
        data = next(self.auction.next_item())
        self.auction.bid('p1', 100)
        self.auction.bid('p2', 220)
        self.auction.bid('p3', 210)
        self.assertEqual(('p2', 0.023), self.auction.winner()) 

    def test_winner_criterion_2(self):
        self.auction.criterion = 2
        data = next(self.auction.next_item())
        self.auction.bid('p1', 100)
        self.auction.bid('p2', 220)
        self.auction.bid('p3', 210)
        name, price = self.auction.winner()
        self.assertEqual('p2', name)
        self.assertAlmostEqual(0.233, price)

class TestAutomatedAuction(unittest.TestCase):
    def setUp(self):
        self.auto_auction = simulate_auction.AutomatedAuction('test/test_auction.csv')
        self.p1_bids = 'test/p1_bids.csv'
        self.p2_bids = 'test/p2_bids.csv'

    def test_players_add(self):
        exp_df = pd.read_csv(self.p1_bids, index_col='bidid')
        self.auto_auction.add_player('p1', 6250, self.p1_bids) 
        self.assertEqual(6250, self.auto_auction.players['p1']['budget'])
        self.assertEqual(0, self.auto_auction.players['p1']['clicks'])
        self.assertEqual(0, self.auto_auction.players['p1']['imps'])
        self.assertEqual(0, self.auto_auction.players['p1']['cost'])
        # Implementation has changed away from dataframes
        # pd.testing.assert_frame_equal(exp_df, self.auto_auction.players['p1']['bids'])
    
    def test_get_player_bids(self):
        exp_df = pd.read_csv(self.p1_bids, index_col='bidid')
        self.auto_auction.add_player('p1', 6250, self.p1_bids) 
        self.assertEqual(241, self.auto_auction._get_bid('p1', 'f4c6a9a3b1db6da035c7e2a36d4f5e389095beca'))
        self.assertEqual(227, self.auto_auction._get_bid('p1', '17ada861c6ed0616f88312ba0d3d76c0f95b4940'))
        self.assertEqual(None, self.auto_auction._get_bid('p1', 'invalid-bid-id'))

    def test_player_in_auction(self):
        exp_df = pd.read_csv(self.p1_bids, index_col='bidid')
        self.auto_auction.add_player('p1', 10, self.p1_bids) 
        self.auto_auction._setup_bidders()
        self.auto_auction._update_player('p1', 9)
        self.assertEqual(set(['p1']), self.auto_auction.bidders)
        self.auto_auction._update_player('p1', 0.2)
        self.assertEqual(set(['p1']), self.auto_auction.bidders)
        self.auto_auction._update_player('p1', 0.90)
        self.assertEqual(set(), self.auto_auction.bidders)

        # result from bidding
        self.assertEqual(0, self.auto_auction.stats('p1')['clicks'])
        self.assertEqual(3, self.auto_auction.stats('p1')['imps'])
        self.assertEqual(10.1, self.auto_auction.stats('p1')['cost'])
        self.assertAlmostEqual(99999, self.auto_auction.stats('p1')['cpc'])
        self.assertAlmostEqual(0, self.auto_auction.stats('p1')['ctr'])

    def test_run_auction(self):
        exp_df = pd.read_csv(self.p1_bids, index_col='bidid')
        self.auto_auction.add_player('p1', 10, self.p1_bids) 
        self.auto_auction.add_player('p2', 10, self.p2_bids) 
        self.auto_auction.run_auction()

        # result from bidding
        p1_stats = self.auto_auction.stats('p1')
        self.assertEqual(1, p1_stats['clicks'])
        self.assertEqual(5, p1_stats['imps'])
        self.assertEqual(0.139, p1_stats['cost'])
        self.assertAlmostEqual(0.139/1, p1_stats['cpc'])
        self.assertAlmostEqual(1/5, p1_stats['ctr'])

        p2_stats = self.auto_auction.stats('p2')
        self.assertEqual(0, p2_stats['clicks'])
        self.assertEqual(4, p2_stats['imps'])
        self.assertEqual(0.166, p2_stats['cost'])
        self.assertAlmostEqual(99999, p2_stats['cpc'])
        self.assertAlmostEqual(0, p2_stats['ctr'])


class TestConstantAuction(unittest.TestCase):
    def setUp(self):
        self.constant_auction = simulate_auction.ConstantAuction('test/test_auction.csv')
    
    def test_constant_auction(self):
        self.constant_auction.add_player('p1', 10, 150) 
        self.constant_auction.run_auction()
        p1_stats = self.constant_auction.stats('p1')
        self.assertEqual(1, p1_stats['clicks'])
        self.assertEqual(9, p1_stats['imps'])
        self.assertEqual(0.305, p1_stats['cost'])
        self.assertAlmostEqual(0.305/1, p1_stats['cpc'])
        self.assertAlmostEqual(1/9, p1_stats['ctr'])
