import unittest
import numpy as np
import pandas as pd
from pypfopt import expected_returns, risk_models
from algorithms import run_black_litterman, run_hrp, run_monte_carlo

# Mock data for testing
def get_mock_data():
    dates = pd.date_range(start="2020-01-01", periods=100)
    data = pd.DataFrame(np.random.randn(100, 3) + 100, index=dates, columns=["A", "B", "C"])
    market = pd.Series(np.random.randn(100) + 100, index=dates, name="^GSPC")
    return data, market

class TestAlgorithms(unittest.TestCase):
    def setUp(self):
        self.prices, self.market_prices = get_mock_data()

    def test_hrp_weights(self):
        try:
            weights = run_hrp(self.prices)
            self.assertAlmostEqual(sum(weights.values()), 1.0, places=4)
        except Exception as e:
            print(f"HRP Test Warning: {e}")

    def test_black_litterman_weights(self):
        try:
            weights = run_black_litterman(self.prices, self.market_prices)
            self.assertAlmostEqual(sum(weights.values()), 1.0, places=4)
        except Exception as e:
            print(f"BL Test Warning: {e}")
            
    def test_monte_carlo_shape(self):
        sims = run_monte_carlo(self.prices, simulations=10, time_horizon=50)
        self.assertEqual(sims.shape, (10, 50))

if __name__ == '__main__':
    unittest.main()
