#!/usr/bin/env python3
"""
REALISTIC MOCK TEST - TIMED FETCHES WITH MIXED DATA
Simulates 5 realistic fetches with 10-second intervals, where only some contain qualifying matches
"""

import json
import time
import os
import sys
from datetime import datetime, timedelta
import pytz

def create_realistic_fetch_data(fetch_number, qualifying_match=False):
    """Create realistic monitor data for a specific fetch"""
    nyc_tz = pytz.timezone('America/New_York')
    
    # Create timestamp for this fetch (spaced 10 seconds apart)
    base_time = datetime.now(nyc_tz) - timedelta(seconds=(5-fetch_number) * 10)
    timestamp = base_time.strftime("%m/%d/%Y %I:%M:%S %p %Z")
    
    # Always include regular matches that don't qualify
    regular_matches = [
        {
            "timestamp": timestamp,
            "match_info": {
                "match_id": f"REGULAR_{fetch_number}_001",
                "competition_id": f"regular_comp_{fetch_number}",
                "competition_name": "Premier League",
                "home_team": "Manchester City",
                "away_team": "Arsenal",
                "status": "Status ID: 4 (Second half)",  # ❌ Not half-time
                "live_score": "Live Score: 1-0 (HT: 1-0)"  # ❌ Not 0-0
            },
            "corners": {"home": 4, "away": 2, "total": 6},
            "odds": {
                "O/U": [{"time_of_match": "4", "Over": "-110", "Total": 3.5, "Under": "-110"}],
                "MoneyLine": [{"time_of_match": "4", "Home": "-150", "Tie": "+300", "Away": "+400"}]
            },
            "environment": {"weather": "Clear", "pressure": "30.0 inHg", "temperature_f": "72 F", "wind": "5mph", "humidity": "50%"},
            "incidents": []
        },
        {
            "timestamp": timestamp,
            "match_info": {
                "match_id": f"REGULAR_{fetch_number}_002",
                "competition_id": f"regular_comp_{fetch_number}",
                "competition_name": "La Liga",
                "home_team": "Barcelona",
                "away_team": "Real Madrid",
                "status": "Status ID: 8 (End)",  # ❌ Match ended
                "live_score": "Live Score: 2-1 (HT: 1-1)"
            },
            "corners": {"home": 6, "away": 4, "total": 10},
            "odds": {
                "O/U": [{"time_of_match": "8", "Over": "-105", "Total": 2.5, "Under": "-115"}],
                "MoneyLine": [{"time_of_match": "8", "Home": "+180", "Tie": "+220", "Away": "+160"}]
            },
            "environment": {"weather": "Sunny", "pressure": "29.8 inHg", "temperature_f": "75 F", "wind": "8mph", "humidity": "45%"},
            "incidents": []
        },
        {
            "timestamp": timestamp,
            "match_info": {
                "match_id": f"REGULAR_{fetch_number}_003",
                "competition_id": f"regular_comp_{fetch_number}",
                "competition_name": "Serie A",
                "home_team": "Juventus",
                "away_team": "AC Milan",
                "status": "Status ID: 3 (Half-time)",  # ✅ Half-time
                "live_score": "Live Score: 0-0 (HT: 0-0)"  # ✅ 0-0 score
            },
            "corners": {"home": 2, "away": 1, "total": 3},
            "odds": {
                "O/U": [{"time_of_match": "3", "Over": "-120", "Total": 2.5, "Under": "+100"}],  # ❌ Total < 3.0
                "MoneyLine": [{"time_of_match": "3", "Home": "+140", "Tie": "+200", "Away": "+180"}]
            },
            "environment": {"weather": "Partly Cloudy", "pressure": "29.9 inHg", "temperature_f": "68 F", "wind": "10mph", "humidity": "60%"},
            "incidents": []
        }
    ]
    
    all_matches = regular_matches.copy()
    matches_in_play = len([m for m in all_matches if "Status ID: 2" in m["match_info"]["status"] or "Status ID: 3" in m["match_info"]["status"] or "Status ID: 4" in m["match_info"]["status"]])
    
    # Add qualifying match only if specified
    if qualifying_match:
        qualifying_match_data = {
            "timestamp": timestamp,
            "match_info": {
                "match_id": f"QUALIFYING_{fetch_number}_SPECIAL",
                "competition_id": f"qualifying_comp_{fetch_number}",
                "competition_name": f"🚨 FETCH #{fetch_number} - QUALIFYING MATCH DETECTED",
                "home_team": f"Alert Test FC #{fetch_number}",
                "away_team": f"Telegram United #{fetch_number}",
                "status": "Status ID: 3 (Half-time)",  # ✅ Half-time
                "live_score": "Live Score: 0-0 (HT: 0-0)"  # ✅ 0-0 score
            },
            "corners": {"home": 3, "away": 2, "total": 5},
            "odds": {
                "O/U": [{"time_of_match": "3", "Over": "-110", "Total": 3.5, "Under": "-110"}],  # ✅ Total >= 3.0
                "MoneyLine": [{"time_of_match": "3", "Home": "+130", "Tie": "+210", "Away": "+190"}]
            },
            "environment": {"weather": "Perfect Alert Conditions", "pressure": "30.0 inHg", "temperature_f": "73 F", "wind": "3mph", "humidity": "48%"},
            "incidents": []
        }
        all_matches.append(qualifying_match_data)
        matches_in_play += 1
    
    # Create status breakdown
    status_breakdown = []
    status_counts = {}
    
    for match in all_matches:
        status = match["match_info"]["status"]
        if "Status ID: 2" in status:
            status_counts["Status ID 2 (First half)"] = status_counts.get("Status ID 2 (First half)", 0) + 1
        elif "Status ID: 3" in status:
            status_counts["Status ID 3 (Half-time)"] = status_counts.get("Status ID 3 (Half-time)", 0) + 1
        elif "Status ID: 4" in status:
            status_counts["Status ID 4 (Second half)"] = status_counts.get("Status ID 4 (Second half)", 0) + 1
        elif "Status ID: 8" in status:
            status_counts["Status ID 8 (End)"] = status_counts.get("Status ID 8 (End)", 0) + 1
    
    for status, count in status_counts.items():
        status_breakdown.append(f"{status}: {count} matches")
    
    return {
        "monitor_central_display": all_matches,
        "total_matches": len(all_matches),
        "generated_at": timestamp,
        "MONITOR_FOOTER": {
            "random_fetch_id": f"REALISTIC_{fetch_number}",
            "nyc_timestamp": timestamp,
            "pipeline_completion_time_seconds": 1.5 + (fetch_number * 0.1),
            "conversion_completion_time_seconds": 0.001,
            "fetch_end": f"=== REALISTIC FETCH #{fetch_number} DATA END ===",
            "total_matches": len(all_matches),
            "matches_in_play": matches_in_play,
            "match_status_breakdown": status_breakdown,
            "total_matches_with_odds": len(all_matches)
        }
    }

def run_realistic_mock_test():
    """Run 5 realistic fetches with 10-second intervals"""
    print("🚀 REALISTIC MOCK TEST - TIMED FETCHES")
    print("=" * 60)
    print("📊 SIMULATION: 5 fetches with 10-second intervals")
    print("🎯 EXPECTATION: Only fetch #3 should trigger alerts")
    print("=" * 60)
    
    # Change to mock directory
    os.chdir('/root/Guaranteed_last_one/MOCK_TEST/mock_7_alert_3ou_half')
    
    # Clear previous test data
    if os.path.exists('mock_alert_3ou_half.json'):
        os.remove('mock_alert_3ou_half.json')
    if os.path.exists('mock_alerted_match_ids.txt'):
        os.remove('mock_alerted_match_ids.txt')
    
    # Import the mock processor
    sys.path.append('/root/Guaranteed_last_one/MOCK_TEST/mock_7_alert_3ou_half')
    from alert_3ou_half import Alert3OUHalfProcessor
    
    # Create processor
    processor = Alert3OUHalfProcessor()
    
    # Define which fetches should have qualifying matches
    qualifying_fetches = [3]  # Only fetch #3 will trigger alerts
    
    # Run 5 fetches
    for fetch_num in range(1, 6):
        print(f"\\n📡 FETCH #{fetch_num} - {datetime.now().strftime('%I:%M:%S %p')}")
        print("-" * 40)
        
        # Create realistic data for this fetch
        has_qualifying = fetch_num in qualifying_fetches
        fetch_data = create_realistic_fetch_data(fetch_num, qualifying_match=has_qualifying)
        
        # Write to mock monitor file
        with open('../mock_6_monitor_central/mock_monitor_central.json', 'w') as f:
            json.dump(fetch_data, f, indent=2)
        
        # Process the data
        print(f"📊 Processing {fetch_data['total_matches']} matches...")
        if has_qualifying:
            print(f"🎯 QUALIFYING MATCH EXPECTED: Alert Test FC #{fetch_num} vs Telegram United #{fetch_num}")
        else:
            print(f"📝 No qualifying matches expected (regular monitoring)")
        
        # Run the processor
        try:
            result = processor.process_monitor_data("../mock_6_monitor_central/mock_monitor_central.json")
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
            else:
                filtered_count = result.get("filtered_match_count", 0)
                if filtered_count > 0:
                    print(f"🚨 ALERT TRIGGERED: {filtered_count} qualifying matches found!")
                    print(f"📱 Check Telegram for alerts!")
                else:
                    print(f"✅ No qualifying matches - normal monitoring")
                    
        except Exception as e:
            print(f"❌ Processing error: {e}")
        
        # Wait 10 seconds before next fetch (except for last one)
        if fetch_num < 5:
            print(f"⏳ Waiting 10 seconds before next fetch...")
            time.sleep(10)
    
    # Final summary
    print(f"\\n" + "=" * 60)
    print("📊 REALISTIC MOCK TEST SUMMARY")
    print("=" * 60)
    
    # Check final log state
    if os.path.exists('mock_alert_3ou_half.json'):
        with open('mock_alert_3ou_half.json', 'r') as f:
            log_content = f.read()
        
        fetch_count = log_content.count('=== FETCH START:')
        print(f"📝 Total fetch entries logged: {fetch_count}")
        
        if "Alert Test FC" in log_content:
            print(f"✅ Qualifying match detected and logged!")
        else:
            print(f"❌ No qualifying matches found in log")
    else:
        print(f"📝 No log file created (no qualifying matches)")
    
    # Check persistent tracking
    if os.path.exists('mock_alerted_match_ids.txt'):
        with open('mock_alerted_match_ids.txt', 'r') as f:
            alerted_ids = f.read().strip().split('\\n')
        print(f"💾 Persistent tracking: {len(alerted_ids)} unique match IDs saved")
    
    print(f"\\n🎯 EXPECTED RESULT: Only fetch #3 should have triggered alerts")
    print(f"📱 Check your Telegram for the alert message!")
    print(f"🧪 Test demonstrates realistic monitoring cycles with mixed data")

if __name__ == "__main__":
    run_realistic_mock_test()