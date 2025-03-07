import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from src.database.db_manager import DatabaseManager

class MarketAnalyzer:
    def __init__(self):
        self.db = DatabaseManager()
        self.scaler = StandardScaler()
        self.model = self._build_model()
        
    def _build_model(self) -> Sequential:
        """Build LSTM model for market prediction"""
        model = Sequential([
            LSTM(100, return_sequences=True, input_shape=(100, 50)),
            Dropout(0.2),
            LSTM(50),
            Dropout(0.2),
            Dense(1, activation='tanh')  # Output between -1 and 1 for market direction
        ])
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        return model

    def analyze_market(self, symbol: str) -> Dict:
        """Analyze market conditions and predict direction"""
        # Get historical data
        data = self.db.get_market_data(symbol)
        
        # Calculate technical indicators
        features = self._calculate_features(data)
        
        # Make prediction
        prediction = self._predict_market_direction(features)
        
        return {
            'symbol': symbol,
            'direction': prediction['direction'],
            'confidence': prediction['confidence'],
            'suggested_entry': prediction['entry_price'],
            'suggested_leverage': prediction['leverage']
        }

    def _calculate_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators and features"""
        df = data.copy()
        
        # Add technical indicators
        df['rsi'] = self._calculate_rsi(df['close'])
        df['macd'] = self._calculate_macd(df['close'])
        df['bb_upper'], df['bb_lower'] = self._calculate_bollinger_bands(df['close'])
        df['volume_sma'] = df['volume'].rolling(20).mean()
        
        return df

    def _predict_market_direction(self, features: pd.DataFrame) -> Dict:
        """Predict market direction and generate trading signals"""
        # Prepare features for prediction
        scaled_features = self.scaler.fit_transform(features)
        
        # Make prediction
        prediction = self.model.predict(scaled_features[-100:].reshape(1, 100, -1))
        
        confidence = abs(prediction[0][0])
        direction = 'long' if prediction[0][0] > 0 else 'short'
        
        return {
            'direction': direction,
            'confidence': float(confidence),
            'entry_price': self._calculate_entry_price(features, direction),
            'leverage': self._calculate_optimal_leverage(confidence)
        }