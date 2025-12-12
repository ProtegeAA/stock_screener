#!/usr/bin/env python3
"""
Blue-Chip Dividend Stock Screener
Based on Lyn Alden's investment principles from:
https://www.lynalden.com/blue-chip-dividend-stocks/

This screener evaluates stocks based on:
1. Dividend yield and growth history
2. Payout ratio sustainability
3. Balance sheet strength (interest coverage, debt/equity)
4. Return on invested capital (ROIC)
5. Valuation metrics
"""

import yfinance as yf
import pandas as pd
from dataclasses import dataclass
from typing import Optional
import sys


@dataclass
class ScreeningCriteria:
    """Configurable screening thresholds based on Lyn Alden's principles."""

    # Dividend criteria
    min_dividend_yield: float = 1.5          # Minimum dividend yield (%)
    max_dividend_yield: float = 8.0          # Max yield to avoid yield traps (%)
    min_dividend_years: int = 5              # Years of consecutive dividend payments
    max_payout_ratio: float = 50.0           # Max payout ratio for growth stocks (%)
    max_payout_ratio_reit: float = 85.0      # Max payout ratio for REITs/utilities (%)

    # Balance sheet criteria
    min_interest_coverage: float = 10.0      # Minimum interest coverage ratio
    min_interest_coverage_reit: float = 4.0  # For REITs/MLPs
    max_debt_to_equity: float = 1.0          # Maximum debt-to-equity ratio

    # Profitability criteria
    min_roic: float = 12.0                   # Minimum return on invested capital (%)
    min_roe: float = 15.0                    # Minimum return on equity (%)

    # Valuation criteria
    max_pe_ratio: float = 25.0               # Maximum P/E ratio
    min_expected_return: float = 8.0         # Dividend yield + expected growth (%)


@dataclass
class StockAnalysis:
    """Results of analyzing a single stock."""

    ticker: str
    name: str
    sector: str

    # Dividend metrics
    dividend_yield: Optional[float] = None
    payout_ratio: Optional[float] = None
    dividend_growth_5yr: Optional[float] = None

    # Balance sheet metrics
    interest_coverage: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None

    # Profitability metrics
    roic: Optional[float] = None
    roe: Optional[float] = None
    profit_margin: Optional[float] = None

    # Valuation metrics
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    price_to_book: Optional[float] = None

    # Calculated metrics
    expected_return: Optional[float] = None

    # Screening results
    passes_screen: bool = False
    score: int = 0
    flags: list = None

    def __post_init__(self):
        if self.flags is None:
            self.flags = []


def get_stock_data(ticker: str) -> Optional[StockAnalysis]:
    """Fetch and analyze a single stock using yfinance."""

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        if not info or 'shortName' not in info:
            return None

        analysis = StockAnalysis(
            ticker=ticker,
            name=info.get('shortName', ticker),
            sector=info.get('sector', 'Unknown'),
        )

        # Dividend metrics
        # yfinance returns dividendYield as percentage already (2.52 = 2.52%)
        analysis.dividend_yield = info.get('dividendYield')

        analysis.payout_ratio = info.get('payoutRatio')
        if analysis.payout_ratio:
            analysis.payout_ratio *= 100  # Convert to percentage

        # Try to get 5-year dividend growth from historical data
        try:
            dividends = stock.dividends
            if len(dividends) > 0:
                # Get annual dividend totals
                annual_divs = dividends.resample('YE').sum()
                if len(annual_divs) >= 5:
                    oldest = annual_divs.iloc[-5]
                    newest = annual_divs.iloc[-1]
                    if oldest > 0:
                        analysis.dividend_growth_5yr = ((newest / oldest) ** 0.2 - 1) * 100
        except Exception:
            pass

        # Balance sheet metrics
        analysis.debt_to_equity = info.get('debtToEquity')
        if analysis.debt_to_equity:
            analysis.debt_to_equity /= 100  # yfinance reports as percentage

        analysis.current_ratio = info.get('currentRatio')

        # Calculate interest coverage (EBIT / Interest Expense)
        try:
            financials = stock.financials
            if financials is not None and not financials.empty:
                ebit = financials.loc['EBIT'].iloc[0] if 'EBIT' in financials.index else None
                interest = financials.loc['Interest Expense'].iloc[0] if 'Interest Expense' in financials.index else None
                if ebit and interest and interest != 0:
                    analysis.interest_coverage = abs(ebit / interest)
        except Exception:
            pass

        # Profitability metrics
        analysis.roe = info.get('returnOnEquity')
        if analysis.roe:
            analysis.roe *= 100

        # Calculate ROIC: NOPAT / Invested Capital
        # ROIC approximation using available data
        try:
            analysis.roic = info.get('returnOnAssets')
            if analysis.roic:
                analysis.roic *= 100
                # Adjust ROA to approximate ROIC (rough estimate)
                if analysis.debt_to_equity:
                    leverage_factor = 1 + analysis.debt_to_equity
                    analysis.roic = analysis.roic * leverage_factor * 0.8  # Conservative adjustment
        except Exception:
            pass

        analysis.profit_margin = info.get('profitMargins')
        if analysis.profit_margin:
            analysis.profit_margin *= 100

        # Valuation metrics
        analysis.pe_ratio = info.get('trailingPE')
        analysis.forward_pe = info.get('forwardPE')
        analysis.price_to_book = info.get('priceToBook')

        # Calculate expected return (Dividend Yield + Expected Growth)
        if analysis.dividend_yield and analysis.dividend_growth_5yr:
            analysis.expected_return = analysis.dividend_yield + analysis.dividend_growth_5yr
        elif analysis.dividend_yield:
            # Estimate growth from earnings growth
            earnings_growth = info.get('earningsGrowth')
            if earnings_growth:
                analysis.expected_return = analysis.dividend_yield + (earnings_growth * 100)

        return analysis

    except Exception as e:
        print(f"Error fetching {ticker}: {e}", file=sys.stderr)
        return None


def screen_stock(analysis: StockAnalysis, criteria: ScreeningCriteria) -> StockAnalysis:
    """Apply screening criteria to a stock analysis."""

    if analysis is None:
        return None

    score = 0
    flags = []
    is_reit = 'REIT' in analysis.sector or 'Real Estate' in analysis.sector
    is_utility = 'Utilities' in analysis.sector
    high_leverage_sector = is_reit or is_utility

    # --- Dividend Yield Check ---
    if analysis.dividend_yield:
        if analysis.dividend_yield < criteria.min_dividend_yield:
            flags.append(f"Low dividend yield: {analysis.dividend_yield:.2f}%")
        elif analysis.dividend_yield > criteria.max_dividend_yield:
            flags.append(f"YIELD TRAP WARNING: {analysis.dividend_yield:.2f}% (unusually high)")
        else:
            score += 2
    else:
        flags.append("No dividend data")

    # --- Payout Ratio Check ---
    if analysis.payout_ratio:
        max_payout = criteria.max_payout_ratio_reit if high_leverage_sector else criteria.max_payout_ratio
        if analysis.payout_ratio > max_payout:
            flags.append(f"High payout ratio: {analysis.payout_ratio:.1f}%")
        elif analysis.payout_ratio > 90:
            flags.append(f"DIVIDEND AT RISK: Payout ratio {analysis.payout_ratio:.1f}%")
        else:
            score += 2

    # --- Dividend Growth Check ---
    if analysis.dividend_growth_5yr:
        if analysis.dividend_growth_5yr > 5:
            score += 2
            if analysis.dividend_growth_5yr > 10:
                score += 1  # Bonus for strong growth
        elif analysis.dividend_growth_5yr < 0:
            flags.append(f"Declining dividends: {analysis.dividend_growth_5yr:.1f}%")

    # --- Interest Coverage Check ---
    if analysis.interest_coverage:
        min_coverage = criteria.min_interest_coverage_reit if high_leverage_sector else criteria.min_interest_coverage
        if analysis.interest_coverage < min_coverage:
            flags.append(f"Low interest coverage: {analysis.interest_coverage:.1f}x")
        else:
            score += 2

    # --- Debt-to-Equity Check ---
    if analysis.debt_to_equity:
        if not high_leverage_sector and analysis.debt_to_equity > criteria.max_debt_to_equity:
            flags.append(f"High debt/equity: {analysis.debt_to_equity:.2f}")
        elif analysis.debt_to_equity < 0.5:
            score += 2  # Strong balance sheet
        else:
            score += 1

    # --- ROIC/ROE Check ---
    if analysis.roic and analysis.roic >= criteria.min_roic:
        score += 2
    elif analysis.roe and analysis.roe >= criteria.min_roe:
        score += 1
    elif analysis.roe and analysis.roe < 10:
        flags.append(f"Low return on equity: {analysis.roe:.1f}%")

    # --- Valuation Check ---
    if analysis.pe_ratio:
        if analysis.pe_ratio > criteria.max_pe_ratio:
            flags.append(f"High P/E ratio: {analysis.pe_ratio:.1f}")
        elif analysis.pe_ratio < 15:
            score += 2  # Attractive valuation
        else:
            score += 1

    # --- Expected Return Check ---
    if analysis.expected_return:
        if analysis.expected_return >= criteria.min_expected_return:
            score += 2
        elif analysis.expected_return >= 6:
            score += 1

    analysis.score = score
    analysis.flags = flags
    analysis.passes_screen = score >= 8 and len([f for f in flags if 'WARNING' in f or 'AT RISK' in f]) == 0

    return analysis


def format_value(value, suffix='', decimal=1):
    """Format a value for display."""
    if value is None:
        return 'N/A'
    return f"{value:.{decimal}f}{suffix}"


def print_analysis(analysis: StockAnalysis, verbose: bool = True):
    """Print formatted analysis results."""

    status = "PASS" if analysis.passes_screen else "REVIEW"
    print(f"\n{'='*60}")
    print(f"{analysis.ticker} - {analysis.name}")
    print(f"Sector: {analysis.sector}")
    print(f"Score: {analysis.score}/15 | Status: {status}")
    print(f"{'='*60}")

    if verbose:
        print("\nDividend Metrics:")
        print(f"  Dividend Yield:     {format_value(analysis.dividend_yield, '%')}")
        print(f"  Payout Ratio:       {format_value(analysis.payout_ratio, '%')}")
        print(f"  5-Year Div Growth:  {format_value(analysis.dividend_growth_5yr, '%')}")

        print("\nBalance Sheet:")
        print(f"  Interest Coverage:  {format_value(analysis.interest_coverage, 'x')}")
        print(f"  Debt/Equity:        {format_value(analysis.debt_to_equity, '', 2)}")
        print(f"  Current Ratio:      {format_value(analysis.current_ratio, '', 2)}")

        print("\nProfitability:")
        print(f"  ROIC (est):         {format_value(analysis.roic, '%')}")
        print(f"  ROE:                {format_value(analysis.roe, '%')}")
        print(f"  Profit Margin:      {format_value(analysis.profit_margin, '%')}")

        print("\nValuation:")
        print(f"  P/E Ratio:          {format_value(analysis.pe_ratio)}")
        print(f"  Forward P/E:        {format_value(analysis.forward_pe)}")
        print(f"  Price/Book:         {format_value(analysis.price_to_book, '', 2)}")

        print(f"\nExpected Return:      {format_value(analysis.expected_return, '%')}")
        print("  (Dividend Yield + Growth Rate)")

    if analysis.flags:
        print("\nFlags/Concerns:")
        for flag in analysis.flags:
            print(f"  - {flag}")


def screen_stocks(tickers: list, criteria: ScreeningCriteria = None, verbose: bool = True) -> pd.DataFrame:
    """Screen multiple stocks and return results as a DataFrame."""

    if criteria is None:
        criteria = ScreeningCriteria()

    results = []

    for ticker in tickers:
        print(f"Analyzing {ticker}...", end=' ', flush=True)
        analysis = get_stock_data(ticker)
        if analysis:
            analysis = screen_stock(analysis, criteria)
            print_analysis(analysis, verbose=verbose)
            results.append({
                'Ticker': analysis.ticker,
                'Name': analysis.name,
                'Sector': analysis.sector,
                'Score': analysis.score,
                'Pass': analysis.passes_screen,
                'Div Yield': analysis.dividend_yield,
                'Payout Ratio': analysis.payout_ratio,
                'Div Growth 5Y': analysis.dividend_growth_5yr,
                'Interest Cov': analysis.interest_coverage,
                'Debt/Equity': analysis.debt_to_equity,
                'ROIC': analysis.roic,
                'ROE': analysis.roe,
                'P/E': analysis.pe_ratio,
                'Expected Return': analysis.expected_return,
                'Flags': '; '.join(analysis.flags) if analysis.flags else ''
            })
        else:
            print("Failed")

    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values('Score', ascending=False)

    return df


# Common dividend aristocrat/king tickers for screening
DIVIDEND_ARISTOCRATS = [
    'JNJ',   # Johnson & Johnson
    'PG',    # Procter & Gamble
    'KO',    # Coca-Cola
    'PEP',   # PepsiCo
    'MMM',   # 3M
    'ABT',   # Abbott Laboratories
    'ABBV',  # AbbVie
    'MCD',   # McDonald's
    'WMT',   # Walmart
    'XOM',   # Exxon Mobil
    'CVX',   # Chevron
    'HD',    # Home Depot
    'LOW',   # Lowe's
    'TGT',   # Target
    'CL',    # Colgate-Palmolive
    'GPC',   # Genuine Parts
    'SWK',   # Stanley Black & Decker
    'EMR',   # Emerson Electric
    'ITW',   # Illinois Tool Works
    'ADP',   # Automatic Data Processing
]

DIVIDEND_KINGS = [
    'PG',    # Procter & Gamble (68+ years)
    'KO',    # Coca-Cola (62+ years)
    'JNJ',   # Johnson & Johnson (62+ years)
    'CL',    # Colgate-Palmolive (61+ years)
    'EMR',   # Emerson Electric (67+ years)
    'MMM',   # 3M (66+ years)
    'GPC',   # Genuine Parts (68+ years)
    'DOV',   # Dover Corporation (69+ years)
    'NWN',   # Northwest Natural (68+ years)
    'PH',    # Parker Hannifin (68+ years)
]


def load_watchlist(filename: str) -> list:
    """Load tickers from a watchlist file.

    File format: One ticker per line. Lines starting with # are treated as comments.
    Blank lines are ignored.

    Example:
        # My favorite dividend stocks
        JNJ
        PG
        KO

        # Tech stocks
        MSFT
        AAPL
    """
    tickers = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip comments and blank lines
                if line and not line.startswith('#'):
                    # Take only the first word (ticker) in case there are inline comments
                    ticker = line.split()[0].upper()
                    tickers.append(ticker)
        print(f"Loaded {len(tickers)} tickers from {filename}")
        return tickers
    except FileNotFoundError:
        print(f"Error: Watchlist file '{filename}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading watchlist file: {e}")
        sys.exit(1)


def save_watchlist(tickers: list, filename: str):
    """Save tickers to a watchlist file."""
    try:
        with open(filename, 'w') as f:
            f.write("# Stock Watchlist\n")
            f.write(f"# Generated on {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for ticker in tickers:
                f.write(f"{ticker}\n")
        print(f"Saved {len(tickers)} tickers to {filename}")
    except Exception as e:
        print(f"Error saving watchlist: {e}")
        sys.exit(1)


def interactive_mode():
    """Interactive mode for non-technical users."""
    import os

    print("\n" + "="*60)
    print("Welcome to the Blue-Chip Dividend Stock Screener!")
    print("="*60)
    print("\nThis tool helps you evaluate dividend stocks based on")
    print("quality metrics like dividend growth, balance sheet strength,")
    print("profitability, and valuation.")

    # Step 1: Choose what to screen
    print("\n" + "-"*60)
    print("STEP 1: Choose what to screen")
    print("-"*60)
    print("\n1. Enter custom stock tickers")
    print("2. Screen Dividend Aristocrats (25+ years of dividend growth)")
    print("3. Screen Dividend Kings (50+ years of dividend growth)")
    print("4. Load from a watchlist file")
    print("5. Exit")

    while True:
        choice = input("\nEnter your choice (1-5): ").strip()
        if choice in ['1', '2', '3', '4', '5']:
            break
        print("Invalid choice. Please enter 1, 2, 3, 4, or 5.")

    if choice == '5':
        print("Goodbye!")
        sys.exit(0)

    tickers = []
    if choice == '1':
        print("\nEnter stock tickers separated by spaces (e.g., JNJ PG KO MSFT):")
        ticker_input = input("Tickers: ").strip().upper()
        if not ticker_input:
            print("No tickers entered. Exiting.")
            sys.exit(0)
        tickers = ticker_input.split()
    elif choice == '2':
        tickers = DIVIDEND_ARISTOCRATS
        print(f"\nScreening {len(tickers)} Dividend Aristocrats")
    elif choice == '3':
        tickers = DIVIDEND_KINGS
        print(f"\nScreening {len(tickers)} Dividend Kings")
    elif choice == '4':
        # List available watchlist files
        watchlists = [f for f in os.listdir('.') if f.endswith('.txt')]
        if watchlists:
            print("\nAvailable watchlist files:")
            for i, wl in enumerate(watchlists, 1):
                print(f"  {i}. {wl}")
            print(f"  {len(watchlists) + 1}. Enter custom filename")

            wl_choice = input(f"\nChoose a file (1-{len(watchlists) + 1}): ").strip()
            try:
                wl_idx = int(wl_choice) - 1
                if 0 <= wl_idx < len(watchlists):
                    filename = watchlists[wl_idx]
                else:
                    filename = input("Enter watchlist filename: ").strip()
            except ValueError:
                filename = input("Enter watchlist filename: ").strip()
        else:
            filename = input("Enter watchlist filename: ").strip()

        if not filename:
            print("No filename entered. Exiting.")
            sys.exit(0)

        tickers = load_watchlist(filename)

    # Step 2: Customize criteria (optional)
    print("\n" + "-"*60)
    print("STEP 2: Screening criteria (optional)")
    print("-"*60)
    print("\nWould you like to customize the screening criteria?")
    print("Default criteria follow Lyn Alden's investment principles.")

    customize = input("Customize? (y/n, default=n): ").strip().lower()

    criteria = ScreeningCriteria()
    if customize == 'y':
        print("\nPress Enter to keep default values:")

        min_yield = input(f"Minimum dividend yield % (default={criteria.min_dividend_yield}): ").strip()
        if min_yield:
            criteria.min_dividend_yield = float(min_yield)

        max_pe = input(f"Maximum P/E ratio (default={criteria.max_pe_ratio}): ").strip()
        if max_pe:
            criteria.max_pe_ratio = float(max_pe)

        min_roic = input(f"Minimum ROIC % (default={criteria.min_roic}): ").strip()
        if min_roic:
            criteria.min_roic = float(min_roic)

    # Step 3: Output options
    print("\n" + "-"*60)
    print("STEP 3: Output options")
    print("-"*60)

    verbose = True
    show_verbose = input("\nShow detailed analysis? (y/n, default=y): ").strip().lower()
    if show_verbose == 'n':
        verbose = False

    export_file = None
    do_export = input("Export results to CSV? (y/n, default=n): ").strip().lower()
    if do_export == 'y':
        export_file = input("Enter filename (e.g., results.csv): ").strip()
        if not export_file:
            export_file = "screener_results.csv"

    save_wl = None
    do_save = input("Save these tickers to a watchlist? (y/n, default=n): ").strip().lower()
    if do_save == 'y':
        save_wl = input("Enter watchlist filename (e.g., my_stocks.txt): ").strip()
        if not save_wl:
            save_wl = "watchlist.txt"

    # Run the screener
    print("\n" + "="*60)
    print("Starting analysis...")
    print("="*60)

    print(f"\nScreening Criteria:")
    print(f"  Min Dividend Yield: {criteria.min_dividend_yield}%")
    print(f"  Max P/E Ratio: {criteria.max_pe_ratio}")
    print(f"  Min ROIC: {criteria.min_roic}%")
    print(f"  Max Payout Ratio: {criteria.max_payout_ratio}%")
    print(f"  Min Interest Coverage: {criteria.min_interest_coverage}x")
    print()

    results = screen_stocks(tickers, criteria, verbose=verbose)

    # Print summary
    if not results.empty:
        print("\n" + "="*60)
        print("SUMMARY - Sorted by Score")
        print("="*60)

        summary_cols = ['Ticker', 'Score', 'Pass', 'Div Yield', 'P/E', 'Expected Return']
        print(results[summary_cols].to_string(index=False))

        passing = results[results['Pass'] == True]
        print(f"\n{len(passing)} of {len(results)} stocks passed the screen")

        if export_file:
            results.to_csv(export_file, index=False)
            print(f"\nResults exported to {export_file}")

    if save_wl:
        save_watchlist(tickers, save_wl)

    print("\n" + "="*60)
    print("Screening complete!")
    print("="*60)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Blue-Chip Dividend Stock Screener based on Lyn Alden principles'
    )
    parser.add_argument(
        'tickers',
        nargs='*',
        help='Stock tickers to analyze (e.g., JNJ PG KO)'
    )
    parser.add_argument(
        '--aristocrats',
        action='store_true',
        help='Screen dividend aristocrats'
    )
    parser.add_argument(
        '--kings',
        action='store_true',
        help='Screen dividend kings'
    )
    parser.add_argument(
        '--min-yield',
        type=float,
        default=1.5,
        help='Minimum dividend yield %% (default: 1.5)'
    )
    parser.add_argument(
        '--max-pe',
        type=float,
        default=25,
        help='Maximum P/E ratio (default: 25)'
    )
    parser.add_argument(
        '--min-roic',
        type=float,
        default=12,
        help='Minimum ROIC %% (default: 12)'
    )
    parser.add_argument(
        '--brief',
        action='store_true',
        help='Show brief output only'
    )
    parser.add_argument(
        '--export',
        type=str,
        help='Export results to CSV file'
    )
    parser.add_argument(
        '--watchlist',
        type=str,
        help='Load tickers from a watchlist file'
    )
    parser.add_argument(
        '--save-watchlist',
        type=str,
        help='Save tickers to a watchlist file'
    )

    args = parser.parse_args()

    # If no arguments provided, launch interactive mode
    if not any([args.tickers, args.aristocrats, args.kings, args.watchlist]):
        interactive_mode()
        sys.exit(0)

    # Determine which tickers to screen
    tickers = []
    if args.watchlist:
        tickers = load_watchlist(args.watchlist)
        print(f"Screening tickers from watchlist: {args.watchlist}")
    elif args.tickers:
        tickers = [t.upper() for t in args.tickers]
    elif args.kings:
        tickers = DIVIDEND_KINGS
        print("Screening Dividend Kings (50+ years of consecutive dividend increases)")
    elif args.aristocrats:
        tickers = DIVIDEND_ARISTOCRATS
        print("Screening Dividend Aristocrats (25+ years of consecutive dividend increases)")

    # Set up criteria
    criteria = ScreeningCriteria(
        min_dividend_yield=args.min_yield,
        max_pe_ratio=args.max_pe,
        min_roic=args.min_roic,
    )

    print(f"\nScreening Criteria:")
    print(f"  Min Dividend Yield: {criteria.min_dividend_yield}%")
    print(f"  Max P/E Ratio: {criteria.max_pe_ratio}")
    print(f"  Min ROIC: {criteria.min_roic}%")
    print(f"  Max Payout Ratio: {criteria.max_payout_ratio}%")
    print(f"  Min Interest Coverage: {criteria.min_interest_coverage}x")
    print()

    # Run the screener
    results = screen_stocks(tickers, criteria, verbose=not args.brief)

    # Print summary
    if not results.empty:
        print("\n" + "="*60)
        print("SUMMARY - Sorted by Score")
        print("="*60)

        summary_cols = ['Ticker', 'Score', 'Pass', 'Div Yield', 'P/E', 'Expected Return']
        print(results[summary_cols].to_string(index=False))

        passing = results[results['Pass'] == True]
        print(f"\n{len(passing)} of {len(results)} stocks passed the screen")

        if args.export:
            results.to_csv(args.export, index=False)
            print(f"\nResults exported to {args.export}")

    # Save watchlist if requested
    if args.save_watchlist:
        save_watchlist(tickers, args.save_watchlist)
