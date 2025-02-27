import requests
import config
from datetime import datetime, timedelta
import random
import logging
import time
from typing import Dict, Optional
import json
import os

logger = logging.getLogger(__name__)

# Cache për të ruajtur rezultatet e fundit
_signal_cache: Dict[str, Dict] = {}
_cache_file = "data/signal_cache.json"

def _generate_demo_data(pair: str) -> Dict:
    """Generate demo data when API fails"""
    base, quote = pair.split('/')

    # Gjeneroj çmime të rastësishme por realiste
    base_price = {
        'EUR': 1.08, 'GBP': 1.26, 'USD': 1.0, 'JPY': 0.0067,
        'CHF': 1.13, 'AUD': 0.65
    }

    # Përcaktoj çmimin bazë
    price = base_price.get(base, 1.0) / base_price.get(quote, 1.0)

    # Shtoj një variacion të vogël rastësor (+/- 0.5%)
    variation = random.uniform(-0.005, 0.005)
    price = price * (1 + variation)

    # Gjeneroj spread të vogël
    spread = price * 0.0002  # 0.02% spread
    bid = price - spread/2
    ask = price + spread/2

    # Gjeneroj forcë sinjali të lartë për demo
    strength = random.uniform(0.85, 0.98)  # Vetëm sinjale të forta për demo

    signal_data = {
        "pair": pair,
        "price": price,
        "strength": strength,
        "signal": get_signal_type(strength),
        "timestamp": datetime.now().isoformat(),
        "trend": random.choice(["⬆️ RRITËSE", "⬇️ ZBRITËSE"]),
        "bid": bid,
        "ask": ask,
        "is_demo": True
    }

    return signal_data

def get_forex_data(pair: str, is_premium: bool = False, max_retries: int = 3) -> Optional[Dict]:
    """Get forex data from Alpha Vantage API with retry mechanism and caching"""
    if not _signal_cache:
        _load_cache()

    if pair in _signal_cache:
        cached_data = _signal_cache[pair]
        cache_time = datetime.fromisoformat(cached_data['timestamp'])
        time_since_cache = (datetime.now() - cache_time).total_seconds()
        time_until_refresh = max(0, config.CACHE_DURATION - time_since_cache)

        if time_since_cache < config.CACHE_DURATION:
            logger.info(f"Using cached data for {pair}. Next refresh in {int(time_until_refresh)} seconds")
            return cached_data
        else:
            logger.info(f"Cache expired for {pair}, refreshing data from API")

    # First try with premium API if user is premium
    if is_premium:
        api_keys = [config.ALPHA_VANTAGE_API_KEYS["premium"], config.ALPHA_VANTAGE_API_KEYS["free"]]
    else:
        api_keys = [config.ALPHA_VANTAGE_API_KEYS["free"]]

    for api_key in api_keys:
        for attempt in range(max_retries):
            try:
                base, quote = pair.split('/')
                logger.info(f"Fetching forex data for {pair} (attempt {attempt + 1}/{max_retries})")

                url = "https://www.alphavantage.co/query"
                params = {
                    "function": "CURRENCY_EXCHANGE_RATE",
                    "from_currency": base,
                    "to_currency": quote,
                    "apikey": api_key
                }

                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                if "Realtime Currency Exchange Rate" in data:
                    exchange_data = data["Realtime Currency Exchange Rate"]

                    close = float(exchange_data["5. Exchange Rate"])
                    bid = float(exchange_data["8. Bid Price"])
                    ask = float(exchange_data["9. Ask Price"])

                    # Përmirësojmë trendin duke përdorur spread
                    spread = ask - bid
                    spread_percentage = spread / close

                    # Trend më realist bazuar në spread
                    if spread_percentage < 0.0001:  # Spread shumë i ngushtë
                        trend_direction = 1  # Trend pozitiv
                    elif spread_percentage > 0.0003:  # Spread i gjerë
                        trend_direction = -1  # Trend negativ
                    else:
                        trend_direction = 0  # Neutral

                    # Forcë e sinjalit më realiste
                    strength = 1 - (spread_percentage * 1000)  # Normalize spread impact
                    strength = min(max(strength, 0), 1)  # Keep between 0 and 1

                    # Përshtatim forcën bazuar në trendin
                    if trend_direction != 0:
                        strength = strength * (0.8 + (0.4 * random.random()))  # Add some randomness
                    else:
                        strength = strength * 0.5  # Weaken neutral signals

                    signal_data = {
                        "pair": pair,
                        "price": close,
                        "strength": strength,
                        "signal": get_signal_type(strength),
                        "timestamp": exchange_data["6. Last Refreshed"],
                        "trend": "⬆️ RRITËSE" if trend_direction > 0 else "⬇️ ZBRITËSE" if trend_direction < 0 else "➡️ NEUTRALE",
                        "bid": bid,
                        "ask": ask,
                        "is_demo": False
                    }

                    _signal_cache[pair] = signal_data
                    _save_cache()

                    logger.info(f"Successfully generated signal for {pair}")
                    return signal_data

                elif "Note" in data:
                    logger.warning(f"API rate limit hit for key {api_key}: {data['Note']}")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    # If this is the last API key, generate demo data
                    if api_key == api_keys[-1]:
                        logger.info(f"All API keys exhausted, generating demo data for {pair}")
                        demo_data = _generate_demo_data(pair)
                        _signal_cache[pair] = demo_data
                        _save_cache()
                        return demo_data
                    break  # Try next API key

            except requests.exceptions.RequestException as e:
                logger.error(f"Request error for {pair}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                if api_key == api_keys[-1]:
                    # Generate demo data as fallback after all retries
                    logger.info(f"Generating demo data as fallback for {pair} after request error")
                    demo_data = _generate_demo_data(pair)
                    _signal_cache[pair] = demo_data
                    _save_cache()
                    return demo_data
                break  # Try next API key

            except Exception as e:
                logger.error(f"Error processing forex data for {pair}: {str(e)}")
                if attempt == max_retries - 1 and api_key == api_keys[-1]:
                    # Generate demo data after all retries failed
                    logger.info(f"Generating demo data after all retries failed for {pair}")
                    demo_data = _generate_demo_data(pair)
                    _signal_cache[pair] = demo_data
                    _save_cache()
                    return demo_data
                time.sleep(2)
                continue

    # If we get here, all API keys failed
    logger.error(f"All API keys failed for {pair}, generating demo data")
    demo_data = _generate_demo_data(pair)
    _signal_cache[pair] = demo_data
    _save_cache()
    return demo_data

def _load_cache():
    """Load signal cache from file"""
    global _signal_cache
    try:
        if os.path.exists(_cache_file):
            with open(_cache_file, 'r') as f:
                _signal_cache = json.load(f)
    except Exception as e:
        logger.error(f"Error loading cache: {e}")
        _signal_cache = {}

def _save_cache():
    """Save signal cache to file"""
    try:
        os.makedirs(os.path.dirname(_cache_file), exist_ok=True)
        with open(_cache_file, 'w') as f:
            json.dump(_signal_cache, f)
    except Exception as e:
        logger.error(f"Error saving cache: {e}")

def get_signal_type(strength):
    """Determine signal type based on strength"""
    if strength >= 0.90:  # Increased threshold for stronger buy signals
        return "STRONG_BUY"
    elif strength >= 0.75:  # Moderate buy needs higher confidence
        return "MODERATE_BUY"
    elif strength <= 0.10:  # Very low strength for strong sell
        return "STRONG_SELL"
    elif strength <= 0.25:  # Decreased threshold for moderate sell
        return "MODERATE_SELL"
    else:
        return "NEUTRAL"

def get_trading_duration(strength, trend):
    """Calculate recommended trading duration based on signal strength and trend"""
    if trend == "⬆️ RRITËSE":
        base_duration = 5  # 5 minute base for upward trend
    elif trend == "⬇️ ZBRITËSE":
        base_duration = 3  # 3 minute base for downward trend
    else:
        return None  # No duration recommendation for neutral trend

    # Adjust duration based on signal strength - only recommend for very strong signals
    if strength >= 0.90:  # Strong signals only
        multiplier = 1.5  # Longer duration for very strong signals
    elif strength >= 0.75:
        multiplier = 1.0  # Base duration for moderate signals
    else:
        return None  # No duration recommendation for weak signals

    return int(base_duration * multiplier)

def format_signal_message(signal_data):
    """Format signal data into a readable message"""
    if not signal_data:
        return "❌ Nuk u mor dot sinjali. Ju lutemi prisni pak sekonda dhe provoni përsëri."

    signal_type = signal_data["signal"]
    is_demo = signal_data.get("is_demo", False)

    # Header with signal strength and demo notice
    demo_notice = "\n📊 (Të dhëna demo - API në limit)" if is_demo else ""
    message = f"{config.SIGNAL_STRENGTH_MESSAGES[signal_type]}{demo_notice}\n\n"

    # Basic information
    message += f"🔄 Çifti: {signal_data['pair']}\n"
    message += f"💰 Çmimi: {signal_data['price']:.5f}\n"
    message += f"📊 Bid/Ask: {signal_data['bid']:.5f}/{signal_data['ask']:.5f}\n"
    message += f"💪 Forca e Sinjalit: {signal_data['strength']:.1%}\n"
    message += f"📈 Trendi: {signal_data['trend']}\n"
    message += f"🕒 Koha: {datetime.fromisoformat(signal_data['timestamp']).strftime('%H:%M:%S')}"

    # Rekomandimi i tregtimit - vetëm për sinjale shumë të forta
    trading_duration = get_trading_duration(signal_data['strength'], signal_data['trend'])

    if signal_type == "STRONG_BUY":
        message += f"\n\n💎 REKOMANDIM BLERJEJE:"
        message += f"\n✅ BLERJE (BUY) në {signal_data['ask']:.5f}"
        if trading_duration:
            message += f"\n⏱️ Kohëzgjatja e Tregtimit: {trading_duration} minuta"
        message += "\n⚠️ Vendosni Stop Loss 10-15 pips poshtë çmimit të hyrjes"
    elif signal_type == "STRONG_SELL":
        message += f"\n\n💎 REKOMANDIM SHITJEJE:"
        message += f"\n🔴 SHITJE (SELL) në {signal_data['bid']:.5f}"
        if trading_duration:
            message += f"\n⏱️ Kohëzgjatja e Tregtimit: {trading_duration} minuta"
        message += "\n⚠️ Vendosni Stop Loss 10-15 pips sipër çmimit të hyrjes"
    elif signal_type in ["MODERATE_BUY", "MODERATE_SELL"]:
        message += "\n\n⚠️ Sinjal mesatar - Prisni për konfirmim më të fortë"
    else:
        message += "\n\n⚠️ Nuk ka sinjal të qartë - Rekomandohet të prisni"

    return message