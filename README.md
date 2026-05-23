# Finance Data Tracker

A Python console application that fetches **real stock market data** from the [Alpha Vantage API](https://www.alphavantage.co/), stores it in a local SQLite database, and lets you explore, compare, chart, and export your personal watchlist — all from a clean interactive terminal menu.

---

## Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | **Search & Save** | Look up any stock by ticker (AAPL, GOOGL, TSLA…) and store company info + price history locally |
| 2 | **View Stocks** | Formatted table of all tracked stocks with their latest closing prices |
| 3 | **Compare Two Stocks** | Side-by-side: price, sector, OHLCV, and 30-day % change |
| 4 | **Price History** | Daily OHLCV table for any saved stock, configurable window |
| 5 | **Price Chart** | Dark-themed matplotlib chart — closing price area, high/low bands, color-coded volume bars |
| 6 | **CSV Export** | Timestamped CSV with metadata header, ready for Excel or pandas |

---

## Project Structure

```
finance-data-tracker/
├── main.py          # Entry point — interactive console menu
├── api.py           # Alpha Vantage API client (quote, time series, overview)
├── database.py      # SQLite layer (schema, CRUD, queries)
├── tracker.py       # Business logic (search, compare, chart, export)
├── requirements.txt # Python dependencies
└── README.md        # This file
```

---

## Requirements

- Python **3.8** or newer
- A free Alpha Vantage API key (see below — takes ~30 seconds to get)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/finance-data-tracker.git
cd finance-data-tracker
```

### 2. Create and activate a virtual environment *(recommended)*

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Getting a Free Alpha Vantage API Key

1. Go to **<https://www.alphavantage.co/support/#api-key>**
2. Fill in the short form — **no credit card required**.
3. Your key is displayed instantly and emailed to you.

### Free tier limits

| Limit | Value |
|-------|-------|
| Requests per day | 25 |
| Requests per minute | 5 |

> **Tip:** each *Search & Save* uses **2 API calls** (company overview + price history).  
> Viewing, comparing, charting, and exporting use **zero** API calls — they read from the local database.

---

## Running the Application

```bash
python main.py
```

**First run** — the app will ask for your API key and save it to `config.json` so you never need to enter it again:

```
==============================================================
     FINANCE DATA TRACKER  |  Powered by Alpha Vantage
==============================================================

  Alpha Vantage API Key Required
  Get your FREE key at:
  https://www.alphavantage.co/support/#api-key

  Enter your API key: YOUR_KEY_HERE
  API key saved to config.json — you won't be asked again.
```

---

## Usage Examples

### 1 — Add a stock

```
  Select an option [0-6]: 1
  Enter ticker symbol to search (e.g. AAPL, TSLA): AAPL

  Fetching data for AAPL...
  Company : Apple Inc
  Sector  : Technology
  Industry: Consumer Electronics
  Fetching price history (last ~100 trading days)...
  Saved 100 trading days (100 new records).

  'AAPL' saved successfully.
```

### 2 — View all saved stocks

```
  Select an option [0-6]: 2

  TICKER   COMPANY                        SECTOR                       CLOSE       DATE
  ─────────────────────────────────────────────────────────────────────────────────────
  AAPL     Apple Inc                      Technology                 $189.30  2024-01-15
  GOOGL    Alphabet Inc                   Technology                 $140.52  2024-01-15
  TSLA     Tesla Inc                      Consumer Cyclical          $218.89  2024-01-15

  Total: 3 stock(s) tracked.
```

### 3 — Compare two stocks

```
  Select an option [0-6]: 3
  First  ticker: AAPL
  Second ticker: MSFT

  METRIC                   AAPL                     MSFT
  ──────────────────────────────────────────────────────────────────────────
  Company                  Apple Inc                Microsoft Corporation
  Sector                   Technology               Technology
  Industry                 Consumer Electronics     Software—Infrastructure
  ──────────────────────────────────────────────────────────────────────────
  Date                     2024-01-15               2024-01-15
  Latest Close             $189.30                  $374.00
  Open                     $186.10                  $370.55
  Day High                 $191.05                  $376.20
  Day Low                  $184.50                  $369.10
  Volume                   52,341,200               21,180,400
  ──────────────────────────────────────────────────────────────────────────
  30-Day Change            +3.45%                   +6.12%
```

### 4 — View price history

```
  Select an option [0-6]: 4
  Enter ticker symbol (e.g. AAPL): TSLA
  Number of trading days [default: 30]: 5

  Price history for TSLA  (last 5 trading days)

  DATE              OPEN       HIGH        LOW      CLOSE         VOLUME
  ────────────────────────────────────────────────────────────────────────
  2024-01-09    $215.20    $219.80    $209.50    $218.89    103,450,200
  2024-01-10    $219.10    $222.45    $214.30    $220.55     98,230,100
  ...
```

### 5 — Generate a price chart

```
  Select an option [0-6]: 5
  Enter ticker symbol (e.g. AAPL): AAPL
  Number of trading days [default: 60]: 90

  Displaying chart for AAPL — close the window to return to the menu.
```

A dark-themed window opens with:
- **Top panel**: closing price area fill with dashed high/low bands and a legend
- **Bottom panel**: green (up day) / red (down day) color-coded volume bars

Close the chart window to return to the menu.

### 6 — Export to CSV

```
  Select an option [0-6]: 6
  Enter ticker symbol (e.g. AAPL): GOOGL
  Number of trading days [default: 90]: 90

  Exported 90 records  →  C:\...\finance-data-tracker\GOOGL_prices_20240115_143022.csv
```

Sample CSV output:

```csv
# Finance Data Tracker — Export
# Ticker: GOOGL   Company: Alphabet Inc
# Exported: 2024-01-15 14:30:22
# Records: 90

Date,Open,High,Low,Close,Volume
2023-10-01,130.25,132.80,129.10,131.45,24500000
2023-10-02,131.50,134.20,130.80,133.90,22100000
```

---

## Screenshots

> *Run the application and add your own screenshots here.*

| Main Menu | Price Chart | Price History |
|-----------|-------------|---------------|
| *(screenshot)* | *(screenshot)* | *(screenshot)* |

---

## Configuration

The API key and any future settings are stored in `config.json` at the project root:

```json
{
  "api_key": "YOUR_ALPHA_VANTAGE_KEY"
}
```

Edit this file directly to update your key at any time.

The SQLite database is saved as `finance_tracker.db` in the same directory.  
Delete it to start fresh — the app will recreate the schema on next launch.

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `requests` | ≥ 2.31 | HTTP calls to the Alpha Vantage REST API |
| `matplotlib` | ≥ 3.8 | Rendering the interactive price chart |
| `pandas` | ≥ 2.1 | Available for extended data analysis (CSV, DataFrame) |

---

## Error Handling

The app handles these scenarios gracefully:

| Scenario | Behavior |
|----------|----------|
| Invalid ticker | Clear message — no crash |
| API rate limit hit | Warning printed, returns to menu |
| No internet connection | Connection error caught, user informed |
| Empty database | Friendly prompt instead of a traceback |
| Not enough data for chart | Descriptive message, returns cleanly |

---

## License

MIT — free to use, modify, and distribute.

---

## Author

Built with Python and the [Alpha Vantage](https://www.alphavantage.co/) free API.  
Feedback and contributions welcome via Issues and Pull Requests.
