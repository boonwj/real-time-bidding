import unittest
import simulate_auction

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
        self.assertEqual(0, data['click'])
        self.assertEqual(4, data['weekday'])
        self.assertEqual('bbcb813b6166538503d8b33a5602d7d72f6019dc', data['bidid'])
        self.assertEqual(300, data['bidprice'])

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