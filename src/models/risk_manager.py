from typing import Dict
import numpy as np
from config.config import Config

class RiskManager:
    def __init__(self):
        self.max_drawdown = Config.MAX_DRAWDOWN
        self.position_history = []
        
    def calculate_position_size(self, 
                              account_balance: float, 
                              analysis: Dict,
                              current_positions: List[Dict]) -> float:
        """Calculate safe position size based on risk parameters"""
        
        # Calculate available margin
        total_margin_used = sum([pos['margin'] for pos in current_positions])
        available_balance = account_balance - total_margin_used
        
        # Adjust risk based on model confidence
        risk_percentage = self._dynamic_risk_adjustment(
            base_risk=Config.INITIAL_RISK_PERCENTAGE,
            confidence=analysis['confidence'],
            market_volatility=self._calculate_market_volatility()
        )
        
        # Calculate position size
        position_size = (available_balance * risk_percentage / 100)
        
        # Apply Kelly Criterion
        kelly_fraction = self._calculate_kelly_fraction()
        position_size *= kelly_fraction
        
        return position_size

    def _dynamic_risk_adjustment(self, 
                               base_risk: float, 
                               confidence: float,
                               market_volatility: float) -> float:
        """Dynamically adjust risk based on market conditions"""
        # Reduce risk in high volatility
        volatility_factor = 1 - (market_volatility / 100)
        
        # Increase risk with higher confidence
        confidence_factor = confidence
        
        # Consider recent performance
        performance_factor = self._calculate_performance_factor()
        
        adjusted_risk = base_risk * volatility_factor * confidence_factor * performance_factor
        
        # Ensure risk stays within reasonable bounds
        return max(0.5, min(adjusted_risk, 5.0))

    def _calculate_kelly_fraction(self) -> float:
        """Calculate Kelly Criterion fraction"""
        if not self.position_history:
            return 0.5  # Conservative default
            
        wins = sum(1 for pos in self.position_history if pos['pnl'] > 0)
        total_trades = len(self.position_history)
        
        if total_trades == 0:
            return 0.5
            
        win_rate = wins / total_trades
        
        # Calculate average win/loss ratio
        avg_win = np.mean([pos['pnl'] for pos in self.position_history if pos['pnl'] > 0])
        avg_loss = abs(np.mean([pos['pnl'] for pos in self.position_history if pos['pnl'] < 0]))
        
        if avg_loss == 0:
            return 0.5
            
        win_loss_ratio = avg_win / avg_loss
        
        # Kelly Fraction formula
        kelly = win_rate - ((1 - win_rate) / win_loss_ratio)
        
        # Limit kelly fraction to avoid excessive risk
        return max(0, min(kelly, 0.5))