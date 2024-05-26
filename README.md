# Trading Algorithm

## Description

This project is a trading algorithm developed in Python, utilizing the Binance API for cryptocurrency futures trading. The algorithm analyzes market data and executes trades based on predefined strategies.

## Installation

To set up the project locally, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/Froiod/crypto-trading-algo.git
   ```
2. Navigate to the project directory:
   ```bash
   cd crypto-trading-algo
   ```
3. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
4. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

To use the trading algorithm, you'll need to set up your Binance Futures API keys and run the script.

1. Open the script and define your API keys:
   ```python
   api_key = "your_api_key"
   api_secret = "your_api_secret"
   ```
2. Run the script:
   ```bash
   python trading_algo.py
   ```
