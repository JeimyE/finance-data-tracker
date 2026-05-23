"""
Finance Data Tracker — Application entry point.

Presents an interactive console menu for searching stocks, viewing prices,
comparing tickers, charting price history, and exporting data to CSV.
"""

import json
import sys
from pathlib import Path

import database
import tracker

CONFIG_FILE = "config.json"


def load_config() -> dict:
    """
    Load persisted configuration from config.json.

    Returns:
        Parsed config dict, or an empty dict if the file is missing or corrupt.
    """
    path = Path(CONFIG_FILE)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_config(config: dict) -> None:
    """
    Persist configuration to config.json.

    Args:
        config: Dictionary of configuration values to save.
    """
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def get_api_key(config: dict) -> str:
    """
    Return the Alpha Vantage API key from config, or prompt the user to enter one.

    If the user provides a new key it is saved to config.json for future sessions.

    Args:
        config: Mutable config dictionary (will be updated with the key).

    Returns:
        The API key string.
    """
    if config.get("api_key"):
        return config["api_key"]

    print("\n" + "=" * 62)
    print("  Alpha Vantage API Key Required")
    print("=" * 62)
    print("  Get your FREE key at:")
    print("  https://www.alphavantage.co/support/#api-key\n")
    print("  Free tier: 25 requests/day · 5 requests/minute")
    print("  Each 'Search & Save' uses up to 2 requests.\n")

    key = input("  Enter your API key: ").strip()
    if not key:
        print("\n  [!] No API key provided. Exiting.")
        sys.exit(1)

    config["api_key"] = key
    save_config(config)
    print("  API key saved to config.json — you won't be asked again.\n")
    return key


def print_banner() -> None:
    """Print the application header banner."""
    print("\n" + "=" * 62)
    print("     FINANCE DATA TRACKER  |  Powered by Alpha Vantage")
    print("=" * 62)


def print_menu() -> None:
    """Print the numbered main menu."""
    print("\n  ┌─ MAIN MENU ────────────────────────────────┐")
    print("  │  1. Search and save a stock                │")
    print("  │  2. View saved stocks & latest prices      │")
    print("  │  3. Compare two stocks side by side        │")
    print("  │  4. View price history of a stock          │")
    print("  │  5. Generate price chart (matplotlib)      │")
    print("  │  6. Export stock data to CSV               │")
    print("  │  0. Exit                                   │")
    print("  └─────────────────────────────────────────────┘")


def prompt_ticker(label: str = "Enter ticker symbol (e.g. AAPL): ") -> str:
    """Read and return a non-empty upper-case ticker from stdin."""
    value = input(f"  {label}").strip().upper()
    if not value:
        print("  [!] No ticker entered.")
    return value


def prompt_days(default: int) -> int:
    """
    Prompt for a number of trading days, returning the default on empty input.

    Args:
        default: Value to use when the user presses Enter without typing.

    Returns:
        Positive integer number of days.
    """
    raw = input(f"  Number of trading days [default: {default}]: ").strip()
    if raw.isdigit() and int(raw) > 0:
        return int(raw)
    return default


def handle_search(api_key: str) -> None:
    """Prompt for a ticker and save it with its price history."""
    ticker = prompt_ticker("Enter ticker symbol to search (e.g. AAPL, TSLA): ")
    if ticker:
        tracker.search_and_save_stock(ticker, api_key)


def handle_view() -> None:
    """Display the full list of saved stocks."""
    tracker.display_all_stocks()


def handle_compare() -> None:
    """Prompt for two tickers and display a side-by-side comparison."""
    t1 = prompt_ticker("First  ticker: ")
    if not t1:
        return
    t2 = prompt_ticker("Second ticker: ")
    if not t2:
        return
    tracker.compare_stocks(t1, t2)


def handle_history() -> None:
    """Prompt for a ticker and day count, then display the OHLCV table."""
    ticker = prompt_ticker()
    if not ticker:
        return
    days = prompt_days(default=30)
    tracker.display_price_history(ticker, days)


def handle_chart() -> None:
    """Prompt for a ticker and day count, then render the price chart."""
    ticker = prompt_ticker()
    if not ticker:
        return
    days = prompt_days(default=60)
    tracker.generate_price_chart(ticker, days)


def handle_export() -> None:
    """Prompt for a ticker and day count, then write a CSV file."""
    ticker = prompt_ticker()
    if not ticker:
        return
    days = prompt_days(default=90)
    tracker.export_to_csv(ticker, days)


def main() -> None:
    """
    Application entry point.

    Initialises the database, resolves the API key, then runs the interactive
    menu loop until the user chooses to exit.
    """
    print_banner()

    config = load_config()
    api_key = get_api_key(config)

    database.init_db()

    menu_handlers = {
        "1": lambda: handle_search(api_key),
        "2": handle_view,
        "3": handle_compare,
        "4": handle_history,
        "5": handle_chart,
        "6": handle_export,
    }

    while True:
        print_menu()
        choice = input("\n  Select an option [0-6]: ").strip()

        if choice == "0":
            print("\n  Goodbye!\n")
            break

        if choice not in menu_handlers:
            print("  [!] Invalid choice. Please enter a number between 0 and 6.")
            continue

        try:
            menu_handlers[choice]()
        except KeyboardInterrupt:
            print("\n  [Cancelled]")
        except Exception as exc:
            print(f"\n  [Error] An unexpected error occurred: {exc}")

        input("\n  Press Enter to return to the menu...")


if __name__ == "__main__":
    main()
