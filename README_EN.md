# Crypto Smart Money Monitor 🚀

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GUI](https://img.shields.io/badge/GUI-Tkinter-orange.svg)](https://docs.python.org/3/library/tkinter.html)
[![Language](https://img.shields.io/badge/language-中文%20%7C%20English-yellow.svg)]()

> A real-time cryptocurrency market monitoring system that tracks whale positions on Hyperliquid and visualizes OKX perpetual futures data. Built in **days** with AI-assisted development, showcasing rapid prototyping and multi-source data integration.

**👨‍💻 Author**: Howard Zeng
English | [中文](README.md)

---

## 📌 Project Highlights

- **🤖 AI-Assisted Development**: Built production-ready app in days using Claude Code
- **📊 Multi-Source Integration**: Combines Hyperliquid whale tracking + OKX real-time market data
- **🎨 Professional UI/UX**: Dark-themed DeFi-style interface with real-time visualization
- **🌐 Bilingual Support**: Complete Chinese-English interface switching, 95%+ UI coverage
- **🔄 Real-Time Monitoring**: Auto-refresh market data with customizable intervals
- **📈 Advanced Visualization**: Heatmaps, sentiment analysis, and top movers dashboard

---

## 🎯 Key Features

### 🐋 Hyperliquid Whale Tracker
- Monitor large positions on Hyperliquid platform via web scraping (Selenium)
- One-click data refresh and Excel export
- Multi-dimensional filtering (symbol, time, amount)
- Clean table view with position details
- Double-click to view whale details (PnL stats, positions, trade history)

### 📊 OKX Market Analytics
- **Real-Time Data Table**: Top 50 perpetual futures with auto-refresh (10s interval)
- **Market Cap Heatmap**: TOP 20 tokens visualized by volume and price change
- **Sentiment Analysis**: Market overview with bull/bear statistics
- **Top Movers**: Gainers and losers leaderboard (TOP 10)

### 🌐 Multilingual Interface
- **Chinese-English Switching**: One-click language toggle, no restart required
- **95%+ Coverage**: Almost all UI elements support translation
- **Real-Time Updates**: Includes main interface, filter panels, table columns, detail windows
- **Professional Terms**: Accurate financial terminology translation

### 🎨 User Interface
- Professional dark theme (DeFi-inspired design)
- Responsive layout with tabbed navigation
- Color-coded profit/loss indicators
- Optimized for high-frequency data updates

---

## 🛠️ Tech Stack

| Category | Technologies |
|----------|-------------|
| **Language** | Python 3.8+ |
| **GUI Framework** | Tkinter + ttk (Modern themed widgets) |
| **Web Scraping** | Selenium WebDriver + ChromeDriver |
| **API Integration** | OKX Public API (REST) |
| **Data Visualization** | Matplotlib + Squarify (Treemap) |
| **Data Processing** | NumPy, Pandas-like operations |
| **HTTP Client** | Requests library |
| **Internationalization** | Custom language management system (Observer pattern) |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Internet connection (for API access)
- Chrome browser (for web scraping)
- Windows/Linux/macOS

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/zengh430/crypto-smart-money-monitor.git
cd crypto-smart-money-monitor
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

Or use the provided batch script (Windows):
```bash
安装依赖.bat
```

3. **Run the application**
```bash
python hyperliquid_monitor.py
```

Or use the quick-start script (Windows):
```bash
快速启动.bat
```

---

## 📖 User Guide

### Hyperliquid Monitoring
1. Launch the app and switch to **"Raw Data"** or **"Position Data"** tab
2. Click **"Refresh"** to fetch the latest whale positions
3. Use left sidebar filters to filter by symbol/time/amount
4. **Double-click any row** to view whale details:
   - Total PnL, 24h/48h/7d/30d PnL statistics
   - PnL trend charts
   - Current position details
   - Historical trade records
   - Deposit/withdrawal records
5. Export data to Excel for further analysis

### OKX Market Monitoring
1. **Data Table Tab**:
   - Click "Refresh" to fetch TOP 50 token prices
   - Enable "Auto Refresh" for 10-second updates
   - Sort by volume, price change, or market cap

2. **Heatmap Tab**:
   - Visualize TOP 20 tokens as a treemap
   - Square size = trading volume
   - Color = price change (green=gain, red=loss)

3. **Market Analysis Tab**:
   - View overall market sentiment
   - Check TOP 10 gainers and losers
   - Monitor bull/bear distribution

### Language Switching
- Click the **🌐 English** button in top-right corner to switch to English
- Click **🌐 中文** button to switch back to Chinese
- All interface elements update in real-time, no restart required

---

## 🏗️ Project Structure

```
crypto-smart-money-monitor/
├── hyperliquid_monitor.py    # Main application (GUI + Hyperliquid scraper)
├── language_config.py         # Language configuration and management
├── okx_trader.py              # OKX API client module
├── config_example.py          # Configuration template
├── okx_config.example.json    # OKX configuration example
├── requirements.txt           # Python dependencies
├── .gitignore                 # Git ignore rules
├── README.md                  # Chinese documentation
├── README_EN.md               # English documentation (this file)
├── 安装依赖.bat                # Windows dependency installation script
└── 快速启动.bat                # Windows quick start script
```

---

## ⚙️ Configuration

Copy `config_example.py` to `config.py` and customize:

```python
# Refresh intervals
OKX_AUTO_REFRESH_INTERVAL = 10  # seconds
HYPERLIQUID_REFRESH_INTERVAL = 30  # seconds

# Theme
THEME = "dark"  # "dark" or "light"

# Monitored coins
MONITORED_COINS = ["BTC", "ETH", "SOL", ...]  # Custom monitoring list

# Default language
DEFAULT_LANGUAGE = "zh"  # "zh" for Chinese, "en" for English
```

**OKX API Configuration** (Optional):
- Copy `okx_config.example.json` to `okx_config.json`
- Fill in your API keys if you need private API features
- Public data features work without API keys

---

## 🔧 API Reference

### OKX Public API
- **Base URL**: `https://www.okx.com`
- **Rate Limit**: 20 requests / 2 seconds
- **No API key required** (for public endpoints)
- **Documentation**: [OKX API Docs](https://www.okx.com/docs-v5/en/)

### Hyperliquid Data
- **Source**: CoinGlass via Selenium web scraping
- **Update Frequency**: Manual or scheduled refresh
- **Data Points**: Position size, entry price, PnL, timestamp, trade history

---

## 🌟 Technical Achievements

### 1. **AI-Assisted Rapid Development**
- Built production-ready app in **days** using AI-assisted programming (Claude Code)
- Demonstrated 10x+ productivity boost
- Rapid prototyping to production-grade code

### 2. **Multi-Source Data Integration**
- Seamlessly combines web scraping (Hyperliquid) and REST API (OKX)
- Handles asynchronous data updates and rate limiting
- Intelligent error handling and auto-retry mechanisms

### 3. **Real-Time Data Visualization**
- Custom Matplotlib integration with Tkinter
- Efficient redrawing for smooth updates
- Responsive heatmap generation

### 4. **Internationalization Architecture**
- Observer pattern for language switching
- 150+ UI elements fully translated
- Real-time interface updates without restart

### 5. **Robust Error Handling**
- Graceful API failure recovery
- User-friendly error messages
- Auto-retry mechanisms

---

## 🎓 Learning Outcomes

This project demonstrates proficiency in:

- **Web Scraping**: Selenium automation, dynamic content handling, anti-bot techniques
- **API Integration**: RESTful API calls, rate limiting, error handling
- **GUI Development**: Tkinter event loop, multi-threading, responsive design
- **Data Visualization**: Custom Matplotlib charts, real-time updates
- **Software Architecture**: MVC pattern, Observer pattern, Singleton pattern
- **Internationalization**: i18n implementation, language management system
- **FinTech**: Cryptocurrency market data, trading metrics
- **Software Engineering**: Code organization, configuration management, documentation

---

## 🚀 Future Enhancements

- [ ] Add more exchanges (Binance, Bybit, etc.)
- [ ] Implement custom alerts and notifications
- [ ] Portfolio tracking and performance analytics
- [ ] Export to multiple formats (CSV, JSON, SQL)
- [ ] Add trading strategy backtesting module
- [ ] More language support (Japanese, Korean, etc.)
- [ ] Dark/Light theme toggle
- [ ] Web dashboard (Flask/FastAPI + React)
- [ ] Docker deployment support
- [ ] Unit tests and CI/CD pipeline

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **OKX** for providing public API access
- **Hyperliquid** for market data
- **CoinGlass** for data aggregation services
- **Claude Code** (Anthropic) for AI-assisted development
- Open-source community for libraries and tools

---

## 📬 Contact

- **Author**: Howard Zeng
- **GitHub**: [@zengh430](https://github.com/zengh430)
- **LinkedIn**: [Howard Zeng](https://www.linkedin.com/in/hao-zeng2024/)
- **Email**: zengh430@gmai.com

---

## ⚠️ Disclaimer

This software is **for educational and research purposes only**. This is not financial advice. Cryptocurrency trading involves significant risks. Always do your own research (DYOR) and consult with financial professionals before making investment decisions.

The author is not responsible for any losses incurred from using this software.

---

<p align="center">
  <strong>Built with AI-Assisted Development ❤️ | Days instead of months</strong><br>
  <em>Built with Claude Code by Howard Zeng</em>
</p>
