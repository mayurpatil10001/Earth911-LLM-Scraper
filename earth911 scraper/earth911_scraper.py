#!/usr/bin/env python3
"""
Earth911 LLM-Based Recycling Facility Scraper
Extracts and classifies recycling facility data using OpenAI GPT models
Author: AI Assistant
Date: 2025
"""

import requests
import json
import re
import time
import subprocess
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import openai
from dataclasses import dataclass

# Auto-install webdriver-manager if not present
def install_webdriver_manager():
    """Install webdriver-manager if not already installed"""
    try:
        import webdriver_manager
        print("✅ webdriver_manager already installed")
    except ImportError:
        print("📦 Installing webdriver-manager...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "webdriver-manager"])
        print("✅ webdriver_manager installed successfully")

install_webdriver_manager()

from webdriver_manager.chrome import ChromeDriverManager

@dataclass
class MaterialsMapping:
    """Predefined materials categories and accepted items for LLM classification"""
    
    CATEGORIES = {
        "Electronics": [
            "Computers, Laptops, Tablets",
            "Monitors, TVs (CRT & Flat Screen)",
            "Cell Phones, Smartphones", 
            "Printers, Copiers, Fax Machines",
            "Audio/Video Equipment",
            "Gaming Consoles",
            "Small Appliances (Microwaves, Toasters, etc.)",
            "Computer Peripherals (Keyboards, Mice, Cables, etc.)"
        ],
        "Batteries": [
            "Household Batteries (AA, AAA, 9V, etc.)",
            "Rechargeable Batteries",
            "Lithium-ion Batteries",
            "Button/Watch Batteries",
            "Power Tool Batteries",
            "E-bike/Scooter Batteries",
            "Car/Automotive Batteries"
        ],
        "Paint & Chemicals": [
            "Latex/Water-based Paint",
            "Oil-based Paint and Stains",
            "Spray Paint",
            "Paint Thinners and Solvents",
            "Household Cleaners",
            "Pool Chemicals",
            "Pesticides and Herbicides",
            "Automotive Fluids (Oil, Antifreeze)"
        ],
        "Medical Sharps": [
            "Needles and Syringes",
            "Lancets",
            "Auto-injectors (EpiPens)",
            "Insulin Pens",
            "Home Dialysis Equipment"
        ],
        "Textiles & Clothing": [
            "Clothing and Shoes",
            "Household Textiles (Towels, Bedding)",
            "Fabric Scraps",
            "Accessories (Belts, Bags, etc.)"
        ],
        "Other Important Materials": [
            "Fluorescent Bulbs and CFLs",
            "Mercury Thermometers",
            "Smoke Detectors",
            "Fire Extinguishers",
            "Propane Tanks",
            "Mattresses and Box Springs",
            "Large Appliances (Fridges, Washers, etc.)",
            "Construction Debris (Residential Quantities)"
        ]
    }


class Earth911Scraper:
    """LLM-powered scraper for Earth911 recycling facility data"""
    
    def __init__(self, openai_api_key: str):
        """Initialize scraper with OpenAI API key"""
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.materials_mapping = MaterialsMapping()
        self.base_url = "https://search.earth911.com/"
        
    def setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome WebDriver with automatic ChromeDriver download"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        try:
            print("🔄 Setting up ChromeDriver automatically...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("✅ Chrome WebDriver initialized successfully")
            return driver
        except Exception as e:
            print(f"❌ Error setting up WebDriver: {str(e)}")
            print("🔧 Trying fallback method...")
            
            # Fallback: try without service
            try:
                driver = webdriver.Chrome(options=chrome_options)
                print("✅ Chrome WebDriver initialized with fallback method")
                return driver
            except Exception as e2:
                print(f"❌ Fallback also failed: {str(e2)}")
                raise Exception("ChromeDriver setup failed. Please install Chrome browser and try again.")
    
    def perform_search(self, driver: webdriver.Chrome, material: str = "Electronics", 
                      zipcode: str = "10001", radius: str = "100") -> bool:
        """Perform search on Earth911 website"""
        try:
            print(f"🌐 Navigating to {self.base_url}")
            driver.get(self.base_url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            print("✅ Page loaded successfully")
            
            # Find and interact with search elements
            
            # Enter material search
            try:
                print(f"🔍 Searching for material: {material}")
                material_input = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 
                        "input[placeholder*='material'], input[name*='material'], #material-search, input[type='search']"))
                )
                material_input.clear()
                material_input.send_keys(material)
                time.sleep(1)
                print("✅ Material entered successfully")
            except TimeoutException:
                print("❌ Could not find material input field")
                return False
            
            # Enter zipcode
            try:
                print(f"📍 Entering zipcode: {zipcode}")
                zip_input = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 
                        "input[placeholder*='zip'], input[name*='zip'], #zip-search, input[maxlength='5']"))
                )
                zip_input.clear()
                zip_input.send_keys(zipcode)
                time.sleep(1)
                print("✅ Zipcode entered successfully")
            except TimeoutException:
                print("❌ Could not find zipcode input field")
                return False
            
            # Set radius (if dropdown available)
            try:
                print(f"📏 Setting radius: Within {radius} miles")
                radius_select = driver.find_element(By.CSS_SELECTOR, 
                    "select[name*='radius'], #radius-select, select[name*='distance']")
                radius_select.send_keys(f"Within {radius} miles")
                time.sleep(1)
                print("✅ Radius set successfully")
            except NoSuchElementException:
                print("⚠️ Radius selector not found, continuing with default...")
            
            # Click search button
            try:
                print("🔍 Clicking search button...")
                search_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 
                        "button[type='submit'], input[type='submit'], .search-button, button:contains('Search')"))
                )
                search_button.click()
                time.sleep(3)
                print("✅ Search executed successfully")
            except TimeoutException:
                print("❌ Could not find search button")
                return False
            
            # Wait for results to load
            print("⏳ Waiting for search results...")
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 
                    ".result, .facility, .location, [class*='result'], [class*='listing']"))
            )
            print("✅ Search results loaded successfully")
            
            return True
            
        except Exception as e:
            print(f"❌ Error performing search: {str(e)}")
            return False
    
    def extract_raw_data(self, driver: webdriver.Chrome) -> List[Dict[str, Any]]:
        """Extract raw facility data from search results"""
        facilities = []
        
        try:
            print("📄 Getting page source and parsing with BeautifulSoup...")
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Find facility containers
            print("🔍 Looking for facility containers...")
            facility_containers = soup.find_all(['div', 'li', 'article'], 
                                              class_=re.compile(r'result|facility|location|listing', re.I))
            
            if not facility_containers:
                print("⚠️ No facility containers found with standard selectors, trying fallback...")
                facility_containers = soup.find_all(['div', 'li'], 
                                                  string=re.compile(r'address|phone|hours|materials', re.I))
            
            print(f"📊 Found {len(facility_containers)} potential facility containers")
            
            for i, container in enumerate(facility_containers[:10]):  # Limit to first 10 results
                try:
                    print(f"🏢 Processing facility container {i+1}...")
                    facility_data = self.parse_facility_container(container)
                    if facility_data:
                        facilities.append(facility_data)
                        print(f"✅ Extracted facility {i+1}: {facility_data.get('business_name', 'Unknown')}")
                    else:
                        print(f"⚠️ No valid data found in container {i+1}")
                except Exception as e:
                    print(f"❌ Error parsing facility container {i+1}: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"❌ Error extracting raw data: {str(e)}")
        
        print(f"📈 Total facilities extracted: {len(facilities)}")
        return facilities
    
    def parse_facility_container(self, container) -> Optional[Dict[str, Any]]:
        """Parse individual facility container to extract basic info"""
        facility = {}
        
        try:
            # Extract business name
            name_elem = container.find(['h1', 'h2', 'h3', 'h4', 'strong', 'b'], 
                                     class_=re.compile(r'name|title|business', re.I))
            if not name_elem:
                name_elem = container.find(['div', 'span'], 
                                         class_=re.compile(r'name|title|business', re.I))
            
            if name_elem:
                facility['business_name'] = name_elem.get_text(strip=True)
            
            # Extract address
            address_elem = container.find(['div', 'span', 'p'], 
                                        class_=re.compile(r'address|location', re.I))
            if not address_elem:
                # Look for address patterns in text
                text_content = container.get_text()
                address_pattern = r'\d+\s+[A-Za-z\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln)[,\s]+[A-Za-z\s]+,?\s+[A-Z]{2}\s+\d{5}'
                address_match = re.search(address_pattern, text_content)
                if address_match:
                    facility['street_address'] = address_match.group().strip()
            else:
                facility['street_address'] = address_elem.get_text(strip=True)
            
            # Extract materials info (raw text for LLM processing)
            materials_elem = container.find(['div', 'span', 'ul'], 
                                          class_=re.compile(r'material|accept|service', re.I))
            if materials_elem:
                facility['raw_materials'] = materials_elem.get_text(strip=True)
            else:
                # Get all text content for LLM analysis
                facility['raw_materials'] = container.get_text(strip=True)
            
            # Look for last update date
            date_elem = container.find(['span', 'div'], 
                                     class_=re.compile(r'date|update|modified', re.I))
            if date_elem:
                facility['last_update_date'] = date_elem.get_text(strip=True)
            else:
                # Default to current date if not found
                facility['last_update_date'] = datetime.now().strftime('%Y-%m-%d')
            
            # Only return if we have at least business name
            if facility.get('business_name'):
                return facility
                
        except Exception as e:
            print(f"❌ Error parsing facility container: {str(e)}")
        
        return None
    
    def classify_materials_with_llm(self, raw_materials: str) -> Dict[str, List[str]]:
        """Use OpenAI GPT to classify materials into predefined categories"""
        
        categories_str = json.dumps(self.materials_mapping.CATEGORIES, indent=2)
        
        prompt = f"""
You are a recycling facility data classifier. Given the raw materials text from a recycling facility, 
classify the materials into the exact predefined categories and items below.

PREDEFINED CATEGORIES AND ITEMS:
{categories_str}

RAW MATERIALS TEXT FROM FACILITY:
{raw_materials}

TASK:
1. Identify which predefined categories this facility accepts
2. For each category, identify which specific items from the predefined list they accept
3. Only use the exact category names and item descriptions provided above
4. If materials don't clearly match predefined items, don't include them

Return your response as a JSON object with this format:
{{
    "materials_category": ["Electronics", "Batteries"],
    "materials_accepted": ["Computers, Laptops, Tablets", "Cell Phones, Smartphones", "Household Batteries (AA, AAA, 9V, etc.)"]
}}

Be conservative - only include categories and items you're confident about based on the text.
"""

        try:
            print("🤖 Sending classification request to OpenAI...")
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a precise data classifier for recycling facilities. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            result = response.choices[0].message.content.strip()
            print("✅ LLM classification completed")
            
            # Clean up response to extract JSON
            if '```json' in result:
                result = result.split('```json')[1].split('```')[0].strip()
            elif '```' in result:
                result = result.split('```')[1].strip()
            
            classification = json.loads(result)
            print(f"📊 Classified into {len(classification.get('materials_category', []))} categories")
            print(f"📋 Found {len(classification.get('materials_accepted', []))} accepted materials")
            
            return classification
            
        except Exception as e:
            print(f"❌ Error classifying materials with LLM: {str(e)}")
            return {"materials_category": [], "materials_accepted": []}
    
    def process_facilities(self, raw_facilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process raw facility data through LLM classification"""
        processed_facilities = []
        
        print(f"🔄 Processing {len(raw_facilities)} raw facilities through LLM...")
        
        for i, facility in enumerate(raw_facilities):
            try:
                print(f"\n🏢 Processing facility {i+1}: {facility.get('business_name', 'Unknown')}")
                
                # Classify materials using LLM
                raw_materials = facility.get('raw_materials', '')
                print(f"📝 Raw materials text (first 100 chars): {raw_materials[:100]}...")
                
                classification = self.classify_materials_with_llm(raw_materials)
                
                # Build final facility object
                processed_facility = {
                    "business_name": facility.get('business_name', 'Unknown'),
                    "last_update_date": facility.get('last_update_date', datetime.now().strftime('%Y-%m-%d')),
                    "street_address": facility.get('street_address', 'Address not found'),
                    "materials_category": classification.get('materials_category', []),
                    "materials_accepted": classification.get('materials_accepted', [])
                }
                
                processed_facilities.append(processed_facility)
                print(f"✅ Successfully processed facility {i+1}")
                
                # Rate limiting for OpenAI API
                print("⏳ Waiting 1 second for API rate limiting...")
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ Error processing facility {i+1}: {str(e)}")
                continue
        
        print(f"\n📈 Successfully processed {len(processed_facilities)} facilities")
        return processed_facilities
    
    def scrape_facilities(self, material: str = "Electronics", zipcode: str = "10001", 
                         radius: str = "100", min_results: int = 3) -> List[Dict[str, Any]]:
        """Main method to scrape and process recycling facilities"""
        driver = None
        
        try:
            print("🚀 Starting Earth911 recycling facility scraper...")
            print(f"🔍 Search parameters: {material}, {zipcode}, within {radius} miles")
            
            # Setup WebDriver
            driver = self.setup_driver()
            
            # Perform search
            print("\n📍 Step 1: Performing search...")
            if not self.perform_search(driver, material, zipcode, radius):
                print("❌ Failed to perform search")
                return []
            
            # Extract raw data
            print("\n📊 Step 2: Extracting raw data...")
            raw_facilities = self.extract_raw_data(driver)
            
            if len(raw_facilities) < min_results:
                print(f"⚠️ Only found {len(raw_facilities)} facilities, minimum required: {min_results}")
            
            # Process through LLM
            print("\n🤖 Step 3: Processing through LLM...")
            processed_facilities = self.process_facilities(raw_facilities)
            
            final_count = min(len(processed_facilities), min_results) if len(processed_facilities) >= min_results else len(processed_facilities)
            result = processed_facilities[:min_results] if len(processed_facilities) >= min_results else processed_facilities
            
            print(f"\n🎉 Scraping completed successfully!")
            print(f"📊 Final result: {len(result)} facilities")
            
            return result
            
        except Exception as e:
            print(f"❌ Error in scrape_facilities: {str(e)}")
            return []
        
        finally:
            if driver:
                print("🔒 Closing WebDriver...")
                driver.quit()


def main():
    """Main execution function"""
    
    # Configuration with your OpenAI API key
    OPENAI_API_KEY = "YOUR API KEY "
    
    # Search configuration
    SEARCH_CONFIG = {
        "material": "Electronics",
        "zipcode": "10001", 
        "radius": "100",
        "min_results": 3
    }
    
    print("🎬 Starting Earth911 LLM-Based Recycling Scraper")
    print(f"🔑 Using OpenAI API key: {OPENAI_API_KEY[:20]}...")
    print(f"🔍 Search configuration: {SEARCH_CONFIG}")
    
    # Initialize scraper
    try:
        scraper = Earth911Scraper(OPENAI_API_KEY)
        print("✅ Scraper initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize scraper: {str(e)}")
        return
    
    # Scrape facilities
    print("\n🚀 Starting scraping process...")
    facilities = scraper.scrape_facilities(
        material=SEARCH_CONFIG["material"],
        zipcode=SEARCH_CONFIG["zipcode"], 
        radius=SEARCH_CONFIG["radius"],
        min_results=SEARCH_CONFIG["min_results"]
    )
    
    # Output results
    if facilities:
        print("\n" + "="*60)
        print("🎉 SCRAPED FACILITIES DATA - SUCCESS!")
        print("="*60)
        
        # Pretty print each facility
        for i, facility in enumerate(facilities, 1):
            print(f"\n🏢 FACILITY {i}:")
            print(f"   Business Name: {facility['business_name']}")
            print(f"   Address: {facility['street_address']}")
            print(f"   Last Update: {facility['last_update_date']}")
            print(f"   Categories: {', '.join(facility['materials_category'])}")
            print(f"   Materials: {len(facility['materials_accepted'])} items")
            for material in facility['materials_accepted']:
                print(f"     • {material}")
        
        # Output as JSON
        output_json = json.dumps(facilities, indent=2)
        print(f"\n📋 COMPLETE JSON OUTPUT:")
        print("-" * 40)
        print(output_json)
        
        # Save to file
        filename = f'earth911_facilities_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        try:
            with open(filename, 'w') as f:
                json.dump(facilities, f, indent=2)
            print(f"\n💾 Results saved to '{filename}'")
        except Exception as e:
            print(f"❌ Error saving file: {str(e)}")
        
        # Summary statistics
        print(f"\n📊 SCRAPING SUMMARY:")
        print(f"   Total facilities: {len(facilities)}")
        
        all_categories = set()
        all_materials = set()
        
        for facility in facilities:
            all_categories.update(facility['materials_category'])
            all_materials.update(facility['materials_accepted'])
        
        print(f"   Unique categories found: {len(all_categories)}")
        print(f"   Categories: {', '.join(sorted(all_categories))}")
        print(f"   Unique materials found: {len(all_materials)}")
        
        print(f"\n✅ Scraping process completed successfully!")
        
    else:
        print("\n❌ No facilities were successfully scraped")
        print("🔧 Try checking the website structure or API connectivity")


if __name__ == "__main__":
    main()
