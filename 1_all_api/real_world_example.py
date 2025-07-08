#!/usr/bin/env python3

def real_world_example():
    """Show a real-world example of how this works"""
    
    print("=" * 70)
    print("⚽ REAL WORLD EXAMPLE: FOOTBALL MATCH TRACKING")
    print("=" * 70)
    
    # Simulate what happens during a live football match
    match_events = []
    
    print("\n🏈 Let's say we're tracking a live football match...")
    print("   Each 'fetch' checks for new events in the game")
    
    print("\n⏱️  12:00 PM - FETCH #1:")
    fetch1 = {"time": "12:00", "events": ["Match starts", "Kickoff"]}
    match_events.append(fetch1)
    print(f"   Events found: {fetch1['events']}")
    print(f"   Array: [Fetch1]")
    print(f"   match_events[0] = {match_events[0]['events']} (oldest)")
    print(f"   match_events[-1] = {match_events[-1]['events']} (newest)")
    
    print("\n⏱️  12:05 PM - FETCH #2:")
    fetch2 = {"time": "12:05", "events": ["Yellow card", "Corner kick"]}
    match_events.append(fetch2)
    print(f"   Events found: {fetch2['events']}")
    print(f"   Array: [Fetch1, Fetch2]")
    print(f"   match_events[0] = {match_events[0]['events']} (oldest)")
    print(f"   match_events[-1] = {match_events[-1]['events']} (newest)")
    
    print("\n⏱️  12:10 PM - FETCH #3:")
    fetch3 = {"time": "12:10", "events": ["VAR REVIEW!", "Penalty awarded"]}
    match_events.append(fetch3)
    print(f"   Events found: {fetch3['events']}")
    print(f"   Array: [Fetch1, Fetch2, Fetch3]")
    print(f"   match_events[0] = {match_events[0]['events']} (oldest)")
    print(f"   match_events[-1] = {match_events[-1]['events']} (newest)")
    
    print("\n⏱️  12:15 PM - FETCH #4:")
    fetch4 = {"time": "12:15", "events": ["Goal scored", "Celebration"]}
    match_events.append(fetch4)
    print(f"   Events found: {fetch4['events']}")
    print(f"   Array: [Fetch1, Fetch2, Fetch3, Fetch4]")
    print(f"   match_events[0] = {match_events[0]['events']} (oldest)")
    print(f"   match_events[-1] = {match_events[-1]['events']} (newest)")
    
    print("\n🎯 Now imagine the VAR logger runs after each fetch:")
    
    print("\n   After FETCH #1:")
    print(f"   • Using [0]: Would check {match_events[0]['events']} (match start)")
    print(f"   • Using [-1]: Would check {match_events[0]['events']} (match start)")
    print("   • Both same because only 1 item")
    
    print("\n   After FETCH #2:")
    print(f"   • Using [0]: Would check {match_events[0]['events']} (match start)")
    print(f"   • Using [-1]: Would check {match_events[1]['events']} (new events)")
    print("   • [-1] finds the NEW events!")
    
    print("\n   After FETCH #3:")
    print(f"   • Using [0]: Would check {match_events[0]['events']} (match start)")
    print(f"   • Using [-1]: Would check {match_events[2]['events']} (VAR REVIEW!)")
    print("   • [-1] finds the VAR incident!")
    
    print("\n   After FETCH #4:")
    print(f"   • Using [0]: Would check {match_events[0]['events']} (match start)")
    print(f"   • Using [-1]: Would check {match_events[3]['events']} (goal)")
    print("   • [-1] finds the newest events!")
    
    print("\n🔍 The problem with using [0]:")
    print("   • It would check the same old events over and over")
    print("   • It would miss the VAR incident at 12:10")
    print("   • It would miss the goal at 12:15")
    print("   • It would never find NEW incidents")
    
    print("\n✅ The benefit of using [-1]:")
    print("   • It always checks the most recent events")
    print("   • It found the VAR incident at 12:10")
    print("   • It found the goal at 12:15")
    print("   • It catches NEW incidents as they happen")
    
    print("\n🎯 Summary:")
    print("   • [0] = Always looks at the FIRST (oldest) fetch")
    print("   • [-1] = Always looks at the LAST (newest) fetch")
    print("   • For live sports, we want the newest data")
    print("   • So we use [-1] to get the most recent events")

if __name__ == "__main__":
    real_world_example()