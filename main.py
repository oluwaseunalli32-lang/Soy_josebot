import os
import time
import logging
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Fetch bot token from environment variable
TOKEN = os.getenv("BOT_TOKEN")

# ==========================================
# WEBSITE SEO CHECKER FUNCTIONALITY
# ==========================================

async def analyze_seo(url: str) -> str:
    """Fetches a web page and performs basic SEO checks."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=10)
        load_time = round(time.time() - start_time, 2)
        
        parsed_url = urlparse(response.url)
        is_https = parsed_url.scheme == "https"
        status_code = response.status_code

        if status_code != 200:
            return f"❌ Could not access site. HTTP Status Code: {status_code}"

        soup = BeautifulSoup(response.text, "html.parser")

        # 1. Page Title
        title_tag = soup.find("title")
        title_text = title_tag.string.strip() if title_tag and title_tag.string else "Missing"
        title_len = len(title_text) if title_text != "Missing" else 0

        # 2. Meta Description
        meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        desc_text = meta_desc["content"].strip() if meta_desc and meta_desc.get("content") else "Missing"
        desc_len = len(desc_text) if desc_text != "Missing" else 0

        # 3. Word Count
        body_text = soup.body.get_text(separator=" ", strip=True) if soup.body else ""
        word_count = len(body_text.split())

        # 4. Basic SEO Checks
        h1_tags = soup.find_all("h1")
        h1_count = len(h1_tags)
        
        img_tags = soup.find_all("img")
        images_missing_alt = sum(1 for img in img_tags if not img.get("alt"))

        canonical_tag = soup.find("link", attrs={"rel": "canonical"})
        has_canonical = "Yes" if canonical_tag else "No"

        # Format Response
        report = (
            f"📊 **SEO Audit Report for:**\n`{url}`\n\n"
            f"🔒 **HTTPS Status:** {'✅ Secure (HTTPS)' if is_https else '⚠️ Insecure (HTTP)'}\n"
            f"⚡ **Load Time:** {load_time} seconds (Status: {status_code})\n\n"
            f"🏷️ **Page Title:**\n`{title_text}`\n"
            f"└ *Length:* {title_len} chars {'✅' if 30 <= title_len <= 60 else '⚠️ (Ideal: 30-60)'}\n\n"
            f"📝 **Meta Description:**\n`{desc_text}`\n"
            f"└ *Length:* {desc_len} chars {'✅' if 120 <= desc_len <= 160 else '⚠️ (Ideal: 120-160)'}\n\n"
            f"📖 **Word Count:** {word_count} words\n\n"
            f"🔍 **Basic SEO Checks:**\n"
            f"• **H1 Headings:** {h1_count} found {'✅' if h1_count == 1 else '⚠️ (Ideal: exactly 1)'}\n"
            f"• **Image Alt Tags:** {images_missing_alt}/{len(img_tags)} missing alt attributes\n"
            f"• **Canonical Tag:** {has_canonical}\n"
        )
        return report

    except requests.exceptions.Timeout:
        return "❌ Request timed out. The website took too long to respond."
    except requests.exceptions.RequestException as e:
        return f"❌ Unable to analyze URL. Error: {str(e)}"


async def my_function(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command handler for /function - Accepts a URL argument."""
    if not context.args:
        await update.message.reply_text(
            "⚠️ Please provide a website URL.\n\n"
            "**Example usage:**\n`/function example.com`",
            parse_mode="Markdown"
        )
        return

    target_url = context.args[0]
    status_msg = await update.message.reply_text("🔍 Analyzing website SEO... Please wait...")
    
    report = await analyze_seo(target_url)
    await status_msg.edit_text(report, parse_mode="Markdown", disable_web_page_preview=True)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command."""
    welcome_text = (
        "👋 **Welcome to the SEO Checker Bot!**\n\n"
        "I can audit any webpage and return title tags, meta descriptions, word counts, and speed metrics.\n\n"
        "**Available Commands:**\n"
        "• /function `<url>` - Run an SEO check on a website\n"
        "• /help - View instructions\n"
        "• /about - Learn about this bot"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /help command."""
    help_text = (
        "ℹ️ **How to Use This Bot**\n\n"
        "To check a website's SEO metrics, send the `/function` command followed by the website address.\n\n"
        "**Example:**\n"
        "`/function wikipedia.org`"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /about command."""
    about_text = (
        "🤖 **About Website SEO Checker Bot**\n\n"
        "Built with Python, BeautifulSoup4, and `python-telegram-bot`.\n"
        "Hosted securely on Render cloud infrastructure."
    )
    await update.message.reply_text(about_text, parse_mode="Markdown")


def main() -> None:
    """Starts the bot application."""
    if not TOKEN:
        logger.error("BOT_TOKEN environment variable missing. Exiting...")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("function", my_function))

    logger.info("Bot started successfully. Listening for commands...")
    app.run_polling()


if __name__ == "__main__":
    main()
