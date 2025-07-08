
● Project Overview

  This is a sports betting data pipeline and real-time monitoring system that fetches live football match data, processes it through multiple stages, and sends alerts via Telegram when
  specific betting conditions are met.

  File-by-File Logging Logic Analysis

  Core Pipeline Files:

  /root/Guaranteed_last_one/1_all_api/all_api.py
  • Uses AllApiLogger class with rotating JSON logs every 50 fetches
  • Logs complete raw API responses with headers/footers containing random fetch IDs and NYC timestamps
  • Creates timestamped log files: all_api_log/all_api_log_YYYYMMDD_HHMMSS.json
  • Main output: all_api.json (overwrites each fetch)
  • Includes pipeline timing, match statistics, and match status breakdowns
  • Uses logging.FileHandler with structured JSON format
  • Triggers next pipeline stage (merge.py) after completion

  /root/Guaranteed_last_one/3_merge/merge.py
  • Uses MergeLogger class with persistent state management via PersistentStateManager
  • Logs merged data combining raw API data with enriched team/competition names
  • Creates rotating log files: merge_log/merge_log_YYYYMMDD_HHMMSS.json
  • Main output: merge.json
  • Preserves original random fetch ID from all_api.py for pipeline continuity
  • Includes merge timing and enhanced match statistics
  • Triggers next pipeline stage (pretty_print.py) after completion

  /root/Guaranteed_last_one/4_pretty_print/pretty_print.py
  • Uses PrettyPrintLogger class with persistent state management
  • Removes bulk raw reference data while preserving enriched match data
  • Creates rotating log files: pretty_print_log/pretty_print_log_YYYYMMDD_HHMMSS.json
  • Main output: pretty_print.json
  • Filters odds to prioritize Bet365 (company ID "2")
  • Filters incidents to only show VAR incidents (type 28)
  • Pure pass-through logging of cleaned data
  • Triggers next pipeline stage (pretty_print_conversion.py) after completion

  /root/Guaranteed_last_one/5_pretty_print_conversion/pretty_print_conversion.py
  • Uses PrettyPrintConversionLogger class with persistent state management
  • Converts odds formats (European/Hong Kong to American) and environmental data
  • Creates rotating log files: pretty_conversion_log/pretty_conversion_log_YYYYMMDD_HHMMSS.json
  • Main output: pretty_print_conversion.json
  • Converts temperature (Celsius to Fahrenheit), wind speeds, weather codes
  • Structures odds data with time-based filtering (prefers minute 3, max minute 10)
  • Triggers next pipeline stage (monitor_central.py) after completion

  /root/Guaranteed_last_one/6_monitor_central/monitor_central.py
  • Uses MonitorCentralLogger class with persistent state management
  • Creates monitor-friendly display format with natural language conversions
  • Main output: monitor_central.json (no rotating logs, only main file)
  • Converts environmental data with proper unit conversions
  • Formats match status displays with human-readable text
  • Pure catch-all pass-through logging of monitor display data
  • Triggers next pipeline stage (alert_3ou_half.py) after completion

  Alert Processing Files:

  /root/Guaranteed_last_one/7_alert_3ou_half/alert_3ou_half.py
  • Uses Alert3OUHalfLogger class with persistent state management
  • Filters matches: Status 3 (Half-time) + 0-0 score + O/U Total >= 3.0
  • Creates rotating log files: Alert_log/alert_3ou_half/alert_3ou_half_log_YYYYMMDD_HHMMSS.json
  • Main output: alert_3ou_half.json
  • Includes duplicate prevention logic to avoid re-logging same match IDs
  • Sends individual Telegram alerts for each filtered match
  • Uses NYC timestamps in headers/footers
  • Triggers next pipeline stage (alert_underdog_0half.py) after completion

  /root/Guaranteed_last_one/8_alert_underdog_0half/alert_underdog_0half.py
  • Uses AlertUnderdogHalfLogger class with special midnight rotation logic
  • Pure catch-all pass-through logging with no filtering
  • Creates rotating log files: alert_underdog_0half_log/alert_underdog_0half_log_YYYYMMDD_HHMMSS.json
  • Main output: alert_underdog_0half.json
  • Automatically rotates logs at midnight NYC time (clears accumulated data daily)
  • Uses extended rotation limit (1440 fetches = 24 hours)
  • No Telegram alerts - pure archival logging
  • End of pipeline (no further stage triggers)

  Utility/Support Files:

  /root/Guaranteed_last_one/shared_utils/persistent_state.py
  • Provides PersistentStateManager class for state persistence across stages
  • Creates {stage_name}_fetch_state.json files to track fetch counts and accumulated data
  • Thread-safe with threading.Lock()
  • Handles state loading, saving, and rotation logic
  • No direct logging - utility class for other loggers

  /root/Guaranteed_last_one/2_cached_endpoints/team_compeition_country_cache.py
  • Uses CacheManager class for API response caching
  • Creates team_compeition_country_cache.json with TTL-based caching
  • No logging mechanism - pure caching utility
  • Caches teams/competitions (24 hours), countries (7 days)
  • Reduces API calls through intelligent caching

  /root/Guaranteed_last_one/var_type_28.py
  • Standalone VAR incident scanner
  • Creates var_type_28_log.json with timestamped VAR incident logs
  • Uses basic JSON file appending (no rotation)
  • Scans all_api.json for VAR incidents (type 28)
  • Prints summary to console
  • Independent utility (not part of main pipeline)

  /root/Guaranteed_last_one/create_backup.py
  • Empty file - no logging logic

  Logging Architecture Patterns:

  Common Logging Features Across Pipeline:
  • All stages use structured JSON logging with headers/footers
  • NYC timezone timestamps throughout pipeline
  • Persistent state management for fetch counts and accumulated data
  • Rotating logs with configurable limits (typically 50 fetches)
  • Pipeline continuity via subprocess triggering between stages
  • Main output files (non-rotating) for current data access

  Unique Logging Behaviors:
  • all_api.py: Creates new random fetch IDs for pipeline tracking
  • merge.py: Preserves fetch IDs from previous stage for continuity
  • pretty_print.py: Massive log files due to detailed data processing
  • alert_3ou_half.py: Includes duplicate prevention and Telegram integration
  • alert_underdog_0half.py: Special midnight rotation with daily data clearing

> ok now specifically for all api log pretty print pretty print conversion monitor cetnral can you be more specific about those files , including logggin g.

● Detailed Logging Analysis for Core Pipeline Files

  1_all_api/all_api.py - Data Fetcher

  Logging Class: AllApiLogger
  • Log Directory: all_api_log/
  • Rotation: Every 50 fetches (max_fetches=50)
  • Log File Format: all_api_log_YYYYMMDD_HHMMSS.json
  • Main Output: all_api.json (overwrites each time)

  Detailed Logging Structure:
  {
    "FETCH_HEADER": {
      "fetch_number": 1,
      "random_fetch_id": "aBc123XyZ456", // 12-char random ID
      "nyc_timestamp": "07/08/2025 03:45:22 PM EDT",
      "fetch_start": "=== RAW API DATA START ==="
    },
    "RAW_API_DATA": {
      "live_matches": {...}, // Complete API response
      "match_details": [...], // Array of match detail responses
      "match_odds": [...] // Array of odds responses
    },
    "FETCH_FOOTER": {
      "random_fetch_id": "aBc123XyZ456", // Same as header
      "nyc_timestamp": "07/08/2025 03:45:25 PM EDT",
      "pipeline_completion_time_seconds": 2.847,
      "total_matches": 45,
      "matches_in_play": 12,
      "match_status_breakdown": [
        "Status ID 2 (First half): 8 matches",
        "Status ID 3 (Half-time): 4 matches"
      ]
    }
  }

  Logging Behavior:
  • Accumulates data in memory until 50 fetches, then rotates
  • Each fetch appends to accumulated_data array
  • Writes to both rotating log AND all_api.json on every fetch
  • Generates match statistics by analyzing status codes
  • Logs pipeline timing from start to finish
  • Creates continuous log file: all_api_continuous.log

  ---
  4_pretty_print/pretty_print.py - Data Cleaner

  Logging Class: PrettyPrintLogger
  • Log Directory: pretty_print_log/
  • Rotation: Every 50 fetches via PersistentStateManager
  • Log File Format: pretty_print_log_YYYYMMDD_HHMMSS.json
  • Main Output: pretty_print.json

  Detailed Logging Structure:
  {
    "FETCH_HEADER": {
      "fetch_number": 23,
      "random_fetch_id": "xyz789abc123", // Inherited from all_api
      "nyc_timestamp": "07/08/2025 03:45:30 PM EDT",
      "fetch_start": "=== MERGED DATA START ==="
    },
    "MERGED_DATA": {
      "SOURCE_ALL_API_HEADER": {...}, // Original all_api header
      "SOURCE_RAW_API_DATA": {
        "live_matches": {...},
        "match_odds": [...] // Filtered to Bet365 only
        // Removed: teams, competitions, countries bulk data
      },
      "MERGED_MATCH_CENTRIC_DATA": {
        "matches": [
          {
            "match_id": "12345",
            "live_data": {
              "incidents": [...] // Only VAR incidents (type 28)
              // Removed: stats, tlive arrays
            },
            "match_details": {
              "parsed_details": {...} // With team/competition names
              // Removed: raw_match_details
            },
            "home_team": {
              "parsed_team": {...} // With names
              // Removed: raw_team_data
            }
          }
        ]
        // Removed: reference_data section
      }
    }
  }

  Specific Logging Logic:
  • Pure pass-through: Takes exact data from merge.json, applies cleaning
  • Massive log files: These are the largest logs due to detailed match data
  • Odds filtering: Prioritizes Bet365 (company ID "2"), removes other bookmakers
  • Incident filtering: Only keeps VAR incidents (type 28), removes all others
  • Time-based odds filtering: Only keeps odds from minutes 0-10, no duplicates
  • State persistence: Uses PersistentStateManager to survive restarts

  ---
  5_pretty_print_conversion/pretty_print_conversion.py - Format Converter

  Logging Class: PrettyPrintConversionLogger
  • Log Directory: pretty_conversion_log/
  • Rotation: Every 50 fetches via PersistentStateManager
  • Log File Format: pretty_conversion_log_YYYYMMDD_HHMMSS.json
  • Main Output: pretty_print_conversion.json

  Detailed Logging Structure:
  {
    "CONVERSION_HEADER": {
      "fetch_number": 15,
      "random_fetch_id": "def456ghi789",
      "nyc_timestamp": "07/08/2025 03:45:35 PM EDT",
      "fetch_start": "=== RAW API DATA START ==="
    },
    "CONVERTED_DATA": {
      "SOURCE_PRETTY_PRINT_HEADER": {...},
      "MATCHES_WITH_CONVERTED_ODDS": [
        {
          "match_id": "12345",
          "formatted_live_score": "Live Score: 2-1 (HT: 1-1)",
          "Home Corners": 3,
          "Away Corners": 5,
          "converted_odds": {
            "Spread": [
              {
                "time_of_match": "3", // Prefers minute 3
                "Home": "-110", // Converted to American odds
                "Spread": "-1.5", // Line unchanged
                "Away": "+105" // Converted to American odds
              }
            ],
            "MoneyLine": [...],
            "O/U": [...],
            "Corners": [...]
          },
          "raw_match_details": {
            "environment": {
              "weather": "Clear", // Converted from code to text
              "temperature": "73F", // Converted from Celsius
              "wind": "15mph (Moderate Breeze)", // Converted from m/s
              "pressure": "29.9 inHg", // Converted units
              "humidity": "65%"
            }
          }
        }
      ]
    },
    "CONVERSION_FOOTER": {
      "random_fetch_id": "def456ghi789",
      "conversion_completion_time_seconds": 0.245,
      "total_matches_with_odds": 23,
      "pipeline_completion_time_seconds": 4.125, // From original all_api
      "total_matches": 45,
      "matches_in_play": 12
    }
  }

  Conversion Logging Specifics:
  • Odds conversion: European/Hong Kong → American format with proper +/- signs
  • Environmental conversion: Celsius→Fahrenheit, m/s→mph with Beaufort scale
  • Time filtering: Prefers minute 3 odds, fallback to closest up to minute 10
  • Corner extraction: Pulls corner stats into dedicated fields
  • Weather mapping: Numeric codes → natural language ("Clear", "Cloudy", etc.)
  • Score formatting: Creates formatted display strings for live scores

  ---
  6_monitor_central/monitor_central.py - Display Formatter

  Logging Class: MonitorCentralLogger
  • Log Directory: None (no rotating logs)
  • Rotation: Every 50 fetches but only saves to main file
  • Main Output: monitor_central.json ONLY

  Detailed Logging Structure:
  {
    "monitor_central_display": [
      {
        "timestamp": "07/08/2025 03:45:40 PM EDT",
        "match_info": {
          "match_id": "12345",
          "competition_id": "67890",
          "competition_name": "Premier League",
          "home_team": "Arsenal",
          "away_team": "Chelsea",
          "status": "Status ID: 2 (First half)",
          "live_score": "Live Score: 1-0 (HT: 0-0)"
        },
        "corners": {
          "home": 3,
          "away": 5,
          "total": 8
        },
        "odds": {
          "Spread": [...],
          "MoneyLine": [...],
          "O/U": [...],
          "Corners": [...]
        },
        "environment": {
          "weather": "Clear",
          "pressure": "29.9 inHg",
          "temperature_f": "73 F", // Clean format without Unicode
          "wind": "15mph (Moderate Breeze)",
          "humidity": "65%"
        },
        "incidents": [...] // VAR incidents only
      }
    ],
    "total_matches": 23,
    "generated_at": "07/08/2025 03:45:40 PM EDT",
    "MONITOR_FOOTER": {
      "random_fetch_id": "ghi789jkl012",
      "nyc_timestamp": "07/08/2025 03:45:40 PM EDT",
      "pipeline_completion_time_seconds": 4.523,
      "conversion_completion_time_seconds": 0.245,
      "fetch_end": "=== MONITOR CENTRAL DATA END ===",
      "total_matches_with_odds": 23,
      "match_status_breakdown": [...]
    }
  }

  Monitor Central Logging Specifics:
  • No rotating logs: Only writes to monitor_central.json
  • Display optimization: Formats all data for human consumption
  • Status mapping: Converts numeric IDs to "Status ID: 2 (First half)" format
  • Environmental cleaning: Removes Unicode issues, standardizes formats
  • Pure extraction: Takes conversion data and creates clean display format
  • Corner aggregation: Calculates total corners for easy reference
  • Pipeline flow-through: Preserves all timing data from earlier stages

  Key Logging Differences:

  1. all_api.py: Creates new data, generates fetch IDs, logs raw API responses
  2. pretty_print.py: Massive logs due to complete data processing, removes bulk data
  3. pretty_print_conversion.py: Focuses on format conversions, smaller logs
  4. monitor_central.py: No rotating logs, only current display data, clean formatting

> can you make an entire comparison chart and list each file. like how you compare one feature is x'd and one feature is checked. do you know what i mean ? like when you are comparing two 
  differtetn computers and you are comparting features

● Pipeline Files Logging Comparison Chart

  File Overview

  | File                       | Purpose               | Input Source                 | Output File                  | Pipeline Position |
  |----------------------------|-----------------------|------------------------------|------------------------------|-------------------|
  | all_api.py                 | Raw API Data Fetcher  | TheSports.com API            | all_api.json                 | Stage 1 (Start)   |
  | merge.py                   | Data Enrichment       | all_api.json                 | merge.json                   | Stage 2           |
  | pretty_print.py            | Data Cleaning         | merge.json                   | pretty_print.json            | Stage 3           |
  | pretty_print_conversion.py | Format Conversion     | pretty_print.json            | pretty_print_conversion.json | Stage 4           |
  | monitor_central.py         | Display Formatting    | pretty_print_conversion.json | monitor_central.json         | Stage 5           |
  | alert_3ou_half.py          | Conditional Filtering | monitor_central.json         | alert_3ou_half.json          | Stage 6           |
  | alert_underdog_0half.py    | Archive Logging       | monitor_central.json         | alert_underdog_0half.json    | Stage 7 (End)     |

  Logging Features Comparison

  | Feature                     | all_api.py | merge.py | pretty_print.py | pretty_conversion.py | monitor_central.py | alert_3ou_half.py | alert_underdog_0half.py |
  |-----------------------------|------------|----------|-----------------|----------------------|--------------------|-------------------|-------------------------|
  | Rotating Log Files          | ✅          | ✅        | ✅               | ✅                    | ❌                  | ✅                 | ✅                       |
  | Main Output File            | ✅          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Persistent State Management | ❌          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | NYC Timestamps              | ✅          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Structured Headers/Footers  | ✅          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Random Fetch ID Generation  | ✅          | ❌        | ❌               | ❌                    | ❌                  | ❌                 | ❌                       |
  | Fetch ID Preservation       | ❌          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Pipeline Timing Logging     | ✅          | ✅        | ❌               | ✅                    | ✅                  | ❌                 | ❌                       |
  | Match Statistics            | ✅          | ✅        | ❌               | ✅                    | ✅                  | ❌                 | ❌                       |
  | Data Accumulation           | ✅          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Auto Stage Triggering       | ✅          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ❌                       |

  Data Processing Features

  | Feature                       | all_api.py | merge.py | pretty_print.py | pretty_conversion.py | monitor_central.py | alert_3ou_half.py | alert_underdog_0half.py |
  |-------------------------------|------------|----------|-----------------|----------------------|--------------------|-------------------|-------------------------|
  | Raw API Data                  | ✅          | ✅        | ✅               | ✅                    | ❌                  | ❌                 | ❌                       |
  | Team Name Enrichment          | ❌          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Competition Name Enrichment   | ❌          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Odds Data Processing          | ✅          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Odds Format Conversion        | ❌          | ❌        | ❌               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Environmental Data Conversion | ❌          | ❌        | ❌               | ✅                    | ✅                  | ✅                 | ✅                       |
  | VAR Incident Filtering        | ❌          | ❌        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Bet365 Odds Prioritization    | ❌          | ❌        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Data Filtering/Cleaning       | ❌          | ❌        | ✅               | ❌                    | ❌                  | ✅                 | ❌                       |
  | Display Formatting            | ❌          | ❌        | ❌               | ❌                    | ✅                  | ❌                 | ❌                       |

  Logging Configuration

  | Setting                     | all_api.py   | merge.py   | pretty_print.py   | pretty_conversion.py   | monitor_central.py | alert_3ou_half.py         | alert_underdog_0half.py   |
  |-----------------------------|--------------|------------|-------------------|------------------------|--------------------|---------------------------|---------------------------|
  | Max Fetches Before Rotation | 50           | 50         | 50                | 50                     | 50                 | 50                        | 1440                      |
  | Log Directory               | all_api_log/ | merge_log/ | pretty_print_log/ | pretty_conversion_log/ | None               | Alert_log/alert_3ou_half/ | alert_underdog_0half_log/ |
  | Uses Python logging Module  | ✅            | ✅          | ❌                 | ❌                      | ❌                  | ❌                         | ✅
   |
  | JSON Structure Logging      | ✅            | ✅          | ✅                 | ✅                      | ✅                  | ✅                         | ✅
   |
  | Continuous Log File         | ✅            | ❌          | ❌                 | ❌                      | ❌                  | ❌                         | ❌
   |
  | State File Creation         | ❌            | ✅          | ✅                 | ✅                      | ✅                  | ✅                         | ✅
   |
  | Midnight Rotation           | ❌            | ❌          | ❌                 | ❌                      | ❌                  | ❌                         | ✅
   |
  | Thread-Safe Logging         | ❌            | ✅          | ✅                 | ✅                      | ✅                  | ✅                         | ✅
   |

  Special Features

  | Feature              | all_api.py | merge.py | pretty_print.py | pretty_conversion.py | monitor_central.py | alert_3ou_half.py | alert_underdog_0half.py |
  |----------------------|------------|----------|-----------------|----------------------|--------------------|-------------------|-------------------------|
  | Telegram Integration | ❌          | ❌        | ❌               | ❌                    | ❌                  | ✅                 | ❌                       |
  | Duplicate Prevention | ❌          | ❌        | ❌               | ❌                    | ❌                  | ✅                 | ❌                       |
  | Caching Integration  | ❌          | ✅        | ❌               | ❌                    | ❌                  | ❌                 | ❌                       |
  | Async API Calls      | ✅          | ✅        | ❌               | ❌                    | ❌                  | ❌                 | ❌                       |
  | Signal Handling      | ✅          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Single-Run Mode      | ❌          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Continuous Mode      | ✅          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Error Recovery       | ✅          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |

  Log File Sizes (Relative)

  | File                    | Typical Log Size | Reason                     |
  |-------------------------|------------------|----------------------------|
  | all_api.py              | 🔴 Largest       | Complete raw API responses |
  | merge.py                | 🟠 Very Large    | Raw data + enriched data   |
  | pretty_print.py         | 🟡 Large         | Cleaned but still detailed |
  | pretty_conversion.py    | 🟢 Medium        | Converted formats only     |
  | monitor_central.py      | 🔵 Small         | Display format only        |
  | alert_3ou_half.py       | 🟣 Very Small    | Filtered matches only      |
  | alert_underdog_0half.py | 🟢 Medium        | Complete pass-through      |

  Data Flow & Dependencies

  all_api.py → merge.py → pretty_print.py → pretty_conversion.py → monitor_central.py → alert_3ou_half.py → alert_underdog_0half.py
       ↓           ↓              ↓                   ↓                      ↓                  ↓                    ↓
   all_api.json merge.json pretty_print.json pretty_conversion.json monitor_central.json alert_3ou_half.json alert_underdog_0half.json

  Key Differences Summary

  - all_api.py: Only file that generates new fetch IDs, has continuous logging
  - merge.py: Only file with caching integration, enriches team/competition names
  - pretty_print.py: Only file that aggressively removes bulk data, largest logs
  - pretty_conversion.py: Only file that converts data formats (odds, weather, etc.)
  - monitor_central.py: Only file with no rotating logs, pure display formatting
  - alert_3ou_half.py: Only file with Telegram alerts and duplicate prevention
  - alert_underdog_0half.py: Only file with midnight rotation and daily clearing

> ca you creatupdate all th einformation here in this reposne to it.

● Complete Sports Betting Pipeline Analysis & Logging Comparison

  🎯 Project Overview

  This is a real-time sports betting data pipeline that fetches live football match data from TheSports.com API, processes it through 7 sequential stages, and sends Telegram alerts when
  specific betting conditions are met. The system runs continuously with automatic crash recovery and comprehensive logging at every stage.

  📊 Pipeline Architecture Flow

  API Data → Enrichment → Cleaning → Conversion → Display → Filtering → Archiving
      ↓          ↓          ↓          ↓          ↓          ↓          ↓
  all_api.py → merge.py → pretty_print.py → conversion.py → monitor.py → alert_3ou.py → alert_underdog.py
      ↓          ↓          ↓              ↓           ↓          ↓             ↓
  all_api.json merge.json pretty_print.json conversion.json monitor.json alert_3ou.json underdog.json

  📋 File Overview Comparison

  | File                       | Purpose                        | Input Source                 | Output File                  | Pipeline Position | Data Size     |
  |----------------------------|--------------------------------|------------------------------|------------------------------|-------------------|---------------|
  | all_api.py                 | Raw API Data Fetcher           | TheSports.com API            | all_api.json                 | Stage 1 (Start)   | 🔴 Largest    |
  | merge.py                   | Data Enrichment & Caching      | all_api.json                 | merge.json                   | Stage 2           | 🟠 Very Large |
  | pretty_print.py            | Data Cleaning & Filtering      | merge.json                   | pretty_print.json            | Stage 3           | 🟡 Large      |
  | pretty_print_conversion.py | Format Conversion              | pretty_print.json            | pretty_print_conversion.json | Stage 4           | 🟢 Medium     |
  | monitor_central.py         | Display Formatting             | pretty_print_conversion.json | monitor_central.json         | Stage 5           | 🔵 Small      |
  | alert_3ou_half.py          | Conditional Filtering + Alerts | monitor_central.json         | alert_3ou_half.json          | Stage 6           | 🟣 Very Small |
  | alert_underdog_0half.py    | Archive Logging                | monitor_central.json         | alert_underdog_0half.json    | Stage 7 (End)     | 🟢 Medium     |

  🔧 Core Logging Features Comparison

  | Feature                     | all_api.py | merge.py | pretty_print.py | pretty_conversion.py | monitor_central.py | alert_3ou_half.py | alert_underdog_0half.py |
  |-----------------------------|------------|----------|-----------------|----------------------|--------------------|-------------------|-------------------------|
  | Rotating Log Files          | ✅          | ✅        | ✅               | ✅                    | ❌                  | ✅                 | ✅                       |
  | Main Output File            | ✅          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Persistent State Management | ❌          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | NYC Timestamps              | ✅          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Structured Headers/Footers  | ✅          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Random Fetch ID Generation  | ✅          | ❌        | ❌               | ❌                    | ❌                  | ❌                 | ❌                       |
  | Fetch ID Preservation       | ❌          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Pipeline Timing Logging     | ✅          | ✅        | ❌               | ✅                    | ✅                  | ❌                 | ❌                       |
  | Match Statistics Analysis   | ✅          | ✅        | ❌               | ✅                    | ✅                  | ❌                 | ❌                       |
  | Data Accumulation           | ✅          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Auto Stage Triggering       | ✅          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ❌                       |

  📁 Logging Configuration Details

  | Setting                     | all_api.py   | merge.py   | pretty_print.py   | pretty_conversion.py   | monitor_central.py | alert_3ou_half.py         | alert_underdog_0half.py   |
  |-----------------------------|--------------|------------|-------------------|------------------------|--------------------|---------------------------|---------------------------|
  | Max Fetches Before Rotation | 50           | 50         | 50                | 50                     | 50                 | 50                        | 1440 (24 hrs)             |
  | Log Directory               | all_api_log/ | merge_log/ | pretty_print_log/ | pretty_conversion_log/ | None               | Alert_log/alert_3ou_half/ | alert_underdog_0half_log/ |
  | Uses Python logging Module  | ✅            | ✅          | ❌                 | ❌                      | ❌                  | ❌                         | ✅
   |
  | JSON Structure Logging      | ✅            | ✅          | ✅                 | ✅                      | ✅                  | ✅                         | ✅
   |
  | Continuous Log File         | ✅            | ❌          | ❌                 | ❌                      | ❌                  | ❌                         | ❌
   |
  | State File Creation         | ❌            | ✅          | ✅                 | ✅                      | ✅                  | ✅                         | ✅
   |
  | Midnight Rotation           | ❌            | ❌          | ❌                 | ❌                      | ❌                  | ❌                         | ✅
   |
  | Thread-Safe Logging         | ❌            | ✅          | ✅                 | ✅                      | ✅                  | ✅                         | ✅
   |

  🔄 Data Processing Capabilities

  | Feature                       | all_api.py | merge.py | pretty_print.py | pretty_conversion.py | monitor_central.py | alert_3ou_half.py | alert_underdog_0half.py |
  |-------------------------------|------------|----------|-----------------|----------------------|--------------------|-------------------|-------------------------|
  | Raw API Data Handling         | ✅          | ✅        | ✅               | ✅                    | ❌                  | ❌                 | ❌                       |
  | Team Name Enrichment          | ❌          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Competition Name Enrichment   | ❌          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Country Name Resolution       | ❌          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Odds Data Processing          | ✅          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Odds Format Conversion        | ❌          | ❌        | ❌               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Environmental Data Conversion | ❌          | ❌        | ❌               | ✅                    | ✅                  | ✅                 | ✅                       |
  | VAR Incident Filtering        | ❌          | ❌        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Bet365 Odds Prioritization    | ❌          | ❌        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Conditional Data Filtering    | ❌          | ❌        | ✅               | ❌                    | ❌                  | ✅                 | ❌                       |
  | Display Format Optimization   | ❌          | ❌        | ❌               | ❌                    | ✅                  | ❌                 | ❌                       |

  ⚡ Special Features & Integrations

  | Feature                          | all_api.py | merge.py | pretty_print.py | pretty_conversion.py | monitor_central.py | alert_3ou_half.py | alert_underdog_0half.py |
  |----------------------------------|------------|----------|-----------------|----------------------|--------------------|-------------------|-------------------------|
  | Telegram Bot Integration         | ❌          | ❌        | ❌               | ❌                    | ❌                  | ✅                 | ❌                       |
  | Duplicate Prevention Logic       | ❌          | ❌        | ❌               | ❌                    | ❌                  | ✅                 | ❌                       |
  | API Response Caching             | ❌          | ✅        | ❌               | ❌                    | ❌                  | ❌                 | ❌                       |
  | Async/Await Processing           | ✅          | ✅        | ❌               | ❌                    | ❌                  | ❌                 | ❌                       |
  | Signal Handling (SIGINT/SIGTERM) | ✅          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Single-Run Mode Support          | ❌          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Continuous Mode Support          | ✅          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Automatic Error Recovery         | ✅          | ✅        | ✅               | ✅                    | ✅                  | ✅                 | ✅                       |
  | Rate Limiting (Semaphore)        | ✅          | ✅        | ❌               | ❌                    | ❌                  | ❌                 | ❌                       |

  📊 Detailed File-by-File Logging Analysis

  1_all_api/all_api.py - Raw Data Fetcher

  Logger Class: AllApiLogger
  - Creates: Random 12-character fetch IDs for pipeline tracking
  - Fetches: Live matches, match details, odds from TheSports.com API
  - Logs: Complete raw API responses with timing and match statistics
  - Rotation: Every 50 fetches to all_api_log/all_api_log_YYYYMMDD_HHMMSS.json
  - Output: all_api.json + all_api_continuous.log
  - Unique: Only file that generates new fetch IDs, uses Python logging module

  3_merge/merge.py - Data Enricher

  Logger Class: MergeLogger
  - Enriches: Adds team names, competition names, country names via cached API calls
  - Preserves: Original fetch ID from all_api for pipeline continuity
  - Logs: Merged data with enriched fields + original raw data
  - Caching: Integrates with CacheManager for efficient API usage
  - State: Uses PersistentStateManager for crash recovery
  - Unique: Only file with caching integration, enrichment processing

  4_pretty_print/pretty_print.py - Data Cleaner

  Logger Class: PrettyPrintLogger
  - Removes: Bulk raw reference data (teams, competitions, countries arrays)
  - Filters: Only Bet365 odds (company ID "2"), only VAR incidents (type 28)
  - Cleans: Removes stats/tlive arrays, raw_team_data sections
  - Logs: Cleaned data preserving enriched fields
  - Size: Largest log files due to comprehensive data processing
  - Unique: Most aggressive data cleaning, largest log files

  5_pretty_print_conversion/pretty_print_conversion.py - Format Converter

  Logger Class: PrettyPrintConversionLogger
  - Converts: European/Hong Kong odds → American format (+/-110)
  - Transforms: Celsius→Fahrenheit, m/s→mph, weather codes→text
  - Filters: Prefers minute 3 odds, max minute 10, removes duplicates
  - Formats: Creates structured odds display, formatted live scores
  - Logs: Converted data with user-friendly formats
  - Unique: Only file performing format conversions

  6_monitor_central/monitor_central.py - Display Formatter

  Logger Class: MonitorCentralLogger
  - Formats: Creates clean display-ready data structure
  - Converts: Status IDs to "Status ID: 2 (First half)" format
  - Aggregates: Corner totals, formatted environmental data
  - Logs: Only to main file (no rotating logs)
  - Output: monitor_central.json only
  - Unique: No rotating logs, pure display optimization

  7_alert_3ou_half/alert_3ou_half.py - Conditional Alert System

  Logger Class: Alert3OUHalfLogger
  - Filters: Status 3 (Half-time) + 0-0 score + O/U Total ≥ 3.0
  - Prevents: Duplicate alerts via match ID tracking
  - Alerts: Sends individual Telegram messages per filtered match
  - Logs: Only matches meeting specific betting criteria
  - Size: Smallest logs (only filtered matches)
  - Unique: Telegram integration, duplicate prevention, conditional filtering

  8_alert_underdog_0half/alert_underdog_0half.py - Archive Logger

  Logger Class: AlertUnderdogHalfLogger
  - Archives: Complete pass-through of all monitor data
  - Rotates: Daily at midnight NYC time (clears accumulated data)
  - Stores: 24 hours of data (1440 fetches max)
  - Logs: Pure catch-all archival with no filtering
  - Purpose: Long-term data retention and analysis
  - Unique: Midnight rotation, daily clearing, end of pipeline

  🔗 Pipeline Dependencies & Data Flow

  graph LR
      A[TheSports API] --> B[all_api.py]
      B --> C[merge.py]
      C --> D[pretty_print.py]
      D --> E[pretty_conversion.py]
      E --> F[monitor_central.py]
      F --> G[alert_3ou_half.py]
      F --> H[alert_underdog_0half.py]
      G --> I[Telegram Alerts]

      B -.-> J[all_api.json]
      C -.-> K[merge.json]
      D -.-> L[pretty_print.json]
      E -.-> M[pretty_conversion.json]
      F -.-> N[monitor_central.json]
      G -.-> O[alert_3ou_half.json]
      H -.-> P[alert_underdog_0half.json]

  📈 Log File Size Progression

  | Stage | File                    | Relative Size | Reason                                     |
  |-------|-------------------------|---------------|--------------------------------------------|
  | 1     | all_api.py              | 🔴 100%       | Complete raw API responses                 |
  | 2     | merge.py                | 🟠 120%       | Raw data + enriched team/competition names |
  | 3     | pretty_print.py         | 🟡 80%        | Cleaned but still comprehensive            |
  | 4     | pretty_conversion.py    | 🟢 60%        | Converted formats only                     |
  | 5     | monitor_central.py      | 🔵 40%        | Display-optimized format                   |
  | 6     | alert_3ou_half.py       | 🟣 5%         | Only filtered matches                      |
  | 7     | alert_underdog_0half.py | 🟢 40%        | Complete daily archive                     |

  🎯 Key Unique Features Summary

  - all_api.py: Only generates fetch IDs, has continuous logging, largest raw data
  - merge.py: Only has caching, enriches with team/competition/country names
  - pretty_print.py: Most aggressive cleaning, removes bulk data, largest processed logs
  - pretty_conversion.py: Only performs format conversions (odds, weather, units)
  - monitor_central.py: Only has no rotating logs, pure display formatting
  - alert_3ou_half.py: Only has Telegram alerts, duplicate prevention, conditional filtering
  - alert_underdog_0half.py: Only has midnight rotation, daily clearing, archive purpose

  🔄 Production Deployment

  The system runs with:
  - PM2 Process Manager: Auto-restart, memory monitoring, log rotation
  - Telegram Monitoring: Real-time file change alerts
  - 60-second intervals: Each stage processes every minute
  - Crash Recovery: Persistent state across all stages
  - Zero Maintenance: Automatic log rotation and cleanup