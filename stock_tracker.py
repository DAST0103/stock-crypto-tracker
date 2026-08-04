import sys
from datetime import datetime
import pytz
import yfinance as yf

# Portfolio mit Kaufkursen
PORTFOLIO = {
    "Dormakaba": {"symbol": "DOKA.SW", "buy_price": 70.50, "currency": "CHF"},
    "Kering": {"symbol": "KER.PA", "buy_price": 340.00, "currency": "EUR"},
    "Beyond Meat": {"symbol": "BYND", "buy_price": 6.00, "currency": "USD"},
    "Microsoft": {"symbol": "MSFT", "buy_price": 530.00, "currency": "USD"},
    "Ethereum": {"symbol": "ETH-USD", "buy_price": 4408.80, "currency": "USD"},
    "Chainlink": {"symbol": "LINK-USD", "buy_price": 19.671, "currency": "USD"},
}


def get_current_price(symbol):
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1d")
    if not data.empty:
        return data["Close"].iloc[-1]
    return None


def main():
    tz = pytz.timezone("Europe/Zurich")
    now = datetime.now(tz)

    # Erweitertes Zeitfenster (12:25 bis 12:59 Uhr) für eventuelle GitHub-Verzögerungen
    is_daily_report = now.hour == 12 and now.minute >= 25

    print(
        f"--- Modus: {'Täglicher Statusbericht (12:30 Uhr)' if is_daily_report else '2-Stunden-Gewinnprüfung'} ---"
    )

    for name, info in PORTFOLIO.items():
        current_price = get_current_price(info["symbol"])

        if current_price is None:
            print(f"❌ Fehler beim Abrufen von {name}")
            continue

        buy_price = info["buy_price"]
        diff = current_price - buy_price
        curr = info["currency"]

        # Log-Ausgabe für den normalen 2-Stunden-Check
        if not is_daily_report:
            status = "🚨 GEWINN-ALERT (+4)!" if diff >= 4.0 else "Kein Alarm"
            print(
                f" -> [{name}] Kurs: {current_price:.2f} {curr} | Kauf: {buy_price:.2f} {curr} | Diff: {diff:+.2f} {curr} ({status})"
            )

        # 1. Benachrichtigung bei Gewinnen >= +4.00
        if diff >= 4.0:
            print(
                f"🚨 GEWINN-ALERT! [{name}] Aktuell: {current_price:.2f} {curr} | "
                f"Kaufkurs: {buy_price:.2f} {curr} | Gewinn: +{diff:.2f} {curr}"
            )

        # 2. Täglicher Statusbericht um 12:30 Uhr
        if is_daily_report:
            sign = "+" if diff >= 0 else ""
            percent = (diff / buy_price) * 100
            print(
                f"📊 [{name}] Aktuell: {current_price:.2f} {curr} | "
                f"Abweichung zum Kauf: {sign}{diff:.2f} {curr} ({sign}{percent:.2f}%)"
            )


if __name__ == "__main__":
    main()
