# Monitor Central Display - Live Match Data

## Overview
This document shows what the **Monitor Central display data** would look like when implemented with real match data based on your cleaned roadmap structure.

## Live Match Example: Manchester United vs Liverpool

```json
{
  "timestamp": "07/02/2025 02:45:30 AM EDT",
  "match_info": {
    "match_id": "1234567",
    "competition_id": "45",
    "competition_name": "Premier League",
    "home_team": "Manchester United",
    "away_team": "Liverpool", 
    "status": "Status ID: 2 (First Half)",
    "live_score": "Man United 1 - 0 Liverpool (42')"
  },
  "corners": {
    "home": 3,
    "away": 5,
    "total": 8
  },
  "odds": {
    "MoneyLine": [
      {
        "time_of_match": "prematch",
        "Home": "2.15",
        "Tie": "3.40",
        "Away": "2.85"
      },
      {
        "time_of_match": "15",
        "Home": "1.95",
        "Tie": "3.60",
        "Away": "3.20"
      },
      {
        "time_of_match": "42",
        "Home": "1.75",
        "Tie": "4.10",
        "Away": "4.50"
      }
    ],
    "Spread": [
      {
        "time_of_match": "prematch",
        "Home": "1.85",
        "Spread": "-0.5",
        "Away": "1.95"
      },
      {
        "time_of_match": "15",
        "Home": "1.90",
        "Spread": "-0.5",
        "Away": "1.90"
      },
      {
        "time_of_match": "42",
        "Home": "1.80",
        "Spread": "-1.0",
        "Away": "2.00"
      }
    ],
    "O/U": [
      {
        "time_of_match": "prematch",
        "Over": "1.90",
        "Total": "2.5",
        "Under": "1.90"
      },
      {
        "time_of_match": "15",
        "Over": "1.85",
        "Total": "2.5",
        "Under": "1.95"
      },
      {
        "time_of_match": "42",
        "Over": "2.10",
        "Total": "3.5",
        "Under": "1.75"
      }
    ],
    "Corners": [
      {
        "time_of_match": "prematch",
        "Over": "1.95",
        "Total": "9.5",
        "Under": "1.85"
      },
      {
        "time_of_match": "15",
        "Over": "1.80",
        "Total": "10.5",
        "Under": "2.00"
      },
      {
        "time_of_match": "42",
        "Over": "2.20",
        "Total": "11.5",
        "Under": "1.65"
      }
    ]
  },
  "environment": {
    "weather": "Clear",
    "pressure": "29.9 inHg",
    "temperature": "64°F",
    "wind": "3.1 mph NE",
    "humidity": "65%"
  }
}
```

## Key Data Fields Breakdown

### 🕐 Timestamp Information
- **NYC Timestamp**: `07/02/2025 02:45:30 AM EDT`
- **Source**: `SOURCE_PRETTY_PRINT_HEADER.nyc_timestamp`

### ⚽ Match Information

| Field | Value | Source |
|-------|-------|--------|
| Match ID | 1234567 | `parsed_details.id` |
| Competition | Premier League | `parsed_details.competition_name` |
| Home Team | Manchester United | `parsed_details.home_team_name` |
| Away Team | Liverpool | `parsed_details.away_team_name` |
| Status | Status ID: 2 (First Half) | Formatted `status_id` |
| Live Score | Man United 1 - 0 Liverpool (42') | `formatted_live_score` |

### 🚩 Corner Statistics

| Team | Corners | Source |
|------|---------|--------|
| Manchester United (Home) | 3 | `live_data.parsed_score.home_detailed.corners` |
| Liverpool (Away) | 5 | `live_data.parsed_score.away_detailed.corners` |
| **Total** | **8** | **Calculated: home + away** |

### 💰 Betting Odds Evolution

#### MoneyLine Odds Movement
| Time | Home | Tie | Away | Notes |
|------|------|-----|------|-------|
| Pre-match | 2.15 | 3.40 | 2.85 | Liverpool slightly favored |
| 15 min | 1.95 | 3.60 | 3.20 | Even odds |
| 42 min | 1.75 | 4.10 | 4.50 | Man United heavily favored |

#### Spread Betting
| Time | Home | Spread | Away |
|------|------|--------|------|
| Pre-match | 1.85 | -0.5 | 1.95 |
| 15 min | 1.90 | -0.5 | 1.90 |
| 42 min | 1.80 | -1.0 | 2.00 |

#### Over/Under Totals
| Time | Over | Total | Under |
|------|------|-------|-------|
| Pre-match | 1.90 | 2.5 | 1.90 |
| 15 min | 1.85 | 2.5 | 1.95 |
| 42 min | 2.10 | 3.5 | 1.75 |

#### Corner Betting
| Time | Over | Total | Under |
|------|------|-------|-------|
| Pre-match | 1.95 | 9.5 | 1.85 |
| 15 min | 1.80 | 10.5 | 2.00 |
| 42 min | 2.20 | 11.5 | 1.65 |

### 🌤️ Environmental Conditions (Converted to US Units)

| Condition | Value | Original | Conversion |
|-----------|-------|----------|------------|
| Weather | Clear | Clear | No change |
| Pressure | 29.9 inHg | 1013 hPa | hPa → inHg |
| Temperature | 64°F | 18°C | °C → °F |
| Wind | **3.1 mph NE** | 5 km/h NE | **km/h → mph** |
| Humidity | 65% | 65% | No change |

## Unit Conversions Applied

### 🌡️ Temperature Conversion
- **Original**: 18°C
- **Converted**: 64°F
- **Formula**: `°F = (°C × 9/5) + 32`

### 🌪️ Wind Speed Conversion (FIXED!)
- **Original**: 5 km/h
- **Converted**: **3.1 mph**
- **Formula**: `mph = km/h × 0.621371`

### 📊 Pressure Conversion
- **Original**: 1013 hPa
- **Converted**: 29.9 inHg  
- **Formula**: `inHg = hPa × 0.02953`

## Implementation Notes

1. **Odds Time Tracking**: Shows how betting odds change throughout the match
2. **Corner Calculation**: Automatically sums home and away corners
3. **Status Formatting**: Clear display of match status with ID and description
4. **US Unit System**: All environmental data converted to US standard units ✅
5. **Real-time Updates**: Data structure supports live updating every 60 seconds

## Data Pipeline Integration

This JSON structure is the final output of your 4-stage pipeline:
1. **all_api.py** → Raw data collection
2. **merge.py** → Data enrichment  
3. **pretty_print.py** → Data cleaning
4. **monitor_central.py** → Final display formatting

**Perfect for**: Dashboards, mobile apps, web interfaces, and monitoring systems!

## Quick Reference

### Wind Conversion Fixed ✅
- **Before**: `"5 km/h NE"` ❌
- **After**: `"3.1 mph NE"` ✅

All environmental data now properly converted to US standard units!