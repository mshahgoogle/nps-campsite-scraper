# NPS Campsite Availability Scraper

A Python script to check for campsite availability on the National Park Service reservations system (recreation.gov). This tool allows you to automatically poll for campsite openings at a specified national park for a specific date.

## Features

- Search for campgrounds within a specific national park
- Check for available campsites on a specified date
- Poll at regular intervals to find cancellations or newly released sites
- Email notifications when available sites are found
- Detailed logging for monitoring the scraper's activity

## Prerequisites

- Python 3.7+
- Required Python packages (install via `pip install -r requirements.txt`):
  - requests
  - beautifulsoup4

## Installation

1. Clone this repository:
```
git clone https://github.com/mshahgoogle/nps-campsite-scraper.git
cd nps-campsite-scraper
```

2. Install dependencies:
```
pip install -r requirements.txt
```

## Usage

Basic usage:
```
python nps_scraper.py --park "Yosemite" --date "2025-06-15"
```

### Command Line Arguments

- `--park`: (Required) National Park name (e.g., "Yosemite", "Grand Canyon")
- `--date`: (Required) Date to check for availability in YYYY-MM-DD format
- `--interval`: (Optional) Polling interval in seconds (default: 3600, i.e., 1 hour)
- `--email`: (Optional) Email address to notify when availability is found
- `--max-attempts`: (Optional) Maximum number of polling attempts (default: 24)

### Example

To check for campsite availability at Zion National Park on July 15, 2025, checking every 30 minutes for a maximum of 48 checks:
```
python nps_scraper.py --park "Zion" --date "2025-07-15" --interval 1800 --email your@email.com --max-attempts 48
```

## Email Notifications

To enable email notifications, you need to configure the SMTP settings in the script:

1. Open `nps_scraper.py`
2. Find the `send_notification` method
3. Replace the placeholder SMTP settings with your own:
```python
smtp_server = "your.smtp.server.com"
smtp_port = 587  # or your server's port
smtp_username = "your_username"
smtp_password = "your_password"
```

## Notes

- The script uses recreation.gov APIs, which may change over time. If the script stops working, it may need to be updated.
- Be respectful of the recreation.gov servers and avoid setting too frequent polling intervals.
- This tool is intended for personal use to find available campsites and not for automated booking.

## License

This project is available under the MIT License - see the LICENSE file for details.
