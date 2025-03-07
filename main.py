import asyncio
import logging
from datetime import datetime
from src.api.kucoin_client import KuCoinClient
from src.models.market_analyzer import MarketAnalyzer
from src.models.position_manager import PositionManager
from src.models.risk_manager import RiskManager
from src.database.db_manager import DatabaseManager
from config.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradingBot:
    def __init__(self):
        self.kucoin = KuCoinClient()
        self.analyzer = MarketAnalyzer()
        self.position_manager = PositionManager()
        self.risk_manager = RiskManager()
        self.db = DatabaseManager()
        
    async def run(self):
        """Main bot loop"""
        while True:
            try:
                # Get active trading symbols
                symbols = self.kucoin.get_active_symbols()
                
                # Get account balance
                balance = self.kucoin.get_account_balance()
                
                for symbol in symbols:
                    # Analyze market
                    analysis = self.analyzer.analyze_market(symbol)
                    
                    # Get current positions
                    positions = self.position_manager.get_positions(symbol)
                    
                    if positions:
                        # Manage existing positions
                        self.position_manager.manage_positions(
                            positions, analysis, self.risk_manager
                        )
                    else:
                        # Check for new trading opportunities
                        if analysis['confidence'] > 0.7:  # High confidence threshold
                            # Calculate position size
                            size = self.risk_manager.calculate_position_size(
                                balance, analysis, positions
                            )
                            
                            # Place order
                            if size > 0:
                                try:
                                    order = self.kucoin.place_order(
                                        symbol=symbol,
                                        side=analysis['direction'],
                                        leverage=analysis['suggested_leverage'],
                                        size=size,
                                        price=analysis['suggested_entry']
                                    )
                                    
                                    logger.info(f"New order placed: {order}")
                                    
                                except Exception as e:
                                    logger.error(f"Error placing order: {e}")
                
                # Update models and clean old data
                await self.maintenance_tasks()
                
                # Wait before next iteration
                await asyncio.sleep(60)  # 1-minute intervals
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(60)
    
    async def maintenance_tasks(self):
        """Perform periodic maintenance tasks"""
        try:
            # Clean old market data
            self.db.clean_old_data()
            
            # Update AI models if needed
            current_time = int(datetime.now().timestamp())
            last_update = self.analyzer.get_last_update_time()
            
            if (current_time - last_update) > (Config.MODEL_UPDATE_INTERVAL * 3600):
                await self.analyzer.update_models()
                
        except Exception as e:
            logger.error(f"Error in maintenance tasks: {e}")

if __name__ == "__main__":
    bot = TradingBot()
