# How to Run the Pune Auction Dashboard App

## Prerequisites

Make sure you have Python installed and the required packages:

```bash
pip install streamlit pandas requests beautifulsoup4
```

## Running the App

### Basic Command

Open your terminal/command prompt in the project directory and run:

```bash
streamlit run app.py
```

### Alternative: Specify Port

If port 8501 is already in use, specify a different port:

```bash
streamlit run app.py --server.port 8502
```

### Access the App

Once started, the app will automatically open in your default web browser at:
- **Default URL**: http://localhost:8501
- If you used a different port: http://localhost:YOUR_PORT

### Stopping the App

Press `Ctrl+C` in the terminal to stop the server.

## App Features

### Sidebar Controls

1. **Run Scraper**
   - Set number of pages to scrape
   - Click "🔄 Run Scraper" to fetch new auction data

2. **Market Rate & Discount Calculation**
   - **🔄 Calculate All**: Calculate market rates for properties missing them
   - **♻️ Force Recalc**: Recalculate all properties (can take a long time)

3. **Export Data**
   - Download all data as CSV file

### Main Dashboard

- View all auction properties in a table
- Filter by City and Bank
- View detailed property information
- See market rates and discount percentages

## File Structure

```
Auction/
├── app.py                    # Main Streamlit application
├── pune_auction_scraper.py   # Scraper script with API integration
├── auctions.db               # SQLite database
├── property_enriched_data.json  # Cache for market rate data
└── requirements.txt          # (Optional) Python dependencies
```

## Troubleshooting

### Port Already in Use

```bash
# Find and kill the process using port 8501
# Windows:
netstat -ano | findstr :8501
taskkill /PID <PID> /F

# Then run the app again
streamlit run app.py
```

### Database Not Found

Make sure `auctions.db` exists. If not, run the scraper first:
```bash
python pune_auction_scraper.py --pages 1
```

### API Key Issues

The app uses Gemini API keys defined in `pune_auction_scraper.py`. Make sure they are valid.

## Quick Start Example

```bash
# 1. Navigate to project directory
cd C:\Users\bioyo\OneDrive\Desktop\Roshan\Auction

# 2. Run the app
streamlit run app.py

# 3. Open browser to http://localhost:8501
# 4. Use the sidebar to scrape data or calculate market rates
```

## Command Line Options

Streamlit supports various command-line options:

```bash
# Run on different port
streamlit run app.py --server.port 8502

# Run without opening browser automatically
streamlit run app.py --server.headless true

# Specify config file
streamlit run app.py --config.file config.toml
```

## Environment

- **OS**: Windows 10
- **Python**: 3.x
- **Framework**: Streamlit
- **Database**: SQLite (auctions.db)

