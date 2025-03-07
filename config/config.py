from typing import Dict, List
import os
from datetime import datetime

class Config:
    # API Configuration
    API_KEY = os.getenv('KUCOIN_API_KEY')
    API_SECRET = os.getenv('KUCOIN_API_SECRET')
    API_PASSPHRASE = os.getenv('KUCOIN_API_PASSPHRASE')
    
    # Database Configuration
    DB_PATH = 'data/historical_data.db'
    
    # Trading Parameters (initial values, will be adjusted by AI)
    INITIAL_RISK_PERCENTAGE = 2.0  # Start with 2% risk per trade
    MAX_DRAWDOWN = 15.0  # Maximum drawdown percentage
    LEVERAGE_RANGE = (1, 20)  # Min and max leverage
    
    # Market Analysis
    TIMEFRAMES = ['1min', '5min', '15min', '1hour', '4hour', '1day']
    MIN_VOLUME_USD = 1000000  # Minimum 24h volume in USD
    HISTORICAL_DATA_DAYS = 90  # Days of historical data to maintain
    
    # Position Management
    MAX_POSITIONS = 5  # Maximum concurrent positions
    POSITION_SIZING_METHOD = 'risk_parity'  # Options: 'equal', 'risk_parity', 'kelly'
    
    # AI Model Parameters
    MODEL_UPDATE_INTERVAL = 24  # Hours between model updates
    MIN_TRAINING_SAMPLES = 1000
    FEATURE_WINDOWS = [14, 30, 50, 200]  # Different lookback periods