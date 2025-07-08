# TheSports.com API Endpoints Reference

This document provides the complete API endpoint URLs and authentication details needed for the sports data pipeline system.

## Base URL

**Base URL**: `https://api.thesports.com/v1/football/`

## Authentication

All endpoints require these authentication parameters:

```
user = "thenecpt"
secret = "0c55322e8e196d6ef9066fa4252cf386"
```

## Primary Endpoints for all_api.py

### 1. Live Match Discovery (Entry Point)
- **URL**: `https://api.thesports.com/v1/football/match/detail_live`
- **Parameters**: `user`, `secret`
- **Purpose**: Get all currently active matches and their IDs
- **Input**: None (global endpoint)
- **Output**: Array of match objects with `id` field

### 2. Match Details
- **URL**: `https://api.thesports.com/v1/football/match/recent/list`
- **Parameters**: `user`, `secret`, `uuid` (match ID from live endpoint)
- **Purpose**: Get detailed match information, team IDs, competition IDs
- **Input**: Match ID from live endpoint
- **Output**: Detailed match data with team and competition IDs

### 3. Betting Odds
- **URL**: `https://api.thesports.com/v1/football/odds/history`
- **Parameters**: `user`, `secret`, `uuid` (match ID from live endpoint)
- **Purpose**: Get betting odds and lines for each match
- **Input**: Match ID from live endpoint
- **Output**: Betting odds arrays for different markets

## Supporting Cache Endpoints

### 4. Team Information
- **URL**: `https://api.thesports.com/v1/football/team/additional/list`
- **Parameters**: `user`, `secret`, `uuid` (team ID from match details)
- **Purpose**: Get team names, logos, details
- **Cache Duration**: 24 hours
- **Input**: Team ID extracted from match details
- **Output**: Team information and metadata

### 5. Competition Information
- **URL**: `https://api.thesports.com/v1/football/competition/additional/list`
- **Parameters**: `user`, `secret`, `uuid` (competition ID from match details)
- **Purpose**: Get league/tournament information
- **Cache Duration**: 24 hours
- **Input**: Competition ID extracted from match details
- **Output**: Competition/league information

### 6. Country Reference
- **URL**: `https://api.thesports.com/v1/football/country/list`
- **Parameters**: `user`, `secret`
- **Purpose**: Get country lookup data
- **Cache Duration**: 24 hours
- **Input**: None (returns all countries)
- **Output**: Complete country reference data

## API Flow for all_api.py Implementation

### Sequential Processing Order:

1. **Initialize Pipeline**: Create fresh fetch ID for coordination
2. **Live Discovery**: Call `/match/detail_live` to get all active match IDs
3. **Parallel Processing**: 
   - Launch `/match/recent/list` for all match IDs
   - Launch `/odds/history` for all match IDs (same IDs)
   - Both use semaphore for 30 concurrent requests
4. **ID Extraction**: From match details responses, extract team and competition IDs
5. **Cache Processing**: 
   - Check team cache for all discovered team IDs
   - Check competition cache for all discovered competition IDs
   - Fetch missing or stale data only using respective endpoints
6. **Data Consolidation**: Combine all fetched data into unified structure

### Data Flow Relationships:

```
/match/detail_live (no input)
    ↓ (provides match IDs)
    ├── /match/recent/list (match ID) → extracts team IDs, competition IDs
    └── /odds/history (match ID) → betting data
         ↓
    ├── /team/additional/list (team ID) → team details
    ├── /competition/additional/list (competition ID) → league details
    └── /country/list (no input) → country reference
```

### Concurrency Management:

- Use semaphore with limit of 30 concurrent requests
- Apply to both match details and odds fetching
- Team/competition caching uses same concurrency limits
- Country data typically fetched once per day

### Error Handling:

- Continue processing even if individual match fetching fails
- Return empty structures for failed API calls
- Log errors but don't halt entire process
- Graceful degradation - missing data doesn't break pipeline

## Example Usage

```python
# 1. Start with live matches
url = "https://api.thesports.com/v1/football/match/detail_live"
params = {'user': 'thenecpt', 'secret': '0c55322e8e196d6ef9066fa4252cf386'}

# 2. For each match ID returned, get details and odds
match_id = "extracted_from_live_response"
detail_url = "https://api.thesports.com/v1/football/match/recent/list"
odds_url = "https://api.thesports.com/v1/football/odds/history"
params = {'user': 'thenecpt', 'secret': '0c55322e8e196d6ef9066fa4252cf386', 'uuid': match_id}

# 3. For extracted team/competition IDs, get cached data
team_id = "extracted_from_match_details"
team_url = "https://api.thesports.com/v1/football/team/additional/list"
params = {'user': 'thenecpt', 'secret': '0c55322e8e196d6ef9066fa4252cf386', 'uuid': team_id}
```

## Important Notes

- **IP Whitelisting**: Ensure your deployment IP is whitelisted with TheSports.com
- **Rate Limiting**: Use semaphore concurrency control to avoid overwhelming the API
- **Caching**: Implement 24-hour TTL for team, competition, and country data
- **Error Handling**: Always implement graceful failure recovery
- **Data Preservation**: Maintain all raw API responses for downstream processing

This endpoint reference provides everything needed to implement the unified all_api.py module for the sports data pipeline system.