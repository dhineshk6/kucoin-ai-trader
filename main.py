import asyncio
import logging
import os
from datetime import datetime
import sys
from typing import List, Dict

# Set up basic logging immediately
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('trading_bot.log')
    ]
)

logger = logging.getLogger(__name__)

# Print immediate feedback
print("Starting Trading Bot...")
logger.info("Initializing trading bot components...")

try:
    from src.api.kucoin_client import KuCoinClient
    from src.models.market_analyzer import MarketAnalyzer
    from src.models.position_manager import PositionManager
    from src.models.risk_manager import RiskManager
    from src.database.db_manager import DatabaseManager
    from config.config import Config
    
    logger.info("Successfully imported all required modules")
except ImportError as e:
    logger.error(f"Failed to import required modules: {str(e)}")
    sys.exit(1)

class TradingBot:
    def __init__(self):
        logger.info("Initializing TradingBot instance...")
        try:
            self.kucoin = KuCoinClient()
            logger.info("KuCoin client initialized")
            
            self.analyzer = MarketAnalyzer()
            logger.info("Market analyzer initialized")
            
            self.position_manager = PositionManager()
            logger.info("Position manager initialized")
            
            self.risk_manager = RiskManager()
            logger.info("Risk manager initialized")
            
            self.db = DatabaseManager()
            logger.info("Database manager initialized")
            
        except Exception as e:
            logger.error(f"Initialization error: {str(e)}")
            raise

    async def get_market_data(self) -> List[Dict]:
        """Get market data with error handling"""
        try:
            symbols = await self.kucoin.get_active_symbols()
            logger.info(f"Found {len(symbols)} active symbols")
            return symbols
        except Exception as e:
            logger.error(f"Error getting market data: {str(e)}")
            return []

    async def run(self):
        """Main bot loop"""
        logger.info("Starting main bot loop...")
        
        while True:
            try:
                # Get active trading symbols
                symbols = await self.get_market_data()
                
                if not symbols:
                    logger.warning("No active symbols found, waiting before retry...")
                    await asyncio.sleep(60)
                    continue

                # Get account balance
                try:
                    balance = await self.kucoin.get_account_balance()
                    logger.info(f"Current account balance: {balance}")
                except Exception as e:
                    logger.error(f"Error getting account balance: {str(e)}")
                    await asyncio.sleep(60)
                    continue

                for symbol in symbols:
                    logger.info(f"Processing symbol: {symbol}")
                    try:
                        analysis = await self.analyzer.analyze_market(symbol)
                        positions = self.position_manager.get_positions(symbol)
                        
                        if positions:
                            logger.info(f"Managing existing positions for {symbol}")
                            await self.position_manager.manage_positions(
                                positions, analysis, self.risk_manager
                            )
                        elif analysis['confidence'] > 0.7:
                            logger.info(f"Found trading opportunity for {symbol}")
                            # Calculate position size and place order
                            size = self.risk_manager.calculate_position_size(
                                balance, analysis, positions
                            )
                            
                            if size > 0:
                                try:
                                    order = await self.kucoin.place_order(
                                        symbol=symbol,
                                        side=analysis['direction'],
                                        leverage=analysis['suggested_leverage'],
                                        size=size,
                                        price=analysis['suggested_entry']
                                    )
                                    logger.info(f"New order placed: {order}")
                                except Exception as e:
                                    logger.error(f"Error placing order: {str(e)}")

                    except Exception as e:
                        logger.error(f"Error processing symbol {symbol}: {str(e)}")
                        continue

                await self.maintenance_tasks()
                logger.info("Waiting for next iteration...")
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                await asyncio.sleep(60)

    async def maintenance_tasks(self):
        """Perform periodic maintenance tasks"""
        logger.info("Running maintenance tasks...")
        try:
            self.db.clean_old_data()
            current_time = int(datetime.now().timestamp())
            last_update = self.analyzer.get_last_update_time()
            
            if (current_time - last_update) > (Config.MODEL_UPDATE_INTERVAL * 3600):
                await self.analyzer.update_models()
                logger.info("Models updated successfully")
                
        except Exception as e:
            logger.error(f"Error in maintenance tasks: {str(e)}")

async def main():
    logger.info("Initializing main function...")
    try:
        bot = TradingBot()
        await bot.run()
    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        print("Starting bot execution...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
        logger.info("Bot stopped by user")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        logger.error(f"Unexpected error: {str(e)}")
