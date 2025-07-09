#!/usr/bin/env python3
"""
ALERT RESULTS TRACKER
Tracks outcomes of 3OU half-time alerts to measure betting success rate
"""

import json
import os
import time
from datetime import datetime, timedelta
import pytz

class AlertResultsTracker:
    def __init__(self):
        self.results_file = "alert_results_tracking.json"
        self.alert_log_file = "alert_3ou_half.json"
        self.monitor_data_file = "../6_monitor_central/monitor_central.json"
        
    def extract_alerted_matches(self):
        """Extract all matches that triggered alerts from alert log"""
        try:
            with open(self.alert_log_file, 'r') as f:
                content = f.read()
                
            alerted_matches = []
            
            # Parse bookended format
            fetch_sections = content.split('=== FETCH START:')
            for section in fetch_sections[1:]:
                try:
                    # Extract timestamp from header
                    header_line = section.split('\n')[0]
                    fetch_id = header_line.split(' | ')[0].strip()
                    alert_timestamp = header_line.split(' | ')[1].strip()
                    
                    # Find JSON content
                    json_start = section.find('\n{')
                    json_end = section.find('\n=== FETCH END:')
                    
                    if json_start != -1 and json_end != -1:
                        json_content = section[json_start:json_end].strip()
                        
                        # Handle multiple JSON objects
                        json_objects = json_content.split('}\n{')
                        
                        for i, json_obj in enumerate(json_objects):
                            if i > 0:
                                json_obj = '{' + json_obj
                            if i < len(json_objects) - 1:
                                json_obj = json_obj + '}'
                            
                            try:
                                match_data = json.loads(json_obj)
                                
                                # Create tracking entry
                                tracking_entry = {
                                    "match_id": match_data["match_info"]["match_id"],
                                    "home_team": match_data["match_info"]["home_team"],
                                    "away_team": match_data["match_info"]["away_team"],
                                    "competition": match_data["match_info"]["competition_name"],
                                    "ou_total": match_data["odds"]["O/U"][0]["Total"],
                                    "alert_timestamp": alert_timestamp,
                                    "fetch_id": fetch_id,
                                    "status": "PENDING",  # PENDING, WON, LOST, MONITORING
                                    "final_score": None,
                                    "goals_scored": None,
                                    "outcome": None,  # WIN/LOSS based on whether any goals scored
                                    "last_checked": None,
                                    "match_ended": False
                                }
                                
                                alerted_matches.append(tracking_entry)
                                
                            except json.JSONDecodeError:
                                continue
                                
                except Exception as e:
                    print(f"Error parsing section: {e}")
                    continue
                    
            return alerted_matches
            
        except FileNotFoundError:
            print("No alert log file found")
            return []
            
    def load_existing_results(self):
        """Load existing results tracking data"""
        try:
            with open(self.results_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"tracked_matches": [], "summary": {"total_alerts": 0, "wins": 0, "losses": 0, "pending": 0, "win_rate": 0.0}}
            
    def save_results(self, results_data):
        """Save results tracking data"""
        with open(self.results_file, 'w') as f:
            json.dump(results_data, f, indent=2)
            
    def find_match_outcome(self, match_id):
        """Find the final outcome of a match from monitor_central.json"""
        try:
            with open(self.monitor_data_file, 'r') as f:
                content = f.read()
                
            # Look for the match ID in monitor data
            fetch_sections = content.split('=== FETCH START:')
            
            for section in fetch_sections[1:]:
                try:
                    json_start = section.find('\n{')
                    json_end = section.find('\n=== FETCH END:')
                    
                    if json_start != -1 and json_end != -1:
                        json_content = section[json_start:json_end].strip()
                        monitor_data = json.loads(json_content)
                        
                        # Search through matches
                        for match in monitor_data.get("monitor_central_display", []):
                            if match.get("match_info", {}).get("match_id") == match_id:
                                status = match.get("match_info", {}).get("status", "")
                                live_score = match.get("match_info", {}).get("live_score", "")
                                
                                # Check if match ended
                                if "Status ID: 8" in status:  # Match ended
                                    return {
                                        "match_ended": True,
                                        "final_score": live_score,
                                        "status": status
                                    }
                                else:
                                    return {
                                        "match_ended": False,
                                        "current_score": live_score,
                                        "status": status
                                    }
                                    
                except json.JSONDecodeError:
                    continue
                    
            return None
            
        except FileNotFoundError:
            print("Monitor data file not found")
            return None
            
    def analyze_score(self, score_text):
        """Analyze final score to determine if any goals were scored"""
        if not score_text:
            return None
            
        # Extract score from text like "Live Score: 2-1 (HT: 0-0)"
        try:
            if "Live Score:" in score_text:
                score_part = score_text.split("Live Score:")[1].split("(")[0].strip()
                home_goals, away_goals = map(int, score_part.split("-"))
                total_goals = home_goals + away_goals
                
                return {
                    "home_goals": home_goals,
                    "away_goals": away_goals,
                    "total_goals": total_goals,
                    "any_goals_scored": total_goals > 0
                }
        except:
            pass
            
        return None
        
    def update_tracking_results(self):
        """Update results for all tracked matches"""
        # Load existing data
        results_data = self.load_existing_results()
        
        # Get new alerts
        new_alerts = self.extract_alerted_matches()
        
        # Add new alerts to tracking (avoid duplicates)
        existing_match_ids = [match["match_id"] for match in results_data["tracked_matches"]]
        
        for alert in new_alerts:
            if alert["match_id"] not in existing_match_ids:
                results_data["tracked_matches"].append(alert)
                print(f"📝 NEW ALERT ADDED: {alert['home_team']} vs {alert['away_team']}")
                
        # Update outcomes for pending/monitoring matches
        for match in results_data["tracked_matches"]:
            if match["status"] in ["PENDING", "MONITORING"]:
                outcome = self.find_match_outcome(match["match_id"])
                
                if outcome:
                    nyc_tz = pytz.timezone('America/New_York')
                    check_time = datetime.now(nyc_tz).strftime("%m/%d/%Y %I:%M:%S %p %Z")
                    match["last_checked"] = check_time
                    
                    if outcome["match_ended"]:
                        # Match ended - determine final result
                        match["match_ended"] = True
                        match["final_score"] = outcome["final_score"]
                        
                        score_analysis = self.analyze_score(outcome["final_score"])
                        if score_analysis:
                            match["goals_scored"] = score_analysis["total_goals"]
                            match["outcome"] = "WIN" if score_analysis["any_goals_scored"] else "LOSS"
                            match["status"] = "WON" if score_analysis["any_goals_scored"] else "LOST"
                            
                            print(f"🏁 MATCH ENDED: {match['home_team']} vs {match['away_team']}")
                            print(f"   Final Score: {outcome['final_score']}")
                            print(f"   Result: {match['outcome']} ({match['goals_scored']} goals)")
                        else:
                            match["status"] = "LOST"  # Couldn't parse score
                    else:
                        # Match still ongoing
                        match["status"] = "MONITORING"
                        print(f"🔄 MONITORING: {match['home_team']} vs {match['away_team']} - {outcome.get('current_score', 'N/A')}")
                        
        # Update summary statistics
        total_alerts = len(results_data["tracked_matches"])
        wins = len([m for m in results_data["tracked_matches"] if m["status"] == "WON"])
        losses = len([m for m in results_data["tracked_matches"] if m["status"] == "LOST"])
        pending = len([m for m in results_data["tracked_matches"] if m["status"] in ["PENDING", "MONITORING"]])
        
        win_rate = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0.0
        
        results_data["summary"] = {
            "total_alerts": total_alerts,
            "wins": wins,
            "losses": losses,
            "pending": pending,
            "win_rate": round(win_rate, 2),
            "last_updated": datetime.now(pytz.timezone('America/New_York')).strftime("%m/%d/%Y %I:%M:%S %p %Z")
        }
        
        # Save updated data
        self.save_results(results_data)
        
        return results_data
        
    def print_summary(self, results_data):
        """Print a summary of alert performance"""
        summary = results_data["summary"]
        
        print("\n" + "=" * 60)
        print("📊 ALERT PERFORMANCE SUMMARY")
        print("=" * 60)
        print(f"📈 Total Alerts: {summary['total_alerts']}")
        print(f"✅ Wins: {summary['wins']}")
        print(f"❌ Losses: {summary['losses']}")
        print(f"⏳ Pending: {summary['pending']}")
        print(f"🎯 Win Rate: {summary['win_rate']}%")
        print(f"🕐 Last Updated: {summary['last_updated']}")
        
        if summary['total_alerts'] > 0:
            print("\n📋 RECENT MATCHES:")
            for match in results_data["tracked_matches"][-5:]:  # Show last 5
                status_emoji = {"WON": "✅", "LOST": "❌", "PENDING": "⏳", "MONITORING": "🔄"}
                emoji = status_emoji.get(match["status"], "❓")
                print(f"  {emoji} {match['home_team']} vs {match['away_team']} - {match['status']}")
                
def main():
    tracker = AlertResultsTracker()
    
    print("🚀 ALERT RESULTS TRACKER")
    print("=" * 40)
    
    # Update tracking results
    results = tracker.update_tracking_results()
    
    # Print summary
    tracker.print_summary(results)
    
    print(f"\n📁 Results saved to: {tracker.results_file}")

if __name__ == "__main__":
    main()