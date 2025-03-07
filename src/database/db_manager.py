import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from config.config import Config

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(Config.DB_PATH)
        self.create_tables()
        
    def create_tables(self):
        """Create necessary database tables"""
        with self.conn:
            # Market data table
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS market_data (
                    timestamp INTEGER,
                    symbol TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    PRIMARY KEY (timestamp, symbol)
                )
            ''')
            
            # Trades table
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER,
                    symbol TEXT,
                    side TEXT,
                    entry_price REAL,
                    exit_price REAL,
                    size REAL,
                    pnl REAL,
                    strategy TEXT
                )
            ''')
            
            # Model performance table
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS model_performance (
                    timestamp INTEGER,
                    model_name TEXT,
                    accuracy REAL,
                    sharpe_ratio REAL,
                    max_drawdown REAL,
                    PRIMARY KEY (timestamp, model_name)
                )
            ''')

    def store_market_data(self, data: pd.DataFrame, symbol: str):
        """Store market data in database"""
        data['symbol'] = symbol
        data.to_sql('market_data', self.conn, if_exists='append', index=False)

    def get_market_data(self, symbol: str, 
                       start_time: datetime = None,
                       end_time: datetime = None) -> pd.DataFrame:
        """Retrieve market data for analysis"""
        query = "SELECT * FROM market_data WHERE symbol = ?"
        params = [symbol]
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(int(start_time.timestamp()))
        if end_time:
            query += " AND timestamp <= ?"
            params.append(int(end_time.timestamp()))
            
        query += " ORDER BY timestamp"
        
        return pd.read_sql_query(query, self.conn, params=params)

    def store_trade(self, trade_data: Dict):
        """Store completed trade information"""
        with self.conn:
            self.conn.execute('''
                INSERT INTO trades (
                    timestamp, symbol, side, entry_price, 
                    exit_price, size, pnl, strategy
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                int(datetime.now().timestamp()),
                trade_data['symbol'],
                trade_data['side'],
                trade_data['entry_price'],
                trade_data['exit_price'],
                trade_data['size'],
                trade_data['pnl'],
                trade_data['strategy']
            ))

    def clean_old_data(self):
        """Remove old market data to manage database size"""
        cutoff_time = int((datetime.now() - 
                          timedelta(days=Config.HISTORICAL_DATA_DAYS)).timestamp())
        
        with self.conn:
            self.conn.execute(
                "DELETE FROM market_data WHERE timestamp < ?",
                (cutoff_time,)
            )