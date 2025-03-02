import requests
from bs4 import BeautifulSoup
import time
import json
import argparse
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("nps_scraper.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

class NPSCampsiteScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml',
            'Accept-Language': 'en-US,en;q=0.9'
        })
        self.base_url = "https://www.recreation.gov"
        # NPS campsites are typically on recreation.gov

    def search_campgrounds(self, park_name):
        """Search for campgrounds in a specific park"""
        search_url = f"{self.base_url}/search"
        params = {
            "q": f"{park_name} campground",
            "entity_type": "campground"
        }
        
        logging.info(f"Searching for campgrounds in {park_name}")
        response = self.session.get(search_url, params=params)
        
        if response.status_code != 200:
            logging.error(f"Failed to search campgrounds: {response.status_code}")
            return []
        
        # Parse the search results page to extract campground IDs and names
        soup = BeautifulSoup(response.text, 'html.parser')
        campgrounds = []
        
        # This will need to be adjusted based on the actual structure of the recreation.gov search results
        search_results = soup.select('.search-result-item')
        
        for result in search_results:
            try:
                campground_id = result.get('data-entity-id')
                campground_name = result.select_one('.entity-name').text.strip()
                campgrounds.append({
                    'id': campground_id,
                    'name': campground_name
                })
            except (AttributeError, KeyError) as e:
                logging.warning(f"Failed to parse campground entry: {e}")
                continue
        
        logging.info(f"Found {len(campgrounds)} campgrounds")
        return campgrounds

    def check_availability(self, campground_id, date):
        """Check availability for a specific campground on a specific date"""
        availability_url = f"{self.base_url}/api/camps/availability/campground/{campground_id}/month"
        
        # Format date as required by the API (YYYY-MM-01)
        formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-01")
        
        params = {
            "start_date": formatted_date
        }
        
        logging.info(f"Checking availability for campground {campground_id} on {date}")
        response = self.session.get(availability_url, params=params)
        
        if response.status_code != 200:
            logging.error(f"Failed to get availability: {response.status_code}")
            return []
        
        try:
            availability_data = response.json()
            campsites = availability_data.get('campsites', {})
            
            available_sites = []
            target_date = date.replace('-', '')
            
            for site_id, site_data in campsites.items():
                # Check if the site is available on the target date
                availability = site_data.get('availabilities', {}).get(target_date, '')
                if availability == 'Available':
                    available_sites.append({
                        'site_id': site_id,
                        'site_name': site_data.get('site', f"Site {site_id}"),
                        'type': site_data.get('type', 'Unknown')
                    })
            
            logging.info(f"Found {len(available_sites)} available sites for {date}")
            return available_sites
            
        except (json.JSONDecodeError, KeyError) as e:
            logging.error(f"Failed to parse availability data: {e}")
            return []

    def send_notification(self, email, campground_name, available_sites, date):
        """Send email notification when available sites are found"""
        if not available_sites:
            return False
            
        sender = "nps_scraper@example.com"  # Configure with your email
        recipient = email
        
        subject = f"Campsite Available: {campground_name} on {date}"
        
        body = f"Good news! The following campsites are available at {campground_name} on {date}:\n\n"
        for site in available_sites:
            body += f"- {site['site_name']} (Type: {site['type']})\n"
            
        body += f"\nBook now at: {self.base_url}/camping/campgrounds/{available_sites[0]['site_id']}\n"
        
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient
        
        try:
            # This is a placeholder. In a real implementation, you would configure 
            # this with your SMTP server details
            smtp_server = "smtp.example.com"
            smtp_port = 587
            smtp_username = "your_username"
            smtp_password = "your_password"
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
                
            logging.info(f"Notification email sent to {email}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send notification: {e}")
            return False
    
    def poll_availability(self, park_name, date, interval=3600, email=None, max_attempts=24):
        """
        Poll for availability at specified intervals
        
        Args:
            park_name: Name of the park
            date: Date to check (YYYY-MM-DD)
            interval: Polling interval in seconds (default: 1 hour)
            email: Email to notify when availability is found
            max_attempts: Maximum number of polling attempts (default: 24, i.e., 24 hours if interval=3600)
        """
        attempts = 0
        
        logging.info(f"Starting polling for {park_name} on {date}")
        
        while attempts < max_attempts:
            logging.info(f"Polling attempt {attempts + 1}/{max_attempts}")
            
            # Find campgrounds in the park
            campgrounds = self.search_campgrounds(park_name)
            
            for campground in campgrounds:
                # Check availability for each campground
                available_sites = self.check_availability(campground['id'], date)
                
                if available_sites:
                    logging.info(f"Found {len(available_sites)} available sites at {campground['name']}")
                    
                    # Print available sites
                    print(f"\nAvailable sites at {campground['name']} on {date}:")
                    for site in available_sites:
                        print(f"- {site['site_name']} (Type: {site['type']})")
                    
                    # Send notification if email is provided
                    if email:
                        self.send_notification(email, campground['name'], available_sites, date)
                    
                    return {
                        'campground': campground['name'],
                        'available_sites': available_sites,
                        'date': date
                    }
            
            # No availability found, wait for next polling interval
            attempts += 1
            if attempts < max_attempts:
                next_poll = time.time() + interval
                logging.info(f"No availability found. Next poll at {datetime.fromtimestamp(next_poll).strftime('%H:%M:%S')}")
                time.sleep(interval)
        
        logging.info("Maximum polling attempts reached. No availability found.")
        return None


def main():
    parser = argparse.ArgumentParser(description='NPS Campsite Availability Scraper')
    parser.add_argument('--park', required=True, help='National Park name (e.g., "Yosemite")')
    parser.add_argument('--date', required=True, help='Date to check (YYYY-MM-DD)')
    parser.add_argument('--interval', type=int, default=3600, help='Polling interval in seconds (default: 3600)')
    parser.add_argument('--email', help='Email to notify when availability is found')
    parser.add_argument('--max-attempts', type=int, default=24, help='Maximum number of polling attempts')
    
    args = parser.parse_args()
    
    scraper = NPSCampsiteScraper()
    result = scraper.poll_availability(
        args.park, 
        args.date, 
        args.interval, 
        args.email, 
        args.max_attempts
    )
    
    if result:
        print(f"\nSuccess! Found available campsites at {result['campground']} on {result['date']}")
    else:
        print(f"\nNo available campsites found for {args.park} on {args.date} after {args.max_attempts} polling attempts.")


if __name__ == "__main__":
    main()