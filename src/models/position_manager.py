from typing import List, Dict
import numpy as np
from datetime import datetime
import logging
from config.config import Config

logger = logging.getLogger(__name__)

class PositionManager:
    def __init__(self):
        self.open_positions = {}
        self.position_history = []
        
    def get_positions(self, symbol: str) -> List[Dict]:
        """Get current open positions for a symbol"""
        return self.open_positions.get(symbol, [])
        
    def manage_positions(self, positions: List[Dict], 
                        analysis: Dict, risk_manager) -> None:
        """Manage open positions based on market analysis"""
        for position in positions:
            try:
                # Calculate current PnL
                current_pnl = self._calculate_pnl(position, analysis['current_price'])
                
                # Check stop loss
                if self._should_stop_loss(position, current_pnl):
                    self._close_position(position, 'stop_loss')
                    continue
                
                # Check take profit
                if self._should_take_profit(position, current_pnl):
                    self._close_position(position, 'take_profit')
                    continue
                
                # Check for position adjustment
                if self._should_adjust_position(position, analysis):
                    self._adjust_position(position, analysis, risk_manager)
                    
            except Exception as e:
                logger.error(f"Error managing position {position['id']}: {e}")
    
    def _calculate_pnl(self, position: Dict, current_price: float) -> float:
        """Calculate current PnL for a position"""
        price_diff = current_price - position['entry_price']
        if position['side'] == 'short':
            price_diff = -price_diff
            
        return (price_diff / position['entry_price']) * position['size'] * position['leverage']
    
    def _should_stop_loss(self, position: Dict, current_pnl: float) -> bool:
        """Determine if stop loss should be triggered"""
        return current_pnl <= -position['stop_loss_pct']
    
    def _should_take_profit(self, position: Dict, current_pnl: float) -> bool:
        """Determine if take profit should be triggered"""
        return current_pnl >= position['take_profit_pct']
    
    def _should_adjust_position(self, position: Dict, analysis: Dict) -> bool:
        """Determine if position should be adjusted"""
        # Check if market direction has changed significantly
        if position['side'] == 'long' and analysis['direction'] == 'short':
            return analysis['confidence'] > 0.8
        elif position['side'] == 'short' and analysis['direction'] == 'long':
            return analysis['confidence'] > 0.8
            
        return False
    
    def _adjust_position(self, position: Dict, 
                        analysis: Dict, risk_manager) -> None:
        """Adjust position size or direction based on new analysis"""
        try:
            # Calculate new position size
            new_size = risk_manager.calculate_position_size(
                position['size'],
                analysis,
                self.open_positions.get(position['symbol'], [])
            )
            
            # Update position
            if new_size != position['size']:
                self._modify_position(position, new_size)
                
        except Exception as e:
            logger.error(f"Error adjusting position {position['id']}: {e}")
    
    def _close_position(self, position: Dict, reason: str) -> None:
        """Close an open position"""
        try:
            # Record position in history
            self.position_history.append({
                'symbol': position['symbol'],
                'side': position['side'],
                'entry_price': position['entry_price'],
                'exit_price': position['current_price'],
                'size': position['size'],
                'leverage': position['leverage'],
                'pnl': self._calculate_pnl(position, position['current_price']),
                'reason': reason,
                'duration': datetime.now().timestamp() - position['entry_time']
            })
            
            # Remove from open positions
            self.open_positions[position['symbol']] = [
                p for p in self.open_positions[position['symbol']]
                if p['id'] != position['id']
            ]
            
        except Exception as e:
            logger.error(f"Error closing position {position['id']}: {e}")