# Monitor Central Display Fields - README

## Overview
This document explains the cleaned up `monitor_central_roadmap_copy.json` file, which defines what data fields should be displayed in the Monitor Central interface.

## File Structure

### 1. MONITOR_CENTRAL_DISPLAY_FIELDS
This section documents **what data to show** and **where to get it from** in the pipeline:

#### Timestamp Information
```json
"timestamp_info": {
  "nyc_timestamp": "Use from SOURCE_PRETTY_PRINT_HEADER - represents when this match data was fetched"
}
```

#### Basic Match Information
```json
"match_basic_info": {
  "match_id": "From parsed_details.id",
  "competition_id": "From parsed_details.competition_id", 
  "competition_name": "From parsed_details.competition_name",
  "home_team_name": "From parsed_details.home_team_name",
  "away_team_name": "From parsed_details.away_team_name",
  "status_display": "Format: 'Status ID: {status_id} ({status_name})' - Example: 'Status ID: 2 (First Half)'",
  "formatted_live_score": "From formatted_live_score field"
}
```

#### Corner Statistics
```json
"corner_statistics": {
  "home_corners": "From live_data.parsed_score.home_detailed.corners",
  "away_corners": "From live_data.parsed_score.away_detailed.corners", 
  "total_corners": "Calculate: home_corners + away_corners"
}
```

#### Betting Odds (4 Types)
- **MoneyLine**: Home/Tie/Away odds
- **Spread**: Point spread betting
- **O/U**: Over/Under totals
- **Corners**: Corner betting markets

Each odds type includes:
- `time_of_match`: When odds were captured
- Relevant odds values for that market type

#### Environmental Data
```json
"environmental_data": {
  "weather": "From raw_match_details.environment.weather",
  "pressure": "From raw_match_details.environment.pressure",
  "temperature": "From raw_match_details.environment.temperature", 
  "wind": "From raw_match_details.environment.wind",
  "humidity": "From raw_match_details.environment.humidity"
}
```

### 2. CLEAN_DISPLAY_STRUCTURE
This section shows **how the final display should be organized**:

```json
{
  "timestamp": "",
  "match_info": {
    "match_id": "",
    "competition_id": "",
    "competition_name": "",
    "home_team": "",
    "away_team": "", 
    "status": "",
    "live_score": ""
  },
  "corners": {
    "home": "",
    "away": "",
    "total": ""
  },
  "odds": {
    "MoneyLine": [],
    "Spread": [],
    "O/U": [],
    "Corners": []
  },
  "environment": {
    "weather": "",
    "pressure": "",
    "temperature": "",
    "wind": "",
    "humidity": ""
  }
}
```

## What Was Fixed

### Before (Messy)
- Broken JSON syntax with missing quotes and brackets
- Mixed formatting and incomplete structures
- Random text mixed with JSON
- Impossible to parse or use

### After (Clean)
- Valid JSON structure throughout
- Clear documentation of data sources
- Organized into logical sections
- Ready for implementation
- Professional formatting

## How to Use This

1. **For Display Development**: Use `CLEAN_DISPLAY_STRUCTURE` as your template
2. **For Data Mapping**: Use `MONITOR_CENTRAL_DISPLAY_FIELDS` to know where each field comes from
3. **For Implementation**: Extract data from the pipeline using the documented paths

## Example Implementation

```javascript
// Get timestamp from pipeline data
const timestamp = pipelineData.SOURCE_PRETTY_PRINT_HEADER.nyc_timestamp;

// Get match info
const matchInfo = {
  match_id: pipelineData.CONVERTED_DATA.MATCHES_WITH_CONVERTED_ODDS[0].match_details.parsed_details.id,
  competition_name: pipelineData.CONVERTED_DATA.MATCHES_WITH_CONVERTED_ODDS[0].match_details.parsed_details.competition_name,
  home_team: pipelineData.CONVERTED_DATA.MATCHES_WITH_CONVERTED_ODDS[0].match_details.parsed_details.home_team_name,
  // ... etc
};

// Calculate total corners
const homeCorners = pipelineData.CONVERTED_DATA.MATCHES_WITH_CONVERTED_ODDS[0].live_data.parsed_score.home_detailed.corners;
const awayCorners = pipelineData.CONVERTED_DATA.MATCHES_WITH_CONVERTED_ODDS[0].live_data.parsed_score.away_detailed.corners;
const totalCorners = homeCorners + awayCorners;
```

## Status Display Format
For the status field, format it as:
```
"Status ID: {status_id} ({status_name})"
```

Example: `"Status ID: 2 (First Half)"`

This README serves as the guide for implementing the Monitor Central display based on your cleaned up requirements.