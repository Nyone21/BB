from bots.ai_memory import get_stats
from bots import state


def build_report(symbol):
    wins, losses, winrate = get_stats()

    return (
        "📊 ОСНОВНОЙ ОТЧЁТ\n"
        f"📌 Symbol: {symbol}\n"
        f"💰 Balance: {state.last_balance}\n"
        f"📈 Price: {state.last_price}\n"
        f"🧠 AI Signal: {state.ai_signal}\n\n"
        f"📊 Trades:\n"
        f"✅ Wins: {wins}\n"
        f"❌ Losses: {losses}\n"
        f"🎯 Winrate: {winrate}%"
    )
