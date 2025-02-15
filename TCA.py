import numpy as np
import pandas as pd

class TransactionCostSimulator():
  def __init__(self):

    # Number of Paths for simulation
    self.num_paths = 1000

    # Base TC cost for Corporate Bonds which serves as the mean for the stochastic process (Ornstein-Uhlenbeck)
    self.base_mean = 5

    # Mean reversion speed and volatility for Base TC Ornstein-Uhlenbeck process
    self.mean_reversion_speed = 0.5
    self.base_vol = 0.001

    # Days and Timesteps for stochastic process
    self.n_days = 10
    self.timestep = 1/252

    self.sector_choice = "Industrials"
    self.ratings_choice = "BBB+"
    self.maturity_choice = 10
    self.liquidity_choice = 3
    self.lotsize_choice = 100000

    # Factors that drive TC in addition to the Base TC
    self.sectors = ['Industrials', 'Financials', 'Utilities', 'Transportation', 'Communication Services', 'Consumer Discretionary', 'Consumer Staples', 'Energy', 'Healthcare', 'Technology']
    self.ratings = ['AAA', 'AA+', 'AA', 'AA-', 'A+', 'A', 'A-', 'BBB+', 'BBB', 'BBB-', 'BB+', 'BB', 'BB-', 'B+', 'B', 'B-']
    self.maturity = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]
    self.liquidity_scores = [1, 2, 3, 4, 5] # Where 1 is least liquid and 5 is most liquid
    self.lot_size = [100000, 1000000, 5000000, 10000000]

    # Long-term mean and volatility for transaction costs by Factor that will serve as parameters for their own OU process that will be additive/subtractive to the base TC
    self.sectors_mean = {'Industrials': 7, 'Financials': 3, 'Utilities': 4, 'Transportation': 5, 'Communication Services': 7, 'Consumer Discretionary': 2, 'Consumer Staples': 2, 'Energy': 8, 'Healthcare': 6, 'Technology': 4}
    self.sectors_vol = {'Industrials': 0.001, 'Financials': 0.1, 'Utilities': 0.1, 'Transportation': 0.1, 'Communication Services': 0.1, 'Consumer Discretionary': 0.1, 'Consumer Staples': 0.1, 'Energy': 0.1, 'Healthcare': 0.1, 'Technology': 0.1}
    self.ratings_mean = {'AAA': 2, 'AA+': 2, 'AA': 2, 'AA-': 2, 'A+': 3, 'A': 3, 'A-': 3, 'BBB+': 4, 'BBB': 4, 'BBB-': 4, 'BB+': 5, 'BB': 5, 'BB-': 5, 'B+': 6, 'B': 6, 'B-': 6}
    self.ratings_vol = {'AAA': 0.1, 'AA+': 0.1, 'AA': 0.1, 'AA-': 0.1, 'A+': 0.1, 'A': 0.1, 'A-': 0.1, 'BBB+': 0.001, 'BBB': 0.1, 'BBB-': 0.1, 'BB+': 0.1, 'BB': 0.1, 'BB-': 0.1, 'B+': 0.1, 'B': 0.1, 'B-': 0.1}
    self.maturity_mean = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0, 15: 0, 16: 0, 17: 0, 18: 0, 19: 0, 20: 0, 21: 0, 22: 0, 23: 0, 24: 0, 25: 0, 26: 0, 27: 0, 28: 0, 29: 0, 30: 0}
    self.maturity_vol = {1: 0.1, 2: 0.1, 3: 0.1, 4: 0.1, 5: 0.1, 6: 0.1, 7: 0.1, 8: 0.1, 9: 0.1, 10: 0.001, 11: 0.1, 12: 0.1, 13: 0.1, 14: 0.1, 15: 0.1, 16: 0.1, 17: 0.1, 18: 0.1, 19: 0.1, 20: 0.1, 21: 0.1, 22: 0.1, 23: 0.1, 24: 0.1, 25: 0.1, 26: 0.1, 27: 0.1, 28: 0.1, 29: 0.1, 30: 0.1}
    self.liquidity_mean = {1: 5, 2: 4, 3: 3, 4: 1, 5: 0}
    self.liquidity_vol = {1: 0.1, 2: 0.1, 3: 0.001, 4: 0.1, 5: 0.1}
    self.lot_size_mean = {100000: 5, 1000000: 2, 5000000: 1, 10000000: 0}
    self.lot_size_vol = {100000: 0.001, 1000000: 0.1, 5000000: 0.1, 10000000: 0.1}

    # Random Noise to Total TC
    self.random_noise = np.random.normal(0, 0.001)


    # Correlation matrix that is required to generate correlated stochastic processes
    self.corr_mat = [[1.        , 0.10613038, 0.06720876, 0.0723708 , 0.07090028],
       [0.10613038, 1.        , 0.1690226 , 0.08636133, 0.08066976],
       [0.06720876, 0.1690226 , 1.        , 0.06547732, 0.04201025],
       [0.0723708 , 0.08636133, 0.06547732, 1.        , 0.060396  ],
       [0.07090028, 0.08066976, 0.04201025, 0.060396  , 1.        ]]


  # Creating correlated Wiener Processes for Ornstein-Uhlenbeck via Cholesky Decomposition
  def _correlated_dW(self):
    dW_independent = np.random.normal(0, 1, size=(10, 5)) * np.sqrt(self.timestep)
    L = np.linalg.cholesky(self.corr_mat)
    dW_correlated = dW_independent @ L.T
    return dW_correlated

  # Defining method to create base OU process. Making timestep = 1 for now
  def _base_ou_process(self, mean, volatility, reversion_speed, n_days, timestep):
    base_TC = np.zeros(n_days)
    base_TC[0] = np.random.normal(mean, volatility, 1)
    dW = self._correlated_dW()[:, 0]
    for i in range(1, n_days):
      #dW = np.random.normal(0, 1) * np.sqrt(timestep)
      base_TC[i] = max(base_TC[i-1] + reversion_speed * (mean - base_TC[i-1]) * timestep + volatility * dW[i], 0)

    return base_TC


  # Instead of of creating multiple methods for each sector, try to create a single method that takes sector as an input and accesses the mean/vol dictionaries
  def _sector_ou_process(self, sector, reversion_speed, n_days, timestep):
    sector_mean = self.sectors_mean[sector]
    sector_vol = self.sectors_vol[sector]
    sector_TC = np.zeros(n_days)
    sector_TC[0] = max(np.random.normal(sector_mean, sector_vol, 1), 0)
    dW = self._correlated_dW()[:, 1]
    for i in range(1, n_days):
      #dW = np.random.normal(0, 1) * np.sqrt(timestep)
      sector_TC[i] = max(sector_TC[i-1] + reversion_speed * (sector_mean - sector_TC[i-1]) * timestep + sector_vol * dW[i], 0)

    return sector_TC

  # Instead of of creating multiple methods for each rating, try to create a single method that takes rating as an input and accesses the mean/vol dictionaries
  def _ratings_ou_process(self, rating, reversion_speed, n_days, timestep):
    rating_mean = self.ratings_mean[rating]
    rating_vol = self.ratings_vol[rating]
    rating_TC = np.zeros(n_days)
    rating_TC[0] = max(np.random.normal(rating_mean, rating_vol, 1), 0)
    dW = self._correlated_dW()[:, 2]
    for i in range(1, n_days):
      #dW = np.random.normal(0, 1) * np.sqrt(timestep)
      rating_TC[i] = max(rating_TC[i-1] + reversion_speed * (rating_mean - rating_TC[i-1]) * timestep + rating_vol * dW[i], 0)

    return rating_TC

  # Instead of of creating multiple methods for each maturity, try to create a single method that takes maturity as an input and accesses the mean/vol dictionaries
  def _maturity_ou_process(self, maturity, reversion_speed, n_days, timestep):
    maturity_mean = self.maturity_mean[maturity]
    maturity_vol = self.maturity_vol[maturity]
    maturity_TC = np.zeros(n_days)
    maturity_TC[0] = max(np.random.normal(maturity_mean, maturity_vol, 1), 0)
    dW = self._correlated_dW()[:, 3]
    for i in range(1, n_days):
      #dW = np.random.normal(0, 1) * np.sqrt(timestep)
      maturity_TC[i] = max(maturity_TC[i-1] + reversion_speed * (maturity_mean - maturity_TC[i-1]) * timestep + maturity_vol * dW[i], 0)

    return maturity_TC

  # Instead of of creating multiple methods for each liqudity score, try to create a single method that takes liqudity score as an input and accesses the mean/vol dictionaries
  def _liquidity_ou_process(self, liquidity, reversion_speed, n_days, timestep):
    liqudity_mean = self.liquidity_mean[liquidity]
    liquidity_vol = self.liquidity_mean[liquidity]
    liqudity_TC = np.zeros(n_days)
    liqudity_TC[0] = max(np.random.normal(liqudity_mean, liquidity_vol, 1), 0)
    dW = self._correlated_dW()[:, 4]
    for i in range(1, n_days):
      #dW = np.random.normal(0, 1) * np.sqrt(timestep)
      liqudity_TC[i] = max(liqudity_TC[i-1] + reversion_speed * (liqudity_mean - liqudity_TC[i-1]) * timestep + liquidity_vol * dW[i], 0)

    return liqudity_TC

  # Instead of of creating multiple methods for each lot size, try to create a single method that takes lot size as an input and accesses the mean/vol dictionaries
  def _lotsize_ou_process(self, lotsize, reversion_speed, n_days, timestep):
    lotsize_mean = self.lot_size_mean[lotsize]
    lotsize_vol = self.lot_size_vol[lotsize]
    lotsize_TC = np.zeros(n_days)
    lotsize_TC[0] = max(np.random.normal(lotsize_mean, lotsize_vol, 1), 0)
    dW = self._correlated_dW()[:, 0]
    for i in range(1, n_days):
      #dW = np.random.normal(0, 1) * np.sqrt(timestep)
      lotsize_TC[i] = max(lotsize_TC[i-1] + reversion_speed * (lotsize_mean - lotsize_TC[i-1]) * timestep + lotsize_vol * dW[i], 0)

    return lotsize_TC


  def generate_transaction_costs(self):
    results = np.zeros((self.num_paths, self.n_days))
    for i in range(self.num_paths):
      base_tc_component = self._base_ou_process(mean=self.base_mean,
                                            volatility=self.base_vol,
                                            reversion_speed=self.mean_reversion_speed,
                                            n_days=self.n_days, timestep=self.timestep)

      sector_tc_component = self._sector_ou_process(sector=self.sector_choice,
                                                    reversion_speed=self.mean_reversion_speed,
                                                    n_days=self.n_days,
                                                    timestep=self.timestep)

      ratings_tc_component = self._ratings_ou_process(rating=self.ratings_choice,
                                                      reversion_speed=self.mean_reversion_speed,
                                                      n_days=self.n_days,
                                                      timestep=self.timestep)

      maturity_tc_component = self._maturity_ou_process(maturity=self.maturity_choice,
                                                        reversion_speed=self.mean_reversion_speed,
                                                        n_days=self.n_days,
                                                        timestep=self.timestep)

      liquidity_tc_component = self._liquidity_ou_process(liquidity=self.liquidity_choice,
                                                        reversion_speed=self.mean_reversion_speed,
                                                        n_days=self.n_days,
                                                        timestep=self.timestep)

      lotsize_tc_component = self._lotsize_ou_process(lotsize=self.lotsize_choice,
                                                      reversion_speed=self.mean_reversion_speed,
                                                      n_days=self.n_days,
                                                      timestep=self.timestep)

      total_tc = np.array([base_tc_component +
                  sector_tc_component +
                  ratings_tc_component +
                  maturity_tc_component +
                  liquidity_tc_component +
                  lotsize_tc_component +
                  self.random_noise])

      total_tc.reshape(1, self.n_days)

      results[i, :] = total_tc

    results = pd.DataFrame(results)

    return results

  def total_tc_statistics(self, df):
    df = df.T
    return df.describe(), df.plot()
