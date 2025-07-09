#!/usr/bin/env python3
"""
DATABASE-STYLE ALERT TRACKING
Creates a structured database-like system for tracking alert outcomes
"""

import json
import sqlite3
from datetime import datetime
import pytz

class AlertDatabase:
    def __init__(self, db_path="alert_tracking.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database for alert tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id TEXT UNIQUE,
                home_team TEXT,
                away_team TEXT,
                competition TEXT,
                ou_total REAL,
                alert_timestamp TEXT,
                fetch_id TEXT,
                status TEXT DEFAULT 'PENDING',
                final_score TEXT,
                goals_scored INTEGER,
                outcome TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def add_alert(self, match_data, fetch_id, timestamp):
        """Add new alert to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO alerts (match_id, home_team, away_team, competition, ou_total, alert_timestamp, fetch_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                match_data["match_info"]["match_id"],
                match_data["match_info"]["home_team"],
                match_data["match_info"]["away_team"],
                match_data["match_info"]["competition_name"],
                match_data["odds"]["O/U"][0]["Total"],
                timestamp,
                fetch_id
            ))
            
            conn.commit()
            print(f"📝 ALERT ADDED TO DATABASE: {match_data['match_info']['home_team']} vs {match_data['match_info']['away_team']}")
            
        except sqlite3.IntegrityError:
            print(f"⚠️ Alert already exists for match: {match_data['match_info']['match_id']}")
            
        finally:
            conn.close()
            
    def update_outcome(self, match_id, final_score, goals_scored, outcome):
        """Update match outcome in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE alerts 
            SET final_score = ?, goals_scored = ?, outcome = ?, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE match_id = ?
        ''', (final_score, goals_scored, outcome, 'COMPLETED', match_id))
        
        conn.commit()
        conn.close()
        
    def get_summary(self):
        """Get performance summary"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_alerts,
                SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN outcome = 'LOSS' THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN status = 'PENDING' THEN 1 ELSE 0 END) as pending,
                ROUND(AVG(CASE WHEN outcome = 'WIN' THEN 1.0 ELSE 0.0 END) * 100, 2) as win_rate
            FROM alerts
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        return {
            "total_alerts": result[0],
            "wins": result[1],
            "losses": result[2],
            "pending": result[3],
            "win_rate": result[4] or 0.0
        }
        
    def get_pending_alerts(self):
        """Get all pending alerts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT match_id, home_team, away_team, alert_timestamp
            FROM alerts 
            WHERE status = 'PENDING'
            ORDER BY created_at DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return [{"match_id": r[0], "home_team": r[1], "away_team": r[2], "alert_timestamp": r[3]} for r in results]