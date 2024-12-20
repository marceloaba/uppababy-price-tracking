import logging
import os
from time import sleep
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Define retailers and their scraping logic
RETAILERS = {
    "uppababy.ca": {
        "base_url": "https://uppababy.ca/strollers/full-size/vista-v3-stroller",
        "colors": ["callum", "declan", "greyson", "gwen", "jake", "kenzi", "savannah", "theo"],
        "find_price": lambda soup: soup.find("bdi").text.strip(),
    },
    "clement.ca": {
        "base_url": "https://www.clement.ca/en/stroller-vista-v3",
        "colors": ["callum-1086856", "declan-1086857", "greyson-1086858", "gwen-1086860", "jake-1086862", "kenzi-1086863", "savannah-1086865", "theo-1086864"],
        "find_price": lambda soup: soup.find("span", class_="price").text.strip(),
    },
}

# Store previous prices
previous_prices = {}
daily_summary_sent = False  # Track if the daily summary has been sent


def send_telegram_alert(message_to_send):
    """
    Send a message to a specific Telegram CHAT_ID.
    """
    endpoint = f"{os.environ.get('MESSAGE_API')}"
    headers = {"Content-Type": "application/json"}
    payload = {"message": message_to_send}

    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        logging.info(f"{response.json()}")
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Fail to send telegram message: {message_to_send}")
        return {"error": str(e)}


def get_html_content(url, retries=3, delay=5):
    """
    Fetch the HTML content of a URL with retries for non-200 responses.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                logging.info(f"Successfully fetched {url} (Status: 200)")
                return response
            else:
                logging.warning(
                    f"Attempt {attempt}/{retries}: Non-200 response for {url} (Status: {response.status_code})")

            if attempt < retries:
                logging.info(f"Retrying in {delay} seconds...")
                sleep(delay)

        except requests.exceptions.RequestException as e:
            logging.error(f"Attempt {attempt}/{retries}: Error fetching {url}: {e}")

            if attempt < retries:
                logging.info(f"Retrying in {delay} seconds...")
                sleep(delay)

    # If all retries fail
    logging.error(f"Failed to fetch {url} after {retries} attempts.")
    return None


def scrape_retailer(retailer_name, config, first_run=False):
    """
    Scrape prices for a given retailer and check for price changes.
    """
    global previous_prices
    base_url = config["base_url"]
    colors = config["colors"]
    find_price = config["find_price"]
    current_prices = []
    for color in colors:
        url = None
        try:
            if retailer_name == "uppababy.ca":
                url = f"{base_url}/{color}/"
            elif retailer_name == "clement.ca":
                url = f"{base_url}-{color}.html"
            logging.info(f"Fetching URL: {url}")
            response = get_html_content(url)
            if not response:
                logging.error(f"Skipping {url} due to repeated failures. Price unknown.")
                current_prices.append(f"{color}: Unknown")
                continue

            soup = BeautifulSoup(response.content, "html.parser")
            price = find_price(soup)

            # Split to get only the color name
            if retailer_name == "clement.ca":
                color = color.split("-")[0]

            logging.info(f"{retailer_name} ({color}): {price}")
            current_prices.append(f"{retailer_name} ({color}): {price}")

            # Check for price change
            previous_price = previous_prices.get(f"{retailer_name}_{color}")
            if first_run:
                previous_prices[f"{retailer_name}_{color}"] = price

            if previous_price is not None:
                if previous_price != price:
                    logging.info(f"Price changed for {retailer_name} ({color}): {previous_price} -> {price}")
                    message = f"{retailer_name} ({color}): {price}" if first_run else f"Price changed for {retailer_name} ({color}): {previous_price} -> {price}\n" \
                                                                                      f"{url}"
                    send_telegram_alert(message)
                else:
                    logging.info(f"No price change for {retailer_name} ({color}): {price}")
                previous_prices[f"{retailer_name}_{color}"] = price

        except Exception as e:
            logging.error(f"Error scraping {url}: {e}")
            send_telegram_alert(f"Error scraping {url}: {e}")

    return current_prices


def main():
    """
    Main function to initialize scraping.
    """
    global daily_summary_sent
    first_run = True  # Flag for the first run

    while True:
        logging.info("Starting price check...")
        all_prices = []

        for retailer, config in RETAILERS.items():
            prices = scrape_retailer(retailer, config, first_run)
            all_prices.extend(prices)

        # First run: Send a summary of all current prices
        if first_run:
            send_telegram_alert("Initial Price Summary:\n" + "\n".join(all_prices))
            first_run = False

        # Daily summary at 8 AM
        current_time = datetime.now()
        if current_time.hour == 8 and not daily_summary_sent:
            send_telegram_alert("Daily Price Summary:\n" + "\n".join(all_prices))
            daily_summary_sent = True
        elif current_time.hour != 8:
            daily_summary_sent = False

        if os.environ.get('SCRAPE_FREQUENCY_IN_SECONDS'):
            scrape_frequency_in_seconds = float(os.environ.get('SCRAPE_FREQUENCY_IN_SECONDS'))
        else:
            scrape_frequency_in_seconds = 1800
        logging.info(f"Price check completed. Sleeping for {scrape_frequency_in_seconds} seconds...")
        sleep(scrape_frequency_in_seconds)


if __name__ == "__main__":
    main()
