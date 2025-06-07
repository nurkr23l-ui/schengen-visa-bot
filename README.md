# Schengen Visa Appointment Checker Bot 🌍

This is a Telegram bot that allows you to check Schengen visa appointments. The bot regularly checks for appointments for the specified country and city, and sends a notification via Telegram when an available appointment is found.

## Features ✨

- Appointment checking for 17 different Schengen countries
- Appointment tracking in 7 different cities in Turkey
- Easy usage via Telegram
- Button interface for country and city selection
- Customizable check frequency (1-5 minutes)
- Detailed appointment information (date, center, category)
- Automatic notification system
- Direct reservation link when an appointment is found

## Installation 🚀

### Requirements

- Python 3.8 or higher (Python 3.11 recommended)
- pip (Python package manager)

### Steps

1. Clone the repository:
```bash
git clone https://github.com/petersawm/schengen-visa-bot.git
cd schengen-visa-bot
```

2. (Optional) Create and activate a virtual environment:
```bash
python3 -m venv .venv
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/macOS
```

3. Install the required Python packages:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file and add your Telegram bot information:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### Required Libraries

- python-telegram-bot (v20.6)
- python-dotenv (v1.0.0)
- aiohttp (v3.8.6)
- asyncio (v3.4.3)
- pytz (v2023.3)

## Usage 📱

To start the bot:
```bash
python3 schengen_bot.py
```

### Telegram Commands

- `/start` - Bot info and command list
- `/help` - Help menu
- `/check` - Start appointment check with button interface
- `/stop` - Stop active check
- `/status` - Current status information

### Using the Button Interface

1. Send the `/check` command
2. Select a country from the menu
3. Select a city
4. Select the check frequency (1-5 minutes)

### Old Command Usage (Optional)

```
/check France Istanbul
```

## Supported Countries 🌐

- 🇫🇷 France
- 🇳🇱 Netherlands
- 🇮🇪 Ireland
- 🇲🇹 Malta
- 🇸🇪 Sweden
- 🇨🇿 Czechia
- 🇭🇷 Croatia
- 🇧🇬 Bulgaria
- 🇫🇮 Finland
- 🇸🇮 Slovenia
- 🇩🇰 Denmark
- 🇳🇴 Norway
- 🇪🇪 Estonia
- 🇱🇹 Lithuania
- 🇱🇺 Luxembourg
- 🇺🇦 Ukraine
- 🇱🇻 Latvia

## Supported Cities 🏢

- 🇹🇷 Ankara
- 🇹🇷 Istanbul
- 🇹🇷 Izmir
- 🇹🇷 Antalya
- 🇹🇷 Gaziantep
- 🇹🇷 Bursa
- 🇹🇷 Edirne

## Development 🛠

This bot is developed with Python 3 and uses the following main libraries:

- python-telegram-bot
- aiohttp
- python-dotenv

## License 📄

This project is licensed under the MIT license. For more information, see the `LICENSE` file.

## Contributing 🤝

All contributions are welcome! Please open an issue to discuss your changes before submitting a pull request.
