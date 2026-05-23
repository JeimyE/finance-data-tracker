"""
Business logic for the Finance Data Tracker.
Orchestrates API calls, database persistence, and all user-facing data presentation.
"""

import csv
import os
from datetime import datetime
from typing import Optional

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.gridspec import GridSpec

import api
import database


def search_and_save_stock(ticker: str, api_key: str, db_path: str = database.DB_PATH) -> bool:
    """
    Fetch a stock's company info and price history from the API, then persist both.

    Falls back gracefully when the OVERVIEW endpoint returns no data (e.g. ETFs),
    and still saves the stock as long as a valid quote is found.

    Args:
        ticker: Stock ticker symbol to search for.
        api_key: Alpha Vantage API key.
        db_path: Path to the SQLite database file.

    Returns:
        True if the stock was successfully saved, False otherwise.
    """
    ticker = ticker.strip().upper()
    print(f"\n  Fetching data for {ticker}...")

    overview = api.get_company_overview(ticker, api_key)
    if overview:
        name = overview["name"]
        sector = overview["sector"]
        industry = overview["industry"]
    else:
        quote = api.get_stock_quote(ticker, api_key)
        if not quote or quote["price"] == 0.0:
            print(f"  [!] Could not find '{ticker}'. Please verify the ticker symbol.")
            return False
        name = ticker
        sector = "Unknown"
        industry = "Unknown"

    database.save_stock(ticker, name, sector, industry, db_path)
    print(f"  Company : {name}")
    print(f"  Sector  : {sector}")
    if overview and overview["industry"] != "Unknown":
        print(f"  Industry: {overview['industry']}")

    print("  Fetching price history (last ~100 trading days)...")
    history = api.get_daily_time_series(ticker, api_key, compact=True)
    if history:
        inserted = database.save_price_history(ticker, history, db_path)
        total = len(history)
        new_label = f"{inserted} new" if inserted < total else "all new"
        print(f"  Saved {total} trading days ({new_label} records).")
    else:
        print("  [!] Price history unavailable right now — try again later.")

    print(f"\n  '{ticker}' saved successfully.")
    return True


def display_all_stocks(db_path: str = database.DB_PATH) -> None:
    """
    Print a formatted table of every saved stock with its latest closing price.

    Args:
        db_path: Path to the SQLite database file.
    """
    stocks = database.get_all_stocks(db_path)
    if not stocks:
        print("\n  No stocks saved yet. Use option 1 to add a stock.")
        return

    print(f"\n  {'TICKER':<8} {'COMPANY':<30} {'SECTOR':<22} {'CLOSE':>10}  {'DATE'}")
    print("  " + "-" * 80)

    for stock in stocks:
        latest = database.get_latest_price(stock["ticker"], db_path)
        close_str = f"${latest['close']:>9.2f}" if latest else "       N/A"
        date_str = latest["date"] if latest else "N/A"
        name = stock["name"][:28]
        sector = stock["sector"][:20]
        print(f"  {stock['ticker']:<8} {name:<30} {sector:<22} {close_str}  {date_str}")

    print(f"\n  Total: {len(stocks)} stock(s) tracked.")


def compare_stocks(ticker1: str, ticker2: str, db_path: str = database.DB_PATH) -> None:
    """
    Print a side-by-side comparison table for two saved stocks.

    Displays company metadata, latest OHLCV, and 30-day percentage change.

    Args:
        ticker1: First stock ticker symbol.
        ticker2: Second stock ticker symbol.
        db_path: Path to the SQLite database file.
    """
    t1, t2 = ticker1.upper(), ticker2.upper()

    info1 = database.get_stock_info(t1, db_path)
    info2 = database.get_stock_info(t2, db_path)

    missing = [t for t, i in [(t1, info1), (t2, info2)] if i is None]
    if missing:
        print(
            f"\n  [!] Not in database: {', '.join(missing)}."
            " Please add them with option 1 first."
        )
        return

    price1 = database.get_latest_price(t1, db_path)
    price2 = database.get_latest_price(t2, db_path)
    hist1 = database.get_price_history(t1, 30, db_path)
    hist2 = database.get_price_history(t2, 30, db_path)

    def pct_change(rows) -> Optional[float]:
        if len(rows) < 2:
            return None
        return ((rows[-1]["close"] - rows[0]["close"]) / rows[0]["close"]) * 100

    chg1 = pct_change(hist1)
    chg2 = pct_change(hist2)

    col = 24

    def row(label: str, v1: str, v2: str) -> None:
        print(f"  {label:<24} {v1:^{col}} {v2:^{col}}")

    def money(val) -> str:
        return f"${val:.2f}" if val is not None else "N/A"

    def pct(val) -> str:
        return f"{val:+.2f}%" if val is not None else "N/A"

    print(f"\n  {'METRIC':<24} {t1:^{col}} {t2:^{col}}")
    print("  " + "-" * (24 + col * 2 + 2))

    row("Company", info1["name"][:col], info2["name"][:col])
    row("Sector", info1["sector"][:col], info2["sector"][:col])
    row("Industry", info1["industry"][:col], info2["industry"][:col])
    print("  " + "-" * (24 + col * 2 + 2))

    if price1 and price2:
        row("Date", price1["date"], price2["date"])
        row("Latest Close", money(price1["close"]), money(price2["close"]))
        row("Open", money(price1["open"]), money(price2["open"]))
        row("Day High", money(price1["high"]), money(price2["high"]))
        row("Day Low", money(price1["low"]), money(price2["low"]))
        row("Volume", f"{price1['volume']:,}", f"{price2['volume']:,}")
    else:
        print("  (Price data unavailable for one or both stocks)")

    print("  " + "-" * (24 + col * 2 + 2))
    row("30-Day Change", pct(chg1), pct(chg2))


def display_price_history(
    ticker: str, days: int = 30, db_path: str = database.DB_PATH
) -> None:
    """
    Print a formatted OHLCV table for the most recent trading days of a stock.

    Args:
        ticker: Stock ticker symbol.
        days: Number of trading days to display.
        db_path: Path to the SQLite database file.
    """
    ticker = ticker.upper()

    if not database.stock_exists(ticker, db_path):
        print(f"\n  [!] '{ticker}' is not in the database. Add it first with option 1.")
        return

    rows = database.get_price_history(ticker, days, db_path)
    if not rows:
        print(f"\n  No price history available for {ticker}.")
        return

    print(f"\n  Price history for {ticker}  (last {len(rows)} trading days)\n")
    print(f"  {'DATE':<12} {'OPEN':>10} {'HIGH':>10} {'LOW':>10} {'CLOSE':>10} {'VOLUME':>14}")
    print("  " + "-" * 72)
    for r in rows:
        print(
            f"  {r['date']:<12}"
            f" ${r['open']:>9.2f}"
            f" ${r['high']:>9.2f}"
            f" ${r['low']:>9.2f}"
            f" ${r['close']:>9.2f}"
            f" {r['volume']:>14,}"
        )


def generate_price_chart(
    ticker: str, days: int = 60, db_path: str = database.DB_PATH
) -> None:
    """
    Generate and display a dark-themed matplotlib price chart for a stock.

    The chart has two panels:
    - Top: closing price as a filled area, with dashed high/low lines.
    - Bottom: daily volume as green/red bars (green = price up, red = price down).

    Args:
        ticker: Stock ticker symbol.
        days: Number of recent trading days to include in the chart.
        db_path: Path to the SQLite database file.
    """
    ticker = ticker.upper()

    if not database.stock_exists(ticker, db_path):
        print(f"\n  [!] '{ticker}' is not in the database. Add it first with option 1.")
        return

    rows = database.get_price_history(ticker, days, db_path)
    if len(rows) < 2:
        print(f"\n  [!] Not enough data to chart {ticker} ({len(rows)} day(s) stored).")
        return

    info = database.get_stock_info(ticker, db_path)
    company_name = info["name"] if info else ticker

    dates = [datetime.strptime(r["date"], "%Y-%m-%d") for r in rows]
    closes = [r["close"] for r in rows]
    highs = [r["high"] for r in rows]
    lows = [r["low"] for r in rows]
    volumes = [r["volume"] for r in rows]

    BG_DARK = "#1e1e2e"
    BG_PANEL = "#12121f"
    BLUE = "#4fc3f7"
    GREEN = "#81c784"
    RED = "#ef9a9a"
    GRID = "#cccccc"
    SPINE = "#333355"

    fig = plt.figure(figsize=(13, 7), facecolor=BG_DARK)
    gs = GridSpec(4, 1, figure=fig, height_ratios=[3, 1, 0, 0], hspace=0.06)
    ax_price = fig.add_subplot(gs[0])
    ax_vol = fig.add_subplot(gs[1], sharex=ax_price)

    ax_price.fill_between(dates, closes, alpha=0.15, color=BLUE)
    ax_price.plot(dates, closes, color=BLUE, linewidth=1.8, label="Close", zorder=3)
    ax_price.plot(dates, highs, color=GREEN, linewidth=0.7, alpha=0.6,
                  linestyle="--", label="High")
    ax_price.plot(dates, lows, color=RED, linewidth=0.7, alpha=0.6,
                  linestyle="--", label="Low")

    ax_price.set_facecolor(BG_PANEL)
    ax_price.set_ylabel("Price (USD)", color=GRID, fontsize=10)
    ax_price.tick_params(colors=GRID)
    ax_price.legend(facecolor=BG_DARK, labelcolor=GRID, fontsize=8, loc="upper left")
    ax_price.grid(True, alpha=0.12, color=GRID)
    for spine in ax_price.spines.values():
        spine.set_color(SPINE)
    plt.setp(ax_price.get_xticklabels(), visible=False)

    ax_price.set_title(
        f"{ticker} — {company_name}   |   Last {len(dates)} Trading Days",
        color="#ffffff",
        fontsize=13,
        pad=12,
        fontweight="bold",
    )

    bar_colors = []
    for i, c in enumerate(closes):
        bar_colors.append(GREEN if i == 0 or c >= closes[i - 1] else RED)

    ax_vol.bar(dates, volumes, color=bar_colors, alpha=0.75, width=0.8)
    ax_vol.set_facecolor(BG_PANEL)
    ax_vol.set_ylabel("Volume", color=GRID, fontsize=9)
    ax_vol.tick_params(colors=GRID, labelsize=8)
    ax_vol.grid(True, alpha=0.08, color=GRID)
    for spine in ax_vol.spines.values():
        spine.set_color(SPINE)

    ax_vol.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax_vol.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    plt.setp(ax_vol.get_xticklabels(), rotation=30, ha="right", color=GRID, fontsize=8)

    fig.patch.set_facecolor(BG_DARK)
    plt.tight_layout()
    print(f"\n  Displaying chart for {ticker} — close the window to return to the menu.")
    plt.show()


def export_to_csv(
    ticker: str, days: int = 90, output_dir: str = ".", db_path: str = database.DB_PATH
) -> Optional[str]:
    """
    Export the price history of a stock to a timestamped CSV file.

    The CSV includes a metadata header block followed by a standard
    Date/Open/High/Low/Close/Volume table.

    Args:
        ticker: Stock ticker symbol.
        days: Number of recent trading days to export.
        output_dir: Directory where the CSV file will be written.
        db_path: Path to the SQLite database file.

    Returns:
        Absolute path to the created CSV file, or None if no data was found.
    """
    ticker = ticker.upper()

    if not database.stock_exists(ticker, db_path):
        print(f"\n  [!] '{ticker}' is not in the database. Add it first with option 1.")
        return None

    rows = database.get_price_history(ticker, days, db_path)
    if not rows:
        print(f"\n  No price history available for {ticker}.")
        return None

    info = database.get_stock_info(ticker, db_path)
    company_name = info["name"] if info else ticker
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"{ticker}_prices_{timestamp}.csv")

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["# Finance Data Tracker — Export"])
        writer.writerow([f"# Ticker: {ticker}   Company: {company_name}"])
        writer.writerow([f"# Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
        writer.writerow([f"# Records: {len(rows)}"])
        writer.writerow([])
        writer.writerow(["Date", "Open", "High", "Low", "Close", "Volume"])
        for r in rows:
            writer.writerow([r["date"], r["open"], r["high"], r["low"], r["close"], r["volume"]])

    abs_path = os.path.abspath(filename)
    print(f"\n  Exported {len(rows)} records  →  {abs_path}")
    return abs_path
