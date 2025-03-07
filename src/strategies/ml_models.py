import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
import tensorflow as tf
from typing import Tuple, List

class MarketPredictionModel:
    def __init__(self, input_shape: Tuple[int, int]):
        self.model = self._build_model(input_shape)
        self.scaler = StandardScaler()
        
    def _build_model(self, input_shape: Tuple[int, int]) -> Sequential:
        """Build and compile the LSTM model"""
        model = Sequential([
            LSTM(128, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(64, return_sequences=True),
            Dropout(0.2),
            LSTM(32),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(1, activation='tanh')  # Output between -1 and 1
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def prepare_data(self, data: pd.DataFrame, 
                    sequence_length: int) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for training or prediction"""
        # Calculate features
        features = self._calculate_features(data)
        
        # Scale features
        scaled_features = self.scaler.fit_transform(features)
        
        # Create sequences
        X, y = [], []
        for i in range(len(scaled_features) - sequence_length):
            X.append(scaled_features[i:(i + sequence_length)])
            y.append(scaled_features[i + sequence_length, 0])  # Predict next price
            
        return np.array(X), np.array(y)
    
    def _calculate_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators and features"""
        df = data.copy()
        
        # Price features
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close']).diff()
        
        # Volume features
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_std'] = df['volume'].rolling(window=20).std()
        
        # Technical indicators
        df['rsi'] = self._calculate_rsi(df['close'])
        df['macd'] = self._calculate_macd(df['close'])
        df['bb_upper'], df['bb_lower'] = self._calculate_bollinger_bands(df['close'])
        
        # Volatility
        df['volatility'] = df['returns'].rolling(window=20).std()
        
        # Remove NaN values
        df = df.dropna()
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_macd(self, prices: pd.Series) -> pd.Series:
        """Calculate MACD"""
        exp1 = prices.ewm(span=12, adjust=False).mean()
        exp2 = prices.ewm(span=26, adjust=False).mean()
        return exp1 - exp2
    
    def _calculate_bollinger_bands(self, prices: pd.Series, 
                                 period: int = 20) -> Tuple[pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        ma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper_band = ma + (std * 2)
        lower_band = ma - (std * 2)
        
        return upper_band, lower_band
    
    def train(self, X: np.ndarray, y: np.ndarray, 
             validation_split: float = 0.2,
             epochs: int = 100,
             batch_size: int = 32) -> tf.keras.callbacks.History:
        """Train the model"""
        return self.model.fit(
            X, y,
            validation_split=validation_split,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[
                tf.keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=10,
                    restore_best_weights=True
                )
            ]
        )
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        return self.model.predict(X)