#!/usr/bin/env python3

import time
import json
import csv
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import logging
from dataclasses import dataclass
from typing import List, Optional
import os
from datetime import datetime

@dataclass
class LinkedInProfile:
    name: str
    title: str
    company: str
    location: str
    profile_url: str
    about: str = ""
    connections: str = ""
    
class LinkedInPeopleScraper:
    def __init__(self, config_path: str = "config.json"):
        self.config = self.load_config(config_path)
        self.driver = None
        self.profiles = []
        self.setup_logging()
        self.delay_min = self.config.get("delay_min", 2)
        self.delay_max = self.config.get("delay_max", 5)
        self.max_retries = self.config.get("max_retries", 3)
        self.debug_mode = self.config.get("debug_mode", False)
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('linkedin_scraper.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_config(self, config_path: str) -> dict:
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Config file {config_path} not found")
            raise
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON in config file {config_path}")
            raise
            
    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--disable-login-animations")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
        
        if self.config.get("headless", False):
            chrome_options.add_argument("--headless")
            
        self.logger.info("Setting up Chrome WebDriver...")
        self.driver = webdriver.Chrome(options=chrome_options)
        
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        })
        self.driver.implicitly_wait(10)
        self.logger.info("WebDriver setup completed")
        
    def login(self):
        self.logger.info("Attempting to log in to LinkedIn...")
        self.driver.get("https://www.linkedin.com/login")
        
        username = os.getenv('LINKEDIN_USERNAME') or self.config.get('username')
        password = os.getenv('LINKEDIN_PASSWORD') or self.config.get('password')
        
        if not username or not password:
            self.logger.error("LinkedIn credentials not found in environment variables or config")
            raise ValueError("LinkedIn credentials required")
            
        try:
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            password_field = self.driver.find_element(By.ID, "password")
            
            username_field.send_keys(username)
            password_field.send_keys(password)
            password_field.send_keys(Keys.RETURN)
            
            WebDriverWait(self.driver, 15).until(
                EC.url_contains("/feed/")
            )
            self.logger.info("Successfully logged in to LinkedIn")
            
        except TimeoutException:
            self.logger.error("Login failed or took too long")
            raise
            
    def debug_page_elements(self):
        if not self.debug_mode:
            return
            
        try:
            page_source_length = len(self.driver.page_source)
            current_url = self.driver.current_url
            self.logger.info(f"Debug - Current URL: {current_url}")
            self.logger.info(f"Debug - Page source length: {page_source_length}")
            
            possible_selectors = [
                ".reusable-search__result-container",
                ".search-result-card", 
                ".search-results-container .search-result",
                "[data-testid='search-result']",
                ".entity-result",
                ".search-result"
            ]
            
            for selector in possible_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                self.logger.info(f"Debug - Selector '{selector}': found {len(elements)} elements")
                
        except Exception as e:
            self.logger.error(f"Debug error: {str(e)}")
    
    def search_people(self, job_title: str, location: str = "") -> List[LinkedInProfile]:
        self.logger.info(f"Searching for people with title: {job_title}")
        
        search_url = "https://www.linkedin.com/search/results/people/"
        
        query_params = []
        if job_title:
            query_params.append(f"keywords={job_title.replace(' ', '%20')}")
        if location:
            query_params.append(f"geoUrn=[{location}]")
            
        if query_params:
            search_url += "?" + "&".join(query_params)
            
        try:
            self.driver.get(search_url)
            self.random_delay()
            
            WebDriverWait(self.driver, 15).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            self.random_delay()
            
        except Exception as e:
            self.logger.error(f"Failed to load search page: {str(e)}")
            return []
        
        self.debug_page_elements()
        
        profiles = []
        page_count = 0
        max_pages = self.config.get("max_pages", 5)
        
        while page_count < max_pages:
            try:
                self.scroll_page()
                
                profile_elements = []
                selectors_to_try = [
                    ".iVQBdbUhhelimibSIqzFwVInEeWYnuzuXYt",
                    ".FUnoUCUWHqgqZSnCbQFYlmjMydtKKTZFBI",
                    "li.iVQBdbUhhelimibSIqzFwVInEeWYnuzuXYt",
                    ".search-results-container li",
                    ".reusable-search__result-container",
                    "[data-chameleon-result-urn*='member']"
                ]
                
                for selector in selectors_to_try:
                    profile_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if profile_elements:
                        self.logger.info(f"Found {len(profile_elements)} elements with selector: {selector}")
                        break
                
                if not profile_elements:
                    self.logger.warning(f"No profile elements found on page {page_count}")
                    if self.debug_mode:
                        self.debug_page_elements()
                    
                profiles_found_on_page = 0
                for element in profile_elements:
                    profile = self.extract_profile_data(element)
                    if profile and self.is_relevant_profile(profile, job_title):
                        profiles.append(profile)
                        profiles_found_on_page += 1
                        self.logger.info(f"Found profile: {profile.name} - {profile.title}")
                        
                self.logger.info(f"Page {page_count + 1}: Found {profiles_found_on_page} relevant profiles")
                        
                if not self.go_to_next_page():
                    break
                    
                page_count += 1
                time.sleep(random.uniform(3, 6))
                
            except Exception as e:
                self.logger.error(f"Error on page {page_count}: {str(e)}")
                break
                
        return profiles
        
    def extract_profile_data(self, element) -> Optional[LinkedInProfile]:
        try:
            name = "N/A"
            name_selectors = [
                "a[data-test-app-aware-link] span[aria-hidden='true']",
                ".cVuaSJRqbNqHnilutFYDHJuqUTzYMuksamE a span[aria-hidden='true']",
                "a span[aria-hidden='true']",
                ".entity-result__title-text a"
            ]
            
            for selector in name_selectors:
                try:
                    name_element = element.find_element(By.CSS_SELECTOR, selector)
                    name = name_element.text.strip()
                    if name:
                        break
                except NoSuchElementException:
                    continue
            
            profile_url = ""
            link_selectors = [
                "a[data-test-app-aware-link]",
                ".cVuaSJRqbNqHnilutFYDHJuqUTzYMuksamE a",
                "a[href*='/in/']"
            ]
            
            for selector in link_selectors:
                try:
                    link_element = element.find_element(By.CSS_SELECTOR, selector)
                    profile_url = link_element.get_attribute("href")
                    if profile_url:
                        break
                except NoSuchElementException:
                    continue
            
            title = "N/A"
            title_selectors = [
                ".yfUkKdhgeLpjgQhByLNZHDeqKrdFoVhLu",
                ".entity-result__primary-subtitle",
                "div.t-14.t-black.t-normal"
            ]
            
            for selector in title_selectors:
                try:
                    title_element = element.find_element(By.CSS_SELECTOR, selector)
                    title = title_element.text.strip()
                    if title:
                        break
                except NoSuchElementException:
                    continue
                
            location = "N/A"
            location_selectors = [
                ".zSSJMHVoDKMBnaZNdAshUPZWUHKNuZqwaVUXw",
                "div.t-14.t-normal:not(.t-black)",
                ".entity-result__summary"
            ]
            
            for selector in location_selectors:
                try:
                    location_element = element.find_element(By.CSS_SELECTOR, selector)
                    location = location_element.text.strip()
                    if location:
                        break
                except NoSuchElementException:
                    continue
            
            summary = "N/A"
            summary_selectors = [
                ".JPLdZSnfcNtQiDKPYwnBNWcWAqncdkolU",
                ".entity-result__summary",
                "p.t-12.t-black--light"
            ]
            
            for selector in summary_selectors:
                try:
                    summary_element = element.find_element(By.CSS_SELECTOR, selector)
                    summary = summary_element.text.strip()
                    if summary:
                        break
                except NoSuchElementException:
                    continue
                
            if self.debug_mode:
                self.logger.info(f"Debug - Extracted: {name} | {title} | {location} | {summary}")
                
            if name == "N/A":
                if self.debug_mode:
                    self.logger.warning("Could not extract name, skipping profile")
                return None
                
            return LinkedInProfile(
                name=name,
                title=title,
                company=summary,
                location=location,
                profile_url=profile_url,
                about=summary
            )
            
        except Exception as e:
            if self.debug_mode:
                self.logger.error(f"Error extracting profile data: {str(e)}")
            return None
            
    def is_relevant_profile(self, profile: LinkedInProfile, job_title: str) -> bool:
        job_title_lower = job_title.lower()
        profile_title_lower = profile.title.lower()
        
        keywords = job_title_lower.split()
        return any(keyword in profile_title_lower for keyword in keywords)
        
    def random_delay(self):
        """Add a random delay to avoid detection"""
        delay = random.uniform(self.delay_min, self.delay_max)
        time.sleep(delay)
        
    def scroll_page(self):
        """Scroll down the page with natural human-like behavior"""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Scroll down in chunks with random pauses
            for _ in range(3):  # Scroll in 3 steps
                scroll_chunk = random.uniform(0.3, 0.7)  # Scroll 30%-70% each time
                self.driver.execute_script(f"window.scrollTo(0, {int(last_height * scroll_chunk)});")
                self.random_delay()
            
            # Final scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.random_delay()
            
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height > last_height:
                # More content loaded, scroll a bit more
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.random_delay()
                
        except Exception as e:
            self.logger.error(f"Error during page scrolling: {str(e)}")
            
    def go_to_next_page(self) -> bool:
        """Navigate to the next page of search results with retry logic"""
        try:
            # Wait for next button to be clickable
            next_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Next']"))
            )
            
            if next_button.is_enabled():
                # Add some randomness to avoid detection
                self.random_delay()
                
                # Scroll the button into view
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                self.random_delay()
                
                # Click with retry logic
                for attempt in range(self.max_retries):
                    try:
                        next_button.click()
                        # Wait for page to load
                        WebDriverWait(self.driver, 10).until(
                            EC.staleness_of(next_button)
                        )
                        self.random_delay()
                        return True
                    except Exception as e:
                        if attempt == self.max_retries - 1:
                            self.logger.error(f"Failed to click next button after {self.max_retries} attempts: {str(e)}")
                            return False
                        self.random_delay()
            return False
        except (NoSuchElementException, TimeoutException) as e:
            self.logger.info(f"No more pages available: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error navigating to next page: {str(e)}")
            return False
            
    def save_to_csv(self, profiles: List[LinkedInProfile], filename: str = None):
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"linkedin_profiles_{timestamp}.csv"
            
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['name', 'title', 'company', 'location', 'profile_url', 'about', 'connections']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for profile in profiles:
                writer.writerow({
                    'name': profile.name,
                    'title': profile.title,
                    'company': profile.company,
                    'location': profile.location,
                    'profile_url': profile.profile_url,
                    'about': profile.about,
                    'connections': profile.connections
                })
                
        self.logger.info(f"Saved {len(profiles)} profiles to {filename}")
        return filename
        
    def run_search(self) -> List[LinkedInProfile]:
        try:
            self.setup_driver()
            self.login()
            
            all_profiles = []
            
            for search_config in self.config["searches"]:
                job_title = search_config["job_title"]
                location = search_config.get("location", "")
                
                self.logger.info(f"Starting search for: {job_title}")
                profiles = self.search_people(job_title, location)
                all_profiles.extend(profiles)
                
                time.sleep(random.uniform(5, 10))
                
            self.profiles = all_profiles
            return all_profiles
            
        except Exception as e:
            self.logger.error(f"Error during scraping: {str(e)}")
            raise
        finally:
            if self.driver:
                self.driver.quit()
                
    def run(self):
        try:
            profiles = self.run_search()
            
            if profiles:
                filename = self.save_to_csv(profiles)
                self.logger.info(f"Scraping completed. Found {len(profiles)} profiles.")
                self.logger.info(f"Results saved to: {filename}")
            else:
                self.logger.info("No profiles found matching the search criteria")
                
        except Exception as e:
            self.logger.error(f"Scraping failed: {str(e)}")
            
if __name__ == "__main__":
    scraper = LinkedInPeopleScraper()
    scraper.run()
