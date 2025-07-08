#!/usr/bin/env python3

def explain_0_vs_minus1():
    """Explain the difference between index 0 and index -1"""
    
    print("=" * 70)
    print("🎯 DIFFERENCE BETWEEN [0] AND [-1]")
    print("=" * 70)
    
    # Create a simple array of fetches
    fetches = [
        "First fetch (oldest)",
        "Second fetch", 
        "Third fetch",
        "Fourth fetch",
        "Fifth fetch (newest)"
    ]
    
    print("\n📋 Our array of fetches:")
    for i, fetch in enumerate(fetches):
        print(f"   [{i}] {fetch}")
    
    print("\n🔢 What different indexes give you:")
    print(f"   fetches[0]  = {fetches[0]}")
    print(f"   fetches[1]  = {fetches[1]}")
    print(f"   fetches[2]  = {fetches[2]}")
    print(f"   fetches[3]  = {fetches[3]}")
    print(f"   fetches[4]  = {fetches[4]}")
    
    print(f"\n   fetches[-1] = {fetches[-1]}")
    print(f"   fetches[-2] = {fetches[-2]}")
    print(f"   fetches[-3] = {fetches[-3]}")
    print(f"   fetches[-4] = {fetches[-4]}")
    print(f"   fetches[-5] = {fetches[-5]}")
    
    print("\n🎯 KEY DIFFERENCE:")
    print("   • [0] = FIRST item (oldest)")
    print("   • [-1] = LAST item (newest)")
    
    print("\n📊 Visual representation:")
    print("   OLDEST ←←←←←←←←←←←←←←←←←←←←←←←←←←← NEWEST")
    print("   [0]     [1]     [2]     [3]     [4]")
    print("   [-5]    [-4]    [-3]    [-2]    [-1]")
    print("   ↑                               ↑")
    print("   FIRST                         LAST")
    
    print("\n🕐 Timeline analogy:")
    print("   Think of it like a timeline:")
    print("   Past ←←←←←←←←←←←←←←←←←←←←←←←← Present")
    print("   [0]                            [-1]")
    print("   OLD                            NEW")
    
    print("\n🔄 What happens when we add a new fetch:")
    print("   BEFORE: [Fetch1, Fetch2, Fetch3, Fetch4, Fetch5]")
    print("           [0]     [1]     [2]     [3]     [4]")
    print("           [-5]    [-4]    [-3]    [-2]    [-1]")
    
    # Add a new fetch
    fetches.append("Sixth fetch (brand new)")
    
    print("\n   AFTER adding new fetch:")
    print("   [Fetch1, Fetch2, Fetch3, Fetch4, Fetch5, Fetch6]")
    print("   [0]     [1]     [2]     [3]     [4]     [5]")
    print("   [-6]    [-5]    [-4]    [-3]    [-2]    [-1]")
    print("                                            ↑")
    print("                                        NEW!")
    
    print("\n✨ The magic of [-1]:")
    print("   • [0] always gives you the SAME old fetch")
    print("   • [-1] always gives you the NEWEST fetch")
    print("   • Even when the array grows, [-1] tracks the newest")
    
    print(f"\n🎯 After adding new fetch:")
    print(f"   fetches[0]  = {fetches[0]} (still oldest)")
    print(f"   fetches[-1] = {fetches[-1]} (now newest)")
    
    print("\n💡 Why VAR logger uses [-1]:")
    print("   • If we used [0], we'd always get the first (oldest) fetch")
    print("   • If we used [-1], we always get the last (newest) fetch")
    print("   • We want the newest fetch to check for new VAR incidents")
    print("   • So we use [-1] to get the most recent data")
    
    print("\n🚫 What would happen if we used [0]:")
    print("   • We'd always process the first fetch over and over")
    print("   • We'd never see new VAR incidents")
    print("   • We'd miss all the recent game data")
    
    print("\n✅ What happens because we use [-1]:")
    print("   • We always process the most recent fetch")
    print("   • We catch new VAR incidents as they happen")
    print("   • We stay current with live game data")

if __name__ == "__main__":
    explain_0_vs_minus1()