#!/usr/bin/env python3
"""
Test Script for Duplicate Prevention Logic
Tests the alert_3ou_half.py duplicate prevention across 5 scenarios
"""

import json
import os
import shutil
import sys
from datetime import datetime

# Add the alert directory to path so we can import the processor
sys.path.append('/root/Guaranteed_last_one/7_alert_3ou_half')
from alert_3ou_half import Alert3OUHalfProcessor

class DuplicatePreventionTester:
    def __init__(self):
        self.test_dir = "/root/Guaranteed_last_one/7_alert_3ou_half"
        self.backup_file = None
        self.processor = Alert3OUHalfProcessor()
        self.test_results = []
        
    def backup_existing_log(self):
        """Backup existing alert_3ou_half.json if it exists"""
        log_file = os.path.join(self.test_dir, "alert_3ou_half.json")
        if os.path.exists(log_file):
            self.backup_file = f"{log_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(log_file, self.backup_file)
            print(f"✅ Backed up existing log to: {self.backup_file}")
        else:
            print("ℹ️  No existing log file to backup")
    
    def restore_backup(self):
        """Restore the original log file"""
        log_file = os.path.join(self.test_dir, "alert_3ou_half.json")
        if self.backup_file and os.path.exists(self.backup_file):
            shutil.copy2(self.backup_file, log_file)
            os.remove(self.backup_file)
            print(f"✅ Restored original log file")
        else:
            # If no backup, just remove test file
            if os.path.exists(log_file):
                os.remove(log_file)
            print("ℹ️  Cleaned up test file")
    
    def create_test_match(self, match_id, status="Status ID: 3 (Half-time)", 
                         live_score="Live Score: 0-0 (HT: 0-0)", ou_total=3.5):
        """Create a test match that meets filtering criteria"""
        return {
            "timestamp": "07/02/2025 02:00:00 PM EDT",
            "match_info": {
                "match_id": match_id,
                "competition_id": "test_comp",
                "competition_name": "Test League",
                "home_team": "Test Home",
                "away_team": "Test Away", 
                "status": status,
                "live_score": live_score
            },
            "corners": {"home": 2, "away": 1, "total": 3},
            "odds": {
                "O/U": [{"time_of_match": "3", "Over": "-110", "Total": ou_total, "Under": "-110"}]
            },
            "environment": {"weather": "Clear", "temperature_f": "70 F"}
        }
    
    def create_mock_monitor_data(self, matches):
        """Create mock monitor_central.json data"""
        return [{
            "monitor_central_display": matches,
            "total_matches": len(matches),
            "generated_at": "07/02/2025 02:00:00 PM EDT",
            "MONITOR_FOOTER": {
                "random_fetch_id": "TEST123",
                "nyc_timestamp": "07/02/2025 02:00:00 PM EDT",
                "total_matches": len(matches)
            }
        }]
    
    def write_mock_monitor_data(self, matches):
        """Write mock data to monitor_central.json"""
        monitor_file = os.path.join(self.test_dir, "../6_monitor_central/monitor_central.json")
        mock_data = self.create_mock_monitor_data(matches)
        with open(monitor_file, 'w') as f:
            json.dump(mock_data, f, indent=2)
    
    def count_logged_matches(self):
        """Count how many matches are in the alert log"""
        log_file = os.path.join(self.test_dir, "alert_3ou_half.json")
        try:
            with open(log_file, 'r') as f:
                data = json.load(f)
            total_matches = 0
            for entry in data:
                total_matches += len(entry.get("monitor_central_display", []))
            return total_matches
        except (FileNotFoundError, json.JSONDecodeError):
            return 0
    
    def get_logged_match_ids(self):
        """Get all match IDs currently in the log"""
        log_file = os.path.join(self.test_dir, "alert_3ou_half.json")
        try:
            with open(log_file, 'r') as f:
                data = json.load(f)
            match_ids = []
            for entry in data:
                for match in entry.get("monitor_central_display", []):
                    match_ids.append(match.get("match_info", {}).get("match_id"))
            return match_ids
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def run_processor(self):
        """Run the alert processor once"""
        os.chdir(self.test_dir)
        return self.processor.process_monitor_data("../6_monitor_central/monitor_central.json")
    
    def test_1_empty_log_new_match(self):
        """Test 1: Empty log + 1 new qualifying match = should log 1 match"""
        print("\n🧪 TEST 1: Empty log + 1 new qualifying match")
        
        # Create 1 qualifying match
        match1 = self.create_test_match("match_001")
        self.write_mock_monitor_data([match1])
        
        # Run processor
        result = self.run_processor()
        
        # Check results
        logged_count = self.count_logged_matches()
        expected = 1
        success = logged_count == expected
        
        print(f"   Expected: {expected} match logged")
        print(f"   Actual: {logged_count} matches logged")
        print(f"   Result: {'✅ PASS' if success else '❌ FAIL'}")
        
        self.test_results.append(("Test 1: Empty log + new match", success))
        return success
    
    def test_2_duplicate_same_match(self):
        """Test 2: Run same match again = should NOT log duplicate"""
        print("\n🧪 TEST 2: Same match again (should prevent duplicate)")
        
        # Keep same match data (match_001)
        match1 = self.create_test_match("match_001")
        self.write_mock_monitor_data([match1])
        
        # Run processor again
        result = self.run_processor()
        
        # Check results - should still be 1 total match
        logged_count = self.count_logged_matches()
        expected = 1
        success = logged_count == expected
        
        print(f"   Expected: {expected} match logged (no duplicate)")
        print(f"   Actual: {logged_count} matches logged")
        print(f"   Result: {'✅ PASS' if success else '❌ FAIL'}")
        
        self.test_results.append(("Test 2: Duplicate prevention", success))
        return success
    
    def test_3_new_different_match(self):
        """Test 3: Different qualifying match = should log new match"""
        print("\n🧪 TEST 3: Different qualifying match (should add)")
        
        # Create different qualifying match
        match2 = self.create_test_match("match_002")
        self.write_mock_monitor_data([match2])
        
        # Run processor
        result = self.run_processor()
        
        # Check results - should now be 2 total matches
        logged_count = self.count_logged_matches()
        expected = 2
        success = logged_count == expected
        
        print(f"   Expected: {expected} matches logged")
        print(f"   Actual: {logged_count} matches logged")
        print(f"   Result: {'✅ PASS' if success else '❌ FAIL'}")
        
        self.test_results.append(("Test 3: New different match", success))
        return success
    
    def test_4_mixed_new_and_duplicate(self):
        """Test 4: Mix of new and existing matches = should only log new ones"""
        print("\n🧪 TEST 4: Mix of new and existing matches")
        
        # Create mix: existing match_001, existing match_002, new match_003
        match1 = self.create_test_match("match_001")  # Already logged
        match2 = self.create_test_match("match_002")  # Already logged  
        match3 = self.create_test_match("match_003")  # New
        self.write_mock_monitor_data([match1, match2, match3])
        
        # Run processor
        result = self.run_processor()
        
        # Check results - should now be 3 total matches (only match_003 added)
        logged_count = self.count_logged_matches()
        expected = 3
        success = logged_count == expected
        
        print(f"   Expected: {expected} matches logged (only new one added)")
        print(f"   Actual: {logged_count} matches logged")
        print(f"   Result: {'✅ PASS' if success else '❌ FAIL'}")
        
        self.test_results.append(("Test 4: Mixed new/existing", success))
        return success
    
    def test_5_non_qualifying_matches(self):
        """Test 5: Non-qualifying matches = should not log anything new"""
        print("\n🧪 TEST 5: Non-qualifying matches (should not log)")
        
        # Create non-qualifying matches
        bad_match1 = self.create_test_match("match_004", status="Status ID: 2 (First half)")  # Wrong status
        bad_match2 = self.create_test_match("match_005", live_score="Live Score: 1-0 (HT: 1-0)")  # Wrong score
        bad_match3 = self.create_test_match("match_006", ou_total=2.5)  # Wrong O/U total
        self.write_mock_monitor_data([bad_match1, bad_match2, bad_match3])
        
        # Run processor
        result = self.run_processor()
        
        # Check results - should still be 3 total matches (no new ones added)
        logged_count = self.count_logged_matches()
        expected = 3
        success = logged_count == expected
        
        print(f"   Expected: {expected} matches logged (no new non-qualifying matches)")
        print(f"   Actual: {logged_count} matches logged")
        print(f"   Result: {'✅ PASS' if success else '❌ FAIL'}")
        
        self.test_results.append(("Test 5: Non-qualifying matches", success))
        return success
    
    def print_final_results(self):
        """Print comprehensive test results"""
        print("\n" + "="*60)
        print("🎯 DUPLICATE PREVENTION TEST RESULTS")
        print("="*60)
        
        passed = sum(1 for _, success in self.test_results if success)
        total = len(self.test_results)
        
        for test_name, success in self.test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        print(f"\n📊 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED - Duplicate prevention is working correctly!")
        else:
            print("⚠️  SOME TESTS FAILED - Check duplicate prevention logic")
        
        # Show current log contents
        print(f"\n📋 Final logged match IDs: {self.get_logged_match_ids()}")
        
    def run_all_tests(self):
        """Run all 5 tests in sequence"""
        print("🧪 Starting Duplicate Prevention Tests")
        print("Testing alert_3ou_half.py duplicate filtering...")
        
        try:
            # Backup existing data
            self.backup_existing_log()
            
            # Run all tests in sequence
            self.test_1_empty_log_new_match()
            self.test_2_duplicate_same_match() 
            self.test_3_new_different_match()
            self.test_4_mixed_new_and_duplicate()
            self.test_5_non_qualifying_matches()
            
            # Print results
            self.print_final_results()
            
        finally:
            # Always restore backup
            self.restore_backup()

if __name__ == "__main__":
    tester = DuplicatePreventionTester()
    tester.run_all_tests()