# Blue-Chip Dividend Stock Screener

A Python-based stock screener that evaluates dividend stocks using the investment principles outlined in [Lyn Alden's guide to blue-chip dividend stocks](https://www.lynalden.com/blue-chip-dividend-stocks/).

## Overview

This screener analyzes stocks across multiple dimensions to identify quality dividend investments:

- **Dividend Quality** - Yield, payout ratio sustainability, and growth history
- **Balance Sheet Strength** - Interest coverage and debt levels
- **Profitability** - Return on invested capital (ROIC) and return on equity (ROE)
- **Valuation** - P/E ratio and expected total return

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/stock_screener.git
cd stock_screener

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Easy Launch (Recommended for Non-Technical Users)

Simply run the launcher script for your operating system:

**On Mac/Linux:**
```bash
./screen.sh
```

**On Windows:**
```
Double-click screen.bat
```

This will start an interactive mode that guides you through the entire process with simple prompts. No command-line knowledge required!

### Interactive Mode

Run without any arguments to enter interactive mode:

```bash
python screener.py
```

You'll be guided through:
1. Choosing what to screen (custom tickers, Aristocrats, Kings, or watchlist)
2. Optionally customizing screening criteria
3. Selecting output options (detailed/brief, CSV export, save watchlist)

### Screen Specific Stocks

```bash
python screener.py JNJ PG KO MSFT AAPL
```

### Screen Pre-defined Lists

```bash
# Dividend Aristocrats (25+ years of consecutive dividend increases)
python screener.py --aristocrats

# Dividend Kings (50+ years of consecutive dividend increases)
python screener.py --kings
```

### Custom Watchlists

Create and manage your own custom stock lists:

```bash
# Create a watchlist file (one ticker per line)
cat > my_stocks.txt << EOF
# My favorite dividend stocks
JNJ
PG
KO
MSFT
EOF

# Screen stocks from a watchlist
python screener.py --watchlist my_stocks.txt

# Save tickers to a watchlist for later use
python screener.py JNJ PG KO --save-watchlist healthcare.txt
```

### Customize Screening Criteria

```bash
python screener.py --min-yield 2.0 --max-pe 20 --min-roic 15 JNJ PG KO
```

### Output Options

```bash
# Brief output (summary only)
python screener.py --aristocrats --brief

# Export results to CSV
python screener.py --aristocrats --export results.csv
```

## Screening Criteria

Based on Lyn Alden's framework, stocks are evaluated on:

| Category | Metric | Default Threshold |
|----------|--------|-------------------|
| **Dividend** | Yield | 1.5% - 8% |
| | Payout Ratio | < 50% (< 85% for REITs) |
| | 5-Year Growth | Positive |
| **Balance Sheet** | Interest Coverage | > 10x (> 4x for REITs) |
| | Debt/Equity | < 1.0 |
| **Profitability** | ROIC | > 12% |
| | ROE | > 15% |
| **Valuation** | P/E Ratio | < 25 |
| | Expected Return | > 8% |

### Scoring System

Each stock receives a score out of 15 points based on how well it meets the criteria:

- **Score 8+**: Passes the screen (marked as "PASS")
- **Score < 8**: Requires further review (marked as "REVIEW")

Stocks with critical flags (yield traps, dividends at risk) automatically fail regardless of score.

### Red Flags

The screener identifies potential problems:

- **YIELD TRAP WARNING**: Unusually high yields (> 8%) often signal distress
- **DIVIDEND AT RISK**: Payout ratios approaching 100%
- **High debt/equity**: Overleveraged balance sheet
- **Low interest coverage**: May struggle to service debt

## Example Output

```
============================================================
JNJ - Johnson & Johnson
Sector: Healthcare
Score: 10/15 | Status: PASS
============================================================

Dividend Metrics:
  Dividend Yield:     2.5%
  Payout Ratio:       49.1%
  5-Year Div Growth:  4.2%

Balance Sheet:
  Interest Coverage:  23.1x
  Debt/Equity:        0.58
  Current Ratio:      1.07

Profitability:
  ROIC (est):         10.4%
  ROE:                33.6%
  Profit Margin:      27.3%

Valuation:
  P/E Ratio:          20.0
  Forward P/E:        18.2
  Price/Book:         6.37

Expected Return:      6.7%
  (Dividend Yield + Growth Rate)
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `tickers` | Stock ticker symbols to analyze |
| `--aristocrats` | Screen dividend aristocrats list |
| `--kings` | Screen dividend kings list |
| `--watchlist FILE` | Load tickers from a watchlist file |
| `--save-watchlist FILE` | Save tickers to a watchlist file |
| `--min-yield` | Minimum dividend yield % (default: 1.5) |
| `--max-pe` | Maximum P/E ratio (default: 25) |
| `--min-roic` | Minimum ROIC % (default: 12) |
| `--brief` | Show condensed output |
| `--export FILE` | Export results to CSV file |

## Data Source

Stock data is fetched from Yahoo Finance via the [yfinance](https://github.com/ranaroussi/yfinance) library.

## Limitations

- ROIC is estimated from available data (ROA adjusted for leverage)
- Historical dividend data may be incomplete for some stocks
- Data accuracy depends on Yahoo Finance
- This is a screening tool, not investment advice

## License

MIT License

## Disclaimer

This tool is for informational and educational purposes only. It does not constitute investment advice. Always conduct your own research and consider consulting a financial advisor before making investment decisions.
