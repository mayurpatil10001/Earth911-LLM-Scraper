# ♻️ Earth911 LLM-Based Recycling Facility Scraper

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--3.5-412991?style=for-the-badge&logo=openai&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-43B02A?style=for-the-badge&logo=selenium&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**An intelligent web scraper that extracts recycling facility data from Earth911, classifies accepted materials using OpenAI GPT, and exports structured JSON output — fully automated with Selenium and BeautifulSoup.**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Output](#-output-format) • [Security](#-security)

</div>

---

## 🌍 Overview

Earth911 LLM Scraper automates the discovery and classification of recycling facilities by combining browser automation (Selenium), HTML parsing (BeautifulSoup), and LLM-powered material classification (OpenAI GPT-3.5). Given a material type, ZIP code, and search radius, the scraper extracts facility details and intelligently maps accepted materials to a predefined set of recycling categories.

Ideal for environmental researchers, waste management platforms, and green-tech applications needing structured recycling data at scale.

---

## ✨ Features

- **Automated Browser Search** — Selenium drives headless Chrome to query Earth911 with custom parameters
- **HTML Parsing** — BeautifulSoup extracts facility names, addresses, and raw materials text
- **LLM Classification** — GPT-3.5 maps raw facility text to structured, predefined material categories
- **Auto ChromeDriver Setup** — `webdriver-manager` handles driver installation automatically
- **JSON Export** — Results saved as timestamped JSON files for downstream use
- **Rate Limiting** — Built-in API call throttling to respect OpenAI rate limits
- **Fallback Handling** — Graceful degradation when selectors or elements are not found

---

## 📦 Material Categories

The scraper classifies facility data into 6 predefined categories:

| Category | Example Items |
|---|---|
| 🖥️ Electronics | Laptops, TVs, Cell Phones, Printers |
| 🔋 Batteries | AA/AAA, Lithium-ion, Car Batteries |
| 🎨 Paint & Chemicals | Latex Paint, Solvents, Pesticides |
| 💉 Medical Sharps | Needles, Lancets, EpiPens |
| 👕 Textiles & Clothing | Clothes, Shoes, Bedding |
| 🔧 Other Materials | Fluorescent Bulbs, Mattresses, Propane Tanks |

---

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Google Chrome browser installed
- OpenAI API key

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/earth911-llm-scraper.git
cd earth911-llm-scraper

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

```txt
requests
beautifulsoup4
selenium
webdriver-manager
openai
dataclasses
```

---

## 🔐 Security

> ⚠️ **NEVER hardcode API keys in your source code.**

Store your OpenAI API key in an environment variable or `.env` file:

```bash
# .env file (add to .gitignore)
OPENAI_API_KEY=your_api_key_here
```

```python
# Load in code
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```

Add a `.gitignore` entry:
```
.env
*.json
logs/
```

If you accidentally committed an API key, **revoke it immediately** at [platform.openai.com/api-keys](https://platform.openai.com/api-keys).

---

## 🚀 Usage

### Basic Run

```bash
python main.py
```

### Configuration

Edit the `SEARCH_CONFIG` dictionary in `main.py`:

```python
SEARCH_CONFIG = {
    "material": "Electronics",   # Material type to search
    "zipcode": "10001",          # Target ZIP code
    "radius": "100",             # Search radius in miles
    "min_results": 3             # Minimum facilities to retrieve
}
```

### Supported Material Search Terms
- `Electronics`
- `Batteries`
- `Paint`
- `Clothing`
- `Sharps`
- `Appliances`

---

## 📋 Output Format

Results are saved as `earth911_facilities_YYYYMMDD_HHMMSS.json`:

```json
[
  {
    "business_name": "GreenDrop Recycling Center",
    "last_update_date": "2025-01-15",
    "street_address": "123 Main St, New York, NY 10001",
    "materials_category": [
      "Electronics",
      "Batteries"
    ],
    "materials_accepted": [
      "Computers, Laptops, Tablets",
      "Cell Phones, Smartphones",
      "Household Batteries (AA, AAA, 9V, etc.)",
      "Rechargeable Batteries"
    ]
  }
]
```

---

## 🏗️ Architecture

```
earth911-llm-scraper/
│
├── main.py                     # Main script & entry point
│
├── Core Classes
│   ├── MaterialsMapping        # Predefined category/item definitions
│   └── Earth911Scraper         # Main scraper class
│
├── Pipeline Steps
│   ├── setup_driver()          # Headless Chrome initialization
│   ├── perform_search()        # Selenium-based form interaction
│   ├── extract_raw_data()      # BeautifulSoup HTML parsing
│   ├── classify_materials_with_llm()  # GPT-3.5 classification
│   └── process_facilities()    # End-to-end facility processing
│
└── requirements.txt
```

### Data Pipeline

```
Search Parameters
      ↓
Selenium (headless Chrome) → Earth911 search
      ↓
BeautifulSoup → Extract raw facility HTML
      ↓
GPT-3.5 → Classify materials into categories
      ↓
Structured JSON → Saved to timestamped file
```

---

## ⚙️ How LLM Classification Works

For each facility, the scraper sends the raw extracted text to GPT-3.5 with a structured prompt:

1. Provides the full predefined categories & items list
2. Sends raw facility text (materials section)
3. GPT returns a conservative JSON classification
4. Only confident matches are included in output

This approach avoids brittle regex-based parsing and handles inconsistent website formatting gracefully.

---

## 📈 Roadmap

- [ ] `.env` support with `python-dotenv` (built-in)
- [ ] Support for multiple ZIP codes in batch mode
- [ ] CSV export option alongside JSON
- [ ] PostgreSQL / SQLite storage backend
- [ ] REST API wrapper for integration
- [ ] Retry logic for failed Selenium interactions
- [ ] Support for additional recycling databases (RecycleNation, iRecycle)

---

## 🤝 Contributing

```bash
# Fork and clone
git clone https://github.com/yourusername/earth911-llm-scraper.git

# Create feature branch
git checkout -b feature/your-feature

# Commit and push
git commit -m "Add: your feature"
git push origin feature/your-feature
```

Please ensure no API keys are present in any commits.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙌 Acknowledgements

- [Earth911](https://earth911.com/) — recycling facility data source
- [OpenAI](https://openai.com/) — GPT-3.5 for intelligent classification
- [Selenium](https://selenium.dev/) — browser automation
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) — HTML parsing

---

<div align="center">
  <b>Built to make recycling data accessible and structured. 🌿</b>
</div>
