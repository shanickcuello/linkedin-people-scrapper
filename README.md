
# POC

https://github.com/user-attachments/assets/a30bc3a3-b6db-43d4-9539-8465c4469048


# LinkedIn People Scraper

A Python-based tool to scrape LinkedIn profiles of people with specific job titles. This tool searches for PEOPLE, not job postings.

## Features

- Search for people by job title
- Filter by location (optional)
- Export results to CSV
- Anti-detection measures to avoid being blocked
- Configurable search parameters
- Comprehensive logging

## Prerequisites

- Python 3.7+
- Chrome browser installed
- ChromeDriver (will be handled automatically by webdriver-manager)
- LinkedIn account

# How to

## Installation

## 1) Clone or download this repository
`git clone https://github.com/shanickcuello/linkedin-people-scrapper.git`

## 2) Optional but recommended, use [venv](https://docs.python.org/3/library/venv.html).

### Mac Os/Linux
Create venv : `python3 -m venv venv`

Activate venv: `. venv/bin/activate`

### Windows

Create venv: `py -3 -m venv venv`

Activate venv: ` . venv/Scripts/activate.bat`

### 3) Install required packages:

```bash
pip install -r requirements.txt
```

or

```bash
pip3 install -r requirements.txt
```

---

## Configuration

Edit `config.json` and add your credentials:

```json
{
  "username": "your_email@example.com",
  "password": "your_password"
}
```

**Warning**: Be careful not to commit credentials to version control. ⚠️‼️

### Configure Search Parameters

Edit `config.json` to specify what job titles to search for:

```json
{
  "searches": [
    {
      "job_title": "Software Engineer", <--- Title
      "location": "" <--- Optional
    },
    {
      "job_title": "Data Scientist",
      "location": "San Francisco"
    }
  ],
  "max_pages": 5,
  "headless": false
}
```

#### Configuration Options

- `searches`: Array of search configurations
  - `job_title`: The job title to search for (required)
  - `location`: Location filter (optional)
- `max_pages`: Maximum number of search result pages to scrape (Too many pages could cause your Linkedin account to be banned for x time. Max pages is 100 in my experience)
- `headless`: Run browser in headless mode (default: false)
- `delay_min`: Minimum delay between actions in seconds (default: 2)
- `delay_max`: Maximum delay between actions in seconds (default: 5)

## Usage

Run the scraper:

```bash
python3 linkedin_people_scraper.py
```

The script will:
1. Log into LinkedIn using your credentials
2. Search for people with the specified job titles
3. Extract profile information (name, title, company, location, profile URL)
4. Save results to a timestamped CSV file

## Output

Results are saved to CSV files with the following columns:
- name
- title
- company
- location
- profile_url
- about
- connections

Example filename: `linkedin_profiles_20241221_143052.csv`

## Logging

The script creates detailed logs in `linkedin_scraper.log` and also outputs to the console.

## Important Notes

### LinkedIn Terms of Service
- This tool is for educational and research purposes
- Be respectful of LinkedIn's terms of service
- Use reasonable delays between requests
- Don't overwhelm LinkedIn's servers

### Rate Limiting
- The script includes random delays between actions
- Avoid running multiple instances simultaneously
- Consider using longer delays for large-scale scraping

### Anti-Detection
- The script includes several anti-detection measures:
  - Custom user agent
  - Random delays
  - Disabling automation indicators
  - Natural scrolling behavior

## Troubleshooting

### Common Issues

1. **Login Failed**: 
   - Check your credentials
   - LinkedIn may require 2FA - handle this manually in non-headless mode

2. **No Profiles Found**:
   - Check if the job title search terms are too specific
   - Verify you're logged in successfully
   - Try broader search terms

3. **Browser Issues**:
   - Ensure Chrome is installed and up to date
   - Try running in non-headless mode first

4. **Rate Limiting**:
   - Increase delays in config
   - Reduce max_pages
   - Take breaks between runs

### Debugging

Run in non-headless mode to see what's happening:

```json
{
  "headless": false
}
```

Check the log file for detailed error messages:

```bash
tail -f linkedin_scraper.log
```

## Legal and Ethical Considerations

- Respect LinkedIn's robots.txt and terms of service
- Use this tool responsibly and ethically
- Consider the privacy of the individuals whose profiles you're scraping
- Be aware of data protection laws in your jurisdiction
- Use scraped data only for legitimate purposes

## Example Results

The CSV output will look like:

```csv
name,title,company,location,profile_url,about,connections
John Doe,Senior Software Engineer,Tech Company Inc,San Francisco Bay Area,https://linkedin.com/in/johndoe,,
Jane Smith,Data Scientist,Data Corp,New York,,
```
