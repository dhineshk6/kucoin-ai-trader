# Continuing from previous main.py
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
    asyncio.run(bot.run())