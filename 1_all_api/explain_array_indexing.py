#!/usr/bin/env python3

def explain_array_indexing():
    """Explain how Python array indexing works with -1"""
    
    print("=" * 70)
    print("📚 PYTHON ARRAY INDEXING EXPLAINED")
    print("=" * 70)
    
    # Create example array like all_api.json
    fetches = [
        {"fetch_number": 1, "time": "12:00:00", "data": "First fetch"},
        {"fetch_number": 2, "time": "12:02:00", "data": "Second fetch"},
        {"fetch_number": 3, "time": "12:04:00", "data": "Third fetch"},
        {"fetch_number": 4, "time": "12:06:00", "data": "Fourth fetch"},
        {"fetch_number": 5, "time": "12:08:00", "data": "Fifth fetch"}
    ]
    
    print("\n🗂️  Example Array (like all_api.json):")
    print("fetches = [")
    for i, fetch in enumerate(fetches):
        print(f"  [{i}] {fetch}")
    print("]")
    
    print(f"\n📏 Array Length: {len(fetches)} items")
    print(f"📊 Index Range: 0 to {len(fetches)-1}")
    
    print("\n🔢 POSITIVE INDEXING (counting from START):")
    print("   Index:  0        1        2        3        4")
    print("   Value:  Fetch1   Fetch2   Fetch3   Fetch4   Fetch5")
    print("           ↑                                    ↑")
    print("         FIRST                                LAST")
    
    print("\n🔢 NEGATIVE INDEXING (counting from END):")
    print("   Index:  -5       -4       -3       -2       -1")
    print("   Value:  Fetch1   Fetch2   Fetch3   Fetch4   Fetch5")
    print("           ↑                                    ↑")
    print("         FIRST                                LAST")
    
    print("\n✨ What -1 means:")
    print("   • -1 = 'Give me the LAST item in the array'")
    print("   • -2 = 'Give me the SECOND to last item'")
    print("   • -3 = 'Give me the THIRD to last item'")
    print("   • etc...")
    
    print("\n🎯 Examples:")
    print(f"   fetches[0]  = {fetches[0]['data']}")
    print(f"   fetches[1]  = {fetches[1]['data']}")
    print(f"   fetches[-1] = {fetches[-1]['data']}")
    print(f"   fetches[-2] = {fetches[-2]['data']}")
    
    print("\n🔄 How all_api.py adds new fetches:")
    print("   1. Start with empty array: []")
    print("   2. Add fetch #1: [Fetch1]")
    print("   3. Add fetch #2: [Fetch1, Fetch2]")
    print("   4. Add fetch #3: [Fetch1, Fetch2, Fetch3]")
    print("   5. Add fetch #4: [Fetch1, Fetch2, Fetch3, Fetch4]")
    print("   6. Add fetch #5: [Fetch1, Fetch2, Fetch3, Fetch4, Fetch5]")
    
    print("\n📍 Key Point:")
    print("   • New fetches are APPENDED to the END of the array")
    print("   • The END of the array is always the MOST RECENT fetch")
    print("   • fetches[-1] ALWAYS gets the MOST RECENT fetch")
    
    print("\n🕐 Timeline visualization:")
    print("   TIME →")
    print("   12:00  12:02  12:04  12:06  12:08")
    print("   Fetch1 Fetch2 Fetch3 Fetch4 Fetch5")
    print("   [0]    [1]    [2]    [3]    [4]")
    print("   [-5]   [-4]   [-3]   [-2]   [-1]")
    print("                                 ↑")
    print("                            NEWEST")
    
    print("\n🎯 Why VAR logger uses [-1]:")
    print("   • It always gets the NEWEST fetch")
    print("   • It doesn't need to know the array length")
    print("   • It works whether there are 5 fetches or 500 fetches")
    print("   • It's the Python way to say 'give me the last one'")

if __name__ == "__main__":
    explain_array_indexing()