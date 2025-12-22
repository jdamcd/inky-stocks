# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Inky Stocks is a stock ticker display for the Raspberry Pi Zero & Pimoroni Inky displays (both pHAT and wHAT). It fetches daily stock performance from Yahoo Finance and renders it as a compact graph with price information. Supports displaying 1 stock on pHAT (250x122) or up to 3 stocks on wHAT (400x300). Optionally supports LED SHIM for visual up/down indicators on pHAT displays only.

## Development Setup

This project is designed to run on Raspberry Pi Zero hardware, but can be developed/tested locally without the display hardware.

1. Activate Python virtual environment:
   ```bash
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Auto-detecting Entry Point

The main script automatically detects which display is connected:

```bash
python stocks.py
# pHAT: Shows ^GSPC (S&P 500)
# wHAT: Shows ^GSPC, ^FTSE, BTC-USD
```

### Display-Specific Scripts

Run the display-specific scripts directly (saves to PNG if no hardware detected):

```bash
# pHAT display (250x122, single stock)
python stocks_phat.py --symbol AAPL
python stocks_phat.py --symbol ^GSPC --three-color

# wHAT display (400x300, up to 3 stocks)
python stocks_what.py --symbols AAPL MSFT GOOGL
python stocks_what.py --symbol ^GSPC  # Single stock on wHAT
```

### Common Options

Single stock:
```bash
python stocks.py --symbol AAPL
python stocks.py --symbol ^FTSE
python stocks.py --symbol BTC-USD
```

Multiple stocks (wHAT only, 1-3 stocks):
```bash
python stocks.py --symbols AAPL MSFT GOOGL
python stocks.py --symbols ^GSPC ^FTSE BTC-USD
```

Three-color (black/white/red) displays:
```bash
python stocks.py --symbol AAPL --three-color
python stocks.py --symbols AAPL MSFT GOOGL --three-color
```

When running without Inky hardware, scripts save output to `inky_stocks_phat.png` or `inky_stocks_what.png`.

## Code Architecture

### File Structure

```
stocks_common.py  - Shared functionality (data fetching, graphing, utilities)
stocks_phat.py    - pHAT-specific display logic (250x122, single stock, LED SHIM)
stocks_what.py    - wHAT-specific display logic (400x300, up to 3 stocks)
stocks.py         - Auto-detecting entry point (delegates to pHAT or wHAT script)
reset_leds.py     - Utility to turn off the LED SHIM
```

### stocks_common.py - Shared Module

**Configuration:**
- `Config`: Global config object holding `three_color` flag
- `FONT_PATH`: Path to Roboto-Bold.ttf font

**Data Fetching:**
- `fetch_market_data(symbol)`: Fetches 15-minute interval data from Yahoo Finance. Returns prepared dict with name, times, prices, latest_day_index, is_up, first_price, last_price.
- `fetch_multiple(symbols)`: Fetches data for multiple symbols, handling errors gracefully. Returns list of dicts with symbol, data, and error keys.

**Rendering:**
- `plot_graph(prices, latest_day_index, graph_width, graph_height, three_color)`: Uses matplotlib to generate price chart. Handles three-color mode by drawing red segments for prices below starting price.
- `load_font(size)`: Loads Roboto Bold font at specified size with fallback to default.
- `display_on_inky(image)`: Quantizes image to 3-color palette and sends to Inky display.

### stocks_phat.py - pHAT Display (250x122)

**Layout:**
- Graph on left (185x80)
- Vertical info panel on right (65px wide): arrow, percentage, price

**Functions:**
- `create_display_image(symbol, market_data)`: Creates full pHAT display image
- `set_lights(market_data)`: Controls LED SHIM (green for gains, red for losses)
- Drawing functions: `draw_title`, `draw_trend_arrow`, `draw_percentage_change`, `draw_price`

### stocks_what.py - wHAT Display (400x300)

**Layout:**
- 3 stock rows (99px each with 1px divider lines)
- Each row has 12px internal padding
- Left side: title, arrow with % change and price
- Right side: graph (150x75)

**Functions:**
- `create_display_image(stock_results)`: Composes final image from stock rows
- `create_stock_row(symbol, market_data)`: Creates single row image
- Drawing functions: `draw_title`, `draw_trend_arrow`, `draw_percentage_change`, `draw_price`

### stocks.py - Auto-detecting Entry Point

- `detect_display_type()`: Detects pHAT or wHAT via inky.auto()
- Parses CLI arguments and delegates to appropriate display script

### Key Implementation Details

**Market Data Logic:**
- Fetches 4 days to cover weekends, uses 15-minute intervals
- If latest trading day has ≤8 data points, includes 16 points from previous day for context

**Hardware Handling:**
- Hardware detection via try/except imports - gracefully degrades without inky/ledshim libraries
- Without Inky library: saves PNG locally instead of displaying
- Without LED SHIM library: skips LED functionality

**Font:**
- Uses Roboto-Bold.ttf from `fonts/` directory

## Hardware Dependencies

When deployed on Raspberry Pi, supports:
- Pimoroni Inky pHAT (250x122 resolution) - displays 1 stock
- Pimoroni Inky wHAT (400x300 resolution) - displays up to 3 stocks
- Optional: Pimoroni LED SHIM (pHAT only)
