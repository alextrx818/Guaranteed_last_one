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
        self.results_file = "alert_3ou_half_results.json"
        self.markdown_file = "alert_3ou_half_results.md"
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
        
        # Generate markdown report
        self.generate_markdown_report(results_data)
        
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
    
    def generate_markdown_report(self, results_data):
        """Generate markdown report with table view"""
        summary = results_data["summary"]
        
        markdown_content = f"""# 3OU Half Alert Results Report

## Summary Statistics
- **Total Alerts**: {summary['total_alerts']}
- **Wins**: {summary['wins']}
- **Losses**: {summary['losses']}
- **Pending**: {summary['pending']}
- **Win Rate**: {summary['win_rate']}%
- **Last Updated**: {summary['last_updated']}

## Match Results Table

| Date | Home Team | Away Team | Competition | Line | HT Score | Status | Final Score | Outcome |
|------|-----------|-----------|-------------|------|----------|---------|-------------|---------|
"""
        
        # Add table rows
        for match in results_data["tracked_matches"]:
            # Format date from timestamp
            try:
                date_str = match['alert_timestamp'].split()[0]
            except:
                date_str = "N/A"
            
            # Format values
            home_team = match.get('home_team', 'N/A')
            away_team = match.get('away_team', 'N/A') 
            competition = match.get('competition', 'N/A')
            ou_total = match.get('ou_total', 'N/A')
            
            # Extract line info (odds)
            line_info = f"O/U {ou_total}" if ou_total != 'N/A' else 'N/A'
            
            # Extract half time score from final score
            ht_score = "0-0"  # Default since alerts only trigger on 0-0 HT
            final_score = match.get('final_score', 'N/A')
            if final_score != 'N/A' and "(HT:" in final_score:
                try:
                    ht_part = final_score.split("(HT:")[1].split(")")[0].strip()
                    ht_score = ht_part
                except:
                    ht_score = "0-0"
            
            status = match.get('status', 'N/A')
            goals_scored = match.get('goals_scored', 'N/A')
            outcome = match.get('outcome', 'N/A')
            
            # Status emoji
            status_emoji = {"WON": "✅", "LOST": "❌", "PENDING": "⏳", "MONITORING": "🔄"}
            status_display = f"{status_emoji.get(status, '❓')} {status}"
            
            # Ensure consistent column widths
            date_str = date_str[:10].ljust(10)
            home_team = home_team[:15].ljust(15)
            away_team = away_team[:15].ljust(15)
            competition = competition[:12].ljust(12)
            line_info = line_info[:8].ljust(8)
            ht_score = ht_score.ljust(6)
            status_display = status_display[:12].ljust(12)
            final_score = final_score[:20].ljust(20)
            outcome = outcome.ljust(8)
            
            markdown_content += f"| {date_str} | {home_team} | {away_team} | {competition} | {line_info} | {ht_score} | {status_display} | {final_score} | {outcome} |\n"
        
        if not results_data["tracked_matches"]:
            markdown_content += "| No matches tracked yet".ljust(10) + " | " + " ".ljust(15) + " | " + " ".ljust(15) + " | " + " ".ljust(12) + " | " + " ".ljust(8) + " | " + " ".ljust(6) + " | " + " ".ljust(12) + " | " + " ".ljust(20) + " | " + " ".ljust(8) + " |\n"
        
        markdown_content += f"""
## WIN/LOSS Logic
- **WIN**: Any goals scored in match (1-0, 2-1, etc.)
- **LOSS**: Match ended 0-0 (no goals scored)

---
*Generated automatically by 3OU Half Alert System*
"""
        
        # Save markdown file
        with open(self.markdown_file, 'w') as f:
            f.write(markdown_content)
        
        print(f"📄 Markdown report saved to: {self.markdown_file}")
                
def main():
    tracker = AlertResultsTracker()
    
    print("🚀 ALERT RESULTS TRACKER")
    print("=" * 40)
    
    # Update tracking results
    results = tracker.update_tracking_results()
    
    # Print summary
    tracker.print_summary(results)
    
    print(f"\n📁 Results saved to: {tracker.results_file}")
    print(f"📄 Markdown report: {tracker.markdown_file}")

if __name__ == "__main__":
    main()