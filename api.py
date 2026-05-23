"""
Alpha Vantage API client for fetching real-time and historical stock market data.
"""

import requests
from typing import Optional, Dict, Any, List


BASE_URL = "https://www.alphavantage.co/query"


def get_stock_quote(ticker: str, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Fetch the current quote (latest price data) for a given stock ticker.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'GOOGL').
        api_key: Alpha Vantage API key.

    Returns:
        Dictionary with quote data or None if the request fails or ticker is invalid.
    """
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": ticker.upper(),
        "apikey": api_key,
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "Note" in data:
            print("  [API Warning] Rate limit reached. Please wait before retrying.")
            return None
        if "Information" in data:
            print(f"  [API Info] {data['Information']}")
            return None
        if "Global Quote" not in data or not data["Global Quote"]:
            return None

        quote = data["Global Quote"]
        return {
            "ticker": quote.get("01. symbol", ticker.upper()),
            "open": float(quote.get("02. open", 0)),
            "high": float(quote.get("03. high", 0)),
            "low": float(quote.get("04. low", 0)),
            "price": float(quote.get("05. price", 0)),
            "volume": int(quote.get("06. volume", 0)),
            "latest_trading_day": quote.get("07. latest trading day", ""),
            "previous_close": float(quote.get("08. previous close", 0)),
            "change": float(quote.get("09. change", 0)),
            "change_percent": quote.get("10. change percent", "0%"),
        }
    except requests.exceptions.ConnectionError:
        print("  [API Error] No internet connection. Please check your network.")
        return None
    except requests.exceptions.Timeout:
        print("  [API Error] Request timed out. Please try again.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  [API Error] Network error fetching quote for {ticker}: {e}")
        return None
    except (ValueError, KeyError) as e:
        print(f"  [API Error] Unexpected data format for {ticker}: {e}")
        return None


def get_daily_time_series(
    ticker: str, api_key: str, compact: bool = True
) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch daily historical OHLCV price data for a given stock ticker.

    Args:
        ticker: Stock ticker symbol.
        api_key: Alpha Vantage API key.
        compact: If True, returns the last ~100 trading days.
                 If False, returns up to 20 years of history (costs more requests).

    Returns:
        List of dicts with keys date/open/high/low/close/volume sorted oldest-first,
        or None if the request fails.
    """
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": ticker.upper(),
        "outputsize": "compact" if compact else "full",
        "apikey": api_key,
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if "Note" in data:
            print("  [API Warning] Rate limit reached. Please wait a minute before retrying.")
            return None
        if "Information" in data:
            print(f"  [API Info] {data['Information']}")
            return None
        if "Time Series (Daily)" not in data:
            return None

        records = []
        for date_str, values in data["Time Series (Daily)"].items():
            records.append({
                "date": date_str,
                "open": float(values.get("1. open", 0)),
                "high": float(values.get("2. high", 0)),
                "low": float(values.get("3. low", 0)),
                "close": float(values.get("4. close", 0)),
                "volume": int(values.get("5. volume", 0)),
            })

        records.sort(key=lambda x: x["date"])
        return records

    except requests.exceptions.ConnectionError:
        print("  [API Error] No internet connection. Please check your network.")
        return None
    except requests.exceptions.Timeout:
        print("  [API Error] Request timed out. Please try again.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  [API Error] Network error fetching time series for {ticker}: {e}")
        return None
    except (ValueError, KeyError) as e:
        print(f"  [API Error] Unexpected data format for {ticker}: {e}")
        return None


def get_company_overview(ticker: str, api_key: str) -> Optional[Dict[str, str]]:
    """
    Fetch company metadata: name, sector, industry, market cap, and key ratios.

    Args:
        ticker: Stock ticker symbol.
        api_key: Alpha Vantage API key.

    Returns:
        Dictionary with company details or None if the ticker is not found or the
        request fails.
    """
    params = {
        "function": "OVERVIEW",
        "symbol": ticker.upper(),
        "apikey": api_key,
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "Note" in data:
            print("  [API Warning] Rate limit reached. Please wait before retrying.")
            return None
        if not data or "Symbol" not in data:
            return None

        return {
            "ticker": data.get("Symbol", ticker.upper()),
            "name": data.get("Name", "Unknown"),
            "sector": data.get("Sector", "Unknown"),
            "industry": data.get("Industry", "Unknown"),
            "description": data.get("Description", ""),
            "market_cap": data.get("MarketCapitalization", "N/A"),
            "pe_ratio": data.get("PERatio", "N/A"),
            "52_week_high": data.get("52WeekHigh", "N/A"),
            "52_week_low": data.get("52WeekLow", "N/A"),
        }
    except requests.exceptions.ConnectionError:
        print("  [API Error] No internet connection. Please check your network.")
        return None
    except requests.exceptions.Timeout:
        print("  [API Error] Request timed out. Please try again.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"  [API Error] Network error fetching overview for {ticker}: {e}")
        return None
    except (ValueError, KeyError) as e:
        print(f"  [API Error] Unexpected data format for {ticker}: {e}")
        return None
