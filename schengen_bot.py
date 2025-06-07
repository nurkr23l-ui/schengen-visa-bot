#!/usr/bin/env python3
import os
import sys
import logging
import json
import asyncio
import aiohttp
from datetime import datetime
from pytz import timezone
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand

# Load environment variables
load_dotenv()

# Logging settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Telegram bot settings
TELEGRAM_BOT_TOKEN = "TOKEN"
TELEGRAM_CHAT_ID = "user-chat-id"

# API URL
API_URL = "https://api.schengenvisaappointments.com/api/visa-list/?format=json"

# Country and city information
COUNTRIES = {
    'France': 'Fransa',
    'Netherlands': 'Hollanda',
    'Ireland': 'İrlanda',
    'Malta': 'Malta',
    'Sweden': 'İsveç',
    'Czechia': 'Çekya',
    'Croatia': 'Hırvatistan',
    'Bulgaria': 'Bulgaristan',
    'Finland': 'Finlandiya',
    'Slovenia': 'Slovenya',
    'Denmark': 'Danimarka',
    'Norway': 'Norveç',
    'Estonia': 'Estonya',
    'Lithuania': 'Litvanya',
    'Luxembourg': 'Lüksemburg',
    'Ukraine': 'Ukrayna',
    'Latvia': 'Letonya'
}

CITIES = ['Ankara', 'Istanbul', 'Izmir', 'Antalya', 'Gaziantep', 'Bursa', 'Edirne']

class VisaBot:
    def __init__(self):
        self.app = None
        self.running = False
        self.current_check = None
        self.country = None
        self.city = None
        self.frequency = 5  # Default check frequency (minutes)
        self.user_selections = {}

    def create_frequency_keyboard(self):
        """Create button keyboard for check frequency"""
        keyboard = [
            [InlineKeyboardButton(f"{i} Minutes", callback_data=f"freq_{i}") for i in range(1, 6)]
        ]
        return InlineKeyboardMarkup(keyboard)

    def create_country_keyboard(self):
        """Create button keyboard for country selection"""
        keyboard = []
        row = []
        for i, (eng_name, tr_name) in enumerate(COUNTRIES.items(), 1):
            row.append(InlineKeyboardButton(tr_name, callback_data=f"country_{eng_name}"))
            if i % 3 == 0:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        return InlineKeyboardMarkup(keyboard)

    def create_city_keyboard(self):
        """Create button keyboard for city selection"""
        keyboard = []
        row = []
        for i, city in enumerate(CITIES, 1):
            row.append(InlineKeyboardButton(city, callback_data=f"city_{city}"))
            if i % 3 == 0:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        return InlineKeyboardMarkup(keyboard)

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Button callback handler"""
        try:
            query = update.callback_query
            await query.answer()
            
            user_id = str(update.effective_user.id)
            if user_id not in self.user_selections:
                self.user_selections[user_id] = {}

            data = query.data
            logger.info(f"Button callback received: {data} - User: {user_id}")

            # Notify the user that the process has started
            await query.edit_message_text(f"⏳ Processing... Please wait.")

            if data.startswith("freq_"):
                try:
                    self.frequency = int(data.split("_")[1])
                    logger.info(f"Check frequency set: {self.frequency} minutes")
                    
                    if self.running:
                        await self.stop_checking()
                        self.running = True
                        self.current_check = asyncio.create_task(self.check_appointments())
                    
                    await query.edit_message_text(f"✅ Check frequency set to {self.frequency} minutes.")
                except Exception as e:
                    logger.error(f"Frequency setting error: {str(e)}")
                    await query.edit_message_text(f"❌ Error setting frequency: {str(e)}")
            
            elif data.startswith("country_"):
                try:
                    # Processing country selection message
                    logger.info(f"Processing country selection: {data}")
                    
                    # Extract country code
                    parts = data.split("_", 1)
                    if len(parts) < 2:
                        raise ValueError(f"Invalid country data: {data}")
                        
                    selected_country_eng = parts[1]  # Get English country name
                    
                    # Check the validity of the country code
                    if selected_country_eng not in COUNTRIES:
                        raise ValueError(f"Invalid country selection: {selected_country_eng}")
                    
                    selected_country_tr = COUNTRIES[selected_country_eng]  # Get Turkish counterpart
                    logger.info(f"Selected country: {selected_country_tr} ({selected_country_eng})")
                    
                    # Update user selections
                    self.user_selections[user_id] = {"country": selected_country_eng}  # Clear previous selections
                    self.country = selected_country_eng  # Update main variable
                    
                    # Show keyboard for city selection
                    await query.edit_message_text(
                        f"✅ {selected_country_tr} selected.\n🏢 Please select a city:",
                        reply_markup=self.create_city_keyboard()
                    )
                except Exception as e:
                    logger.error(f"Country selection error: {str(e)}")
                    await query.edit_message_text(
                        f"❌ An error occurred during country selection: {str(e)}\nPlease try again.",
                        reply_markup=self.create_country_keyboard()
                    )
            
            elif data.startswith("city_"):
                try:
                    # Processing city selection message
                    logger.info(f"Processing city selection: {data}")
                    
                    # Extract city name
                    parts = data.split("_", 1)
                    if len(parts) < 2:
                        raise ValueError(f"Invalid city data: {data}")
                        
                    selected_city = parts[1]  # Get city name
                    logger.info(f"Selected city: {selected_city}")
                    
                    # Update user selections
                    self.user_selections[user_id]["city"] = selected_city
                    
                    # Check if country selection has been made
                    if "country" in self.user_selections[user_id]:
                        selected_country = self.user_selections[user_id]["country"]
                        logger.info(f"Starting appointment check: {selected_country} - {selected_city}")
                        
                        await self.start_check_with_selections(
                            update,
                            selected_country,
                            selected_city
                        )
                    else:
                        logger.error(f"Country selection not found - User: {user_id}")
                        await query.edit_message_text("❌ Please select a country first.")
                except Exception as e:
                    logger.error(f"City selection error: {str(e)}")
                    await query.edit_message_text(
                        f"❌ An error occurred during city selection: {str(e)}\nPlease try again.",
                        reply_markup=self.create_city_keyboard()
                    )
            else:
                logger.warning(f"Unknown callback data: {data}")
                await query.edit_message_text(f"❌ Unknown operation: {data}")
                
        except Exception as e:
            logger.error(f"Callback processing error: {str(e)}")
            try:
                await update.callback_query.edit_message_text(f"❌ An error occurred during the operation: {str(e)}")
            except Exception:
                logger.error("Error message could not be sent")


    async def start_check_with_selections(self, update, country, city):
        """Start appointment check with selections"""
        try:
            # Check country and city information
            if not country or not city:
                error_msg = "Country or city information is missing"
                logger.error(f"Cannot start appointment check: {error_msg}")
                
                if hasattr(update, "callback_query"):
                    await update.callback_query.edit_message_text(f"❌ {error_msg}. Please try again.")
                else:
                    await update.message.reply_text(f"❌ {error_msg}. Please try again.")
                return
                
            # If there is already a running check, stop it
            if self.running:
                logger.info(f"Stopping previous check: {self.country} - {self.city}")
                await self.stop_checking()

            # Set variables for new check
            self.country = country
            self.city = city
            self.running = True
            
            # Translate country name to Turkish
            country_tr = COUNTRIES.get(country, country)
            
            logger.info(f"Starting appointment check: {country_tr} - {city}")

            # Send information message to the user
            message = (
                f"✅ Appointment check started for {country_tr} in {city}.\n"
                f"⏱ Select the check frequency:"
            )
            
            # Send the message
            if hasattr(update, "callback_query"):
                await update.callback_query.edit_message_text(
                    message,
                    reply_markup=self.create_frequency_keyboard()
                )
            else:
                await update.message.reply_text(
                    message,
                    reply_markup=self.create_frequency_keyboard()
                )

            # Start the check task
            self.current_check = asyncio.create_task(self.check_appointments())
            logger.info(f"Appointment check task started: {country_tr} - {city}")
            
            # Send information message to Telegram chat
            try:
                start_message = (
                    f"🔄 Appointment check started\n"
                    f"📍 Country: {country_tr}\n"
                    f"🏢 City: {city}\n"
                    f"⏱ Check frequency: {self.frequency} minutes\n"
                    f"⏰ Start: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                )
                await self.app.bot.send_message(
                    chat_id=TELEGRAM_CHAT_ID,
                    text=start_message
                )
            except Exception as e:
                logger.error(f"Error sending start message: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error starting appointment check: {str(e)}")
            error_message = f"❌ An error occurred while starting the appointment check: {str(e)}"
            
            try:
                if hasattr(update, "callback_query"):
                    await update.callback_query.edit_message_text(error_message)
                else:
                    await update.message.reply_text(error_message)
            except Exception:
                logger.error("Error message could not be sent")
                
            # Reset the running status in case of error
            self.running = False
            self.current_check = None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Bot start command"""
        welcome_message = (
            "🌟 Welcome to the Schengen Visa Appointment Check Bot! 🌟\n\n"
            "Available commands:\n"
            "/start - Bot information\n"
            "/check - Start appointment check\n"
            "/stop - Stop active check\n"
            "/status - Current status information\n"
            "/help - Help menu"
        )
        await update.message.reply_text(welcome_message)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command"""
        help_text = (
            "📋 Command List:\n\n"
            "1. Start Appointment Check:\n"
            "/check France Istanbul\n\n"
            "2. Stop Check:\n"
            "/stop\n\n"
            "3. Check Status:\n"
            "/status\n\n"
            "Supported Countries:\n"
            + ", ".join(COUNTRIES.values()) + "\n\n"
            "Supported Cities:\n"
            + ", ".join(CITIES)
        )
        await update.message.reply_text(help_text)

    async def check(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start appointment check"""
        await update.message.reply_text(
            "🌍 Please select a country:",
            reply_markup=self.create_country_keyboard()
        )

    async def stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Stop appointment check"""
        if not self.running:
            await update.message.reply_text("ℹ️ No active check.")
            return

        await self.stop_checking()
        await update.message.reply_text("✅ Appointment check stopped.")

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Current status information"""
        if not self.running:
            await update.message.reply_text("ℹ️ No active check.")
            return

        status_message = (
            f"📍 Checked Country: {self.country}\n"
            f"🏢 Checked City: {self.city}\n"
            f"⏱ Check Frequency: {self.frequency} minutes\n"
            "✅ Status: Active"
        )
        await update.message.reply_text(status_message)

    async def stop_checking(self):
        """Stop the check task"""
        self.running = False
        if self.current_check:
            self.current_check.cancel()
            try:
                await self.current_check
            except asyncio.CancelledError:
                pass
        self.current_check = None

    async def check_appointments(self):
        """Perform appointment check"""
        check_count = 0
        last_error_time = None
        error_count = 0
        first_check = True
        
        while self.running:
            check_count += 1
            try:
                logger.info(f"Checking appointments: {self.country} - {self.city} (Check #{check_count})")
                
                # Send notification only on the first check, skip on subsequent checks
                if first_check:
                    first_check = False
                    # Skip the first check notification as it is already sent in start_check_with_selections
                    logger.info("First check - notification skipped as start notification is already sent")
                    # Notification sending code removed
                
                # Send request to the API
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get(API_URL, timeout=30) as response:
                            if response.status != 200:
                                error_msg = f"API error: HTTP {response.status}"
                                logger.error(error_msg)
                                
                                # Notify the user in case of continuous error
                                error_count += 1
                                if error_count >= 3:
                                    await self.app.bot.send_message(
                                        chat_id=TELEGRAM_CHAT_ID,
                                        text=f"⚠️ API connection issue: {error_msg}\nChecks are continuing."
                                    )
                                    error_count = 0
                                continue

                            # Successful response, reset error count
                            error_count = 0
                            
                            try:
                                data = await response.json()
                                logger.info(f"Received {len(data)} appointment records from API")
                            except json.JSONDecodeError as e:
                                logger.error(f"API response is not in JSON format: {str(e)}")
                                continue
                            
                            available_appointments = []

                            # Filter appointments
                            for appointment in data:
                                try:
                                    source = appointment.get('source_country')
                                    mission = appointment.get('mission_country', '')
                                    center = appointment.get('center_name', '')
                                    
                                    # Country and city check
                                    if (
                                        source == 'Turkiye'
                                        and self.country == mission
                                        and center and self.city and self.city.lower() in center.lower()
                                    ):
                                        # Convert appointment date to Turkey timezone
                                        appointment_date = appointment.get('appointment_date')
                                        if appointment_date:
                                            try:
                                                date_obj = datetime.fromisoformat(appointment_date.replace('Z', '+00:00'))
                                                tr_timezone = timezone('Europe/Istanbul')
                                                tr_date = date_obj.astimezone(tr_timezone)
                                                formatted_date = tr_date.strftime('%d.%m.%Y %H:%M')
                                            except ValueError as e:
                                                logger.warning(f"Date conversion error: {str(e)}")
                                                formatted_date = appointment_date
                                        else:
                                            formatted_date = 'No date information'
                                        
                                        # Add appointment information
                                        available_appointments.append({
                                            'date': formatted_date,
                                            'center': center,
                                            'category': appointment.get('visa_category', 'Not specified'),
                                            'link': appointment.get('book_now_link', '#')
                                        })
                                except Exception as e:
                                    logger.warning(f"Appointment processing error: {str(e)}")
                                    continue

                            # Notify found appointments
                            if available_appointments:
                                logger.info(f"{len(available_appointments)} suitable appointments found")
                                for appt in available_appointments:
                                    message = (
                                        f"🎉 Appointment found for {self.country}!\n\n"
                                        f"📍 Center: {appt['center']}\n"
                                        f"📅 Date: {appt['date']}\n"
                                        f"📋 Category: {appt['category']}\n"
                                        f"🔗 Appointment Link:\n{appt['link']}"
                                    )
                                    try:
                                        await self.app.bot.send_message(
                                            chat_id=TELEGRAM_CHAT_ID,
                                            text=message
                                        )
                                    except Exception as e:
                                        logger.error(f"Error sending message: {str(e)}")
                            else:
                                logger.info(f"No suitable appointment found: {self.country} - {self.city}")
                                
                                # Send status notification every 10 checks
                                if check_count % 10 == 0:
                                    status_message = (
                                        f"ℹ️ Status Update\n"
                                        f"📍 Country: {self.country}\n"
                                        f"🏢 City: {self.city}\n"
                                        f"🔄 Check Count: {check_count}\n"
                                        f"⏱ Check Frequency: {self.frequency} minutes\n"
                                        f"⏰ Last Check: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                                        f"✅ Status: Actively checking"
                                    )
                                    try:
                                        await self.app.bot.send_message(
                                            chat_id=TELEGRAM_CHAT_ID,
                                            text=status_message
                                        )
                                    except Exception as e:
                                        logger.error(f"Error sending status message: {str(e)}")
                    except aiohttp.ClientError as e:
                        logger.error(f"API connection error: {str(e)}")
                        error_count += 1
                        
            except asyncio.CancelledError:
                logger.info("Appointment check cancelled")
                break
            except Exception as e:
                logger.error(f"Unexpected error during check: {str(e)}")
                error_count += 1
                
                # Notify the user in case of continuous error
                if error_count >= 3:
                    try:
                        await self.app.bot.send_message(
                            chat_id=TELEGRAM_CHAT_ID,
                            text=f"⚠️ Error during appointment check: {str(e)}\nChecks are continuing."
                        )
                    except Exception:
                        pass
                    error_count = 0

            # Wait for the next check
            logger.info(f"Waiting {self.frequency} minutes for the next check...")
            await asyncio.sleep(self.frequency * 60)

    async def run(self):
        """Start the bot"""
        try:
            logger.info("Configuring bot...")
            self.app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

            # Define command descriptions
            commands = [
                BotCommand("start", "Bot information and command list"),
                BotCommand("help", "Help menu"),
                BotCommand("check", "Start appointment check"),
                BotCommand("stop", "Stop active check"),
                BotCommand("status", "Current status information")
            ]
            
            # Add handlers
            logger.info("Adding command handlers...")
            self.app.add_handler(CommandHandler("start", self.start))
            self.app.add_handler(CommandHandler("help", self.help))
            self.app.add_handler(CommandHandler("check", self.check))
            self.app.add_handler(CommandHandler("stop", self.stop))
            self.app.add_handler(CommandHandler("status", self.status))
            
            # Add callback handler - important: to handle callback_query's
            logger.info("Adding callback handler...")
            self.app.add_handler(CallbackQueryHandler(self.button_callback))

            # Start the bot
            logger.info("Starting bot...")
            await self.app.initialize()
            await self.app.start()
            
            # Register command list to Telegram
            logger.info("Registering command list to Telegram...")
            await self.app.bot.set_my_commands(commands)
            
            # Start polling - also listen to callback_query's
            logger.info("Starting polling...")
            await self.app.updater.start_polling(
                allowed_updates=["message", "callback_query"],  # Also listen to callback_query's
                drop_pending_updates=True
            )
            
            # Startup message
            logger.info("Bot successfully started and running!")
            print("✅ Schengen Visa Appointment Check Bot started!")
            print("ℹ️ Press Ctrl+C to stop the bot.")

            # Continue polling
            while True:
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.info("Shutdown signal received...")
        except Exception as e:
            logger.error(f"Error running bot: {str(e)}")
            print(f"❌ Error starting bot: {str(e)}")
            raise
        finally:
            if self.app:
                logger.info("Shutting down bot...")
                try:
                    # Stop active checks
                    if self.running:
                        logger.info("Stopping active checks...")
                        await self.stop_checking()
                    
                    # Stop the updater
                    if self.app.updater and self.app.updater.running:
                        logger.info("Stopping updater...")
                        await self.app.updater.stop()
                    
                    logger.info("Stopping bot...")
                    await self.app.stop()
                    await self.app.shutdown()
                    logger.info("Bot successfully stopped.")
                    print("✅ Bot successfully stopped.")
                except Exception as e:
                    logger.error(f"Error stopping bot: {str(e)}")
                    print(f"⚠️ Error stopping bot: {str(e)}")
                    raise


async def main():
    """Main program"""
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not found! Please check the .env file.")
        return

    if not TELEGRAM_CHAT_ID:
        print("❌ TELEGRAM_CHAT_ID not found! Please check the .env file.")
        return

    bot = VisaBot()
    try:
        logger.info("Starting bot...")
        await bot.run()
    except KeyboardInterrupt:
        print("\n👋 Stopping bot...")
    except Exception as e:
        print(f"\n❌ Critical error: {str(e)}")
    finally:
        logger.info("Shutting down bot...")


if __name__ == "__main__":
    asyncio.run(main())
