# Quick Start Guide

## 🚀 Running the App

### Step 1: Install Dependencies (First time only)

```bash
pip install -r requirements.txt
```

### Step 2: Start the App

**Windows:**
```bash
streamlit run app.py
```

**Or use the batch file:**
```bash
START_APP.bat
```

**Linux/Mac:**
```bash
streamlit run app.py
```

**Or use the shell script:**
```bash
chmod +x START_APP.sh
./START_APP.sh
```

### Step 3: Access the Dashboard

The app will automatically open in your browser at:
- **http://localhost:8501**

If it doesn't open automatically, manually navigate to that URL.

---

## 📋 What the App Does

1. **View Properties**: Browse all auction properties in the database
2. **Scrape New Data**: Fetch new auction listings from eauctionsindia.com
3. **Calculate Market Rates**: Use AI to get market rates and calculate discounts
4. **Filter & Search**: Filter properties by city and bank
5. **Export Data**: Download all data as CSV

---

## 🛠️ Common Commands

### Run App
```bash
streamlit run app.py
```

### Run on Different Port
```bash
streamlit run app.py --server.port 8502
```

### Run Scraper Only (in terminal)
```bash
python pune_auction_scraper.py --pages 3
```

### Check Database
```bash
python verify_db.py
```

---

## ⚠️ Troubleshooting

### Port Already in Use
```bash
# Windows: Find process on port 8501
netstat -ano | findstr :8501

# Kill the process (replace <PID> with actual process ID)
taskkill /PID <PID> /F
```

### Missing Packages
```bash
pip install streamlit pandas requests beautifulsoup4 lxml
```

### Database Not Found
Run the scraper first to create the database:
```bash
python pune_auction_scraper.py --pages 1
```

---

## 📁 Important Files

- `app.py` - Main Streamlit application
- `pune_auction_scraper.py` - Web scraper with API integration
- `auctions.db` - SQLite database (created automatically)
- `property_enriched_data.json` - Cache for market rate calculations

---

## 🔑 API Keys

The app uses Gemini API keys for market rate calculations. Keys are configured in `pune_auction_scraper.py`:
- Primary key (first)
- Fallback key (second, used if first fails)

