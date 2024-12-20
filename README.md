# UPPAbaby Price Tracking Bot

This Python-based application tracks stroller prices from multiple retailers and sends Telegram alerts for price changes. The application is built with web scraping libraries like `BeautifulSoup` and uses Telegram API integration for notifications.

## Features

- Tracks stroller prices from specified retailers.
- Sends alerts for price changes or errors using a Telegram bot.
- Provides daily price summaries.
- Configurable scraping frequency via environment variables.

## Requirements

- Python 3.10+
- Docker or Kubernetes or Run localy
- Telegram Bot API token and chat ID
- Libraries: `requests`, `beautifulsoup4`

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/marceloaba/uppababy-price-tracking.git
cd uppababy-price-tracking
```

### 2. Build and Push Docker Image

```bash
docker buildx build --platform linux/amd64,linux/arm64,linux/arm/v7 \
    -t marceloaba/uppababy-price-tracking:tagname --push .
```

### 3. Set Environment Variables

Create and set the following environment variables:

```bash
export TELEGRAM_TOKEN="your_telegram_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

### 4. Run the Application Using Docker Compose

#### Start the Containers

```bash
docker-compose up -d
```

The application will start and function using the configurations in the `docker-compose.yaml` file.

### 5. Run the Application on Kubernetes
Create base64 environment variables:
```bash
export TELEGRAM_TOKEN_BASE64=$(echo -n "$TELEGRAM_TOKEN" | base64)
export TELEGRAM_CHAT_ID_BASE64=$(echo -n "$TELEGRAM_CHAT_ID" | base64)
```

Install `envsubst` to create the telegram-secret.yaml and replace the variables with the actual telegram token and group ID values
```bash
brew install gettext
```

Deploying applications
```bash
cd kubernetes
kubectl create -f telegram.yaml
envsubst < telegram-secret.yaml | kubectl create -f -
kubectl create -f uppababy-price-tracking.yaml
```

## Retailers and Pricing Details

The bot scrapes pricing information from the following retailers:

- **uppababy.ca**: Supports multiple stroller colors.
- **clement.ca**: Supports multiple stroller colors.

Each retailer's scraping logic is defined in the application.

## Telegram Notifications
Telegram Repository: https://github.com/marceloaba/telegram

### Alerts Sent for:

- Price changes for specific stroller colors.
- Errors during scraping.
- Daily summaries of all prices at 8 AM.

### Example Message Format:

- **Price Change:**
  ```
  uppababy.ca (declan): Price changed from $1,200 to $1,150
  https://uppababy.ca/strollers/full-size/vista-v3-stroller/declan/
  ```

- **Daily Summary:**
  ```
  Daily Price Summary:
  uppababy.ca (callum): $1,200
  clement.ca (jake): $1,150
  ```

## Testing the Application

You can verify Telegram notifications by triggering price changes or simulating scraping errors.

## Notes

- Ensure your Telegram bot token and chat ID are securely stored.
- You can customize the scraping frequency by modifying the `SCRAPE_FREQUENCY_IN_SECONDS` environment variable.
- The application logs detailed information for monitoring and debugging purposes.

## Example Curl Command to Test Telegram API

```bash
curl -X POST http://localhost:5001/send_message \
     -H "Content-Type: application/json" \
     -d '{"message": "Test message from UPPAbaby Price Tracking Bot"}'
```

## Acknowledgments

This project uses the following:

- **BeautifulSoup** for web scraping.
- **Docker** and **Docker Compose** for containerization.
- **Telegram Bot API** for sending alerts.