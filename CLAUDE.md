# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Inky Stocks is a stock ticker display for the Raspberry Pi Zero & Pimoroni Inky pHAT e-ink display. It fetches daily stock performance from Yahoo Finance and renders it as a compact graph with price information. Optionally supports LED SHIM for visual up/down indicators.

## Development Setup

This project is designed to run on Raspberry Pi Zero hardware, but can be developed/tested locally without the display hardware.

1. Activate Python virtual environment:
   ```bash
   source ~/.virtualenvs/pimoroni/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

Basic usage (defaults to S&P 500):
```bash
python stocks.py
```

With a specific symbol:
```bash
python stocks.py --symbol AAPL
python stocks.py --symbol ^FTSE
python stocks.py --symbol BTC-USD
```

For three-color (black/white/red) displays:
```bash
python stocks.py --symbol AAPL --three-color
```

When running without Inky pHAT hardware, the script saves output to `inky_stocks.png` instead of displaying.

## Code Architecture

### Core Components

**stocks.py** - Main application with the following key functions:

- `fetch_market_data(symbol)`: Fetches 15-minute interval data from Yahoo Finance using yfinance. Handles market timing logic - if market opened <2 hours ago, shows previous day. Returns dict with name, times, prices, and latest_day_index.

- `plot_graph(prices, latest_day_index)`: Uses matplotlib to generate the price chart (185x80px). Handles three-color mode by drawing red segments for prices below starting price. Anti-aliasing is disabled for crisp e-ink rendering. Includes dashed vertical line to separate previous day from current day.

- `create_display_image(symbol, market_data)`: Composes the final 250x122px image. Layout is graph on left (185x80), with three 40px-tall info columns on right (65px wide): title/symbol at top, trend arrow, percentage change, and current price.

- `display_on_inky(image)`: Quantizes the image to a 3-color palette (white/black/red) and sends to the Inky pHAT display.

- `set_lights(market_data)`: Controls optional LED SHIM - green for gains, red for losses.

**reset_leds.py** - Utility to turn off the LED SHIM.

### Key Implementation Details

- Display resolution is hardcoded to 250x122 (current Inky pHAT specification)
- Font is Roboto-Bold.ttf from `fonts/` directory
- Uses global `Config` object for three-color mode flag
- Hardware detection via try/except imports - gracefully degrades without inky/ledshim libraries
- Market data logic: fetches 4 days to cover weekends, uses 15-minute intervals
- If latest trading day has ≤8 data points, includes 16 points from previous day for context

## Hardware Dependencies

The code handles missing hardware gracefully:
- Without Inky pHAT library: saves PNG locally instead of displaying
- Without LED SHIM library: skips LED functionality

When deployed on Raspberry Pi, requires:
- Pimoroni Inky pHAT (250x122 resolution)
- Optional: Pimoroni LED SHIM
