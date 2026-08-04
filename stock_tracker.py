import sys
from datetime import datetime
import pytz
import requests
import yfinance as yf

# ---------------------------------------------------------
# NTFY EINSTELLUNG
# ---------------------------------------------------------
NTFY_TOPIC = "dast0103_kurs_alert"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"

# ---------------------------------------------------------
# PORTFOLIO & KAUFKURSE
# ---------------------------------------------------------
PORTFOLIO = {
    "Dormakaba": {"symbol": "DOKA.SW", "buy_price": 70.50, "currency": "CHF"},
    "Kering": {"symbol": "KER.PA", "buy_price": 340.00, "currency": "EUR"},
    "Beyond Meat": {"symbol": "BYND", "buy_price": 6.00, "currency": "USD"},
    "Microsoft": {"symbol": "MSFT", "buy_price": 530.00, "currency": "USD"},
    "Ethereum": {"symbol": "ETH-USD", "buy_price": 4408.80, "currency": "USD"},
    "Chainlink": {"symbol": "LINK-USD", "buy_price": 19.671, "currency": "USD"},
}


def send_ntfy_notification(title, message, tags="chart_with_upwards_trend"):
    """Sendet eine Push-Nachricht über ntfy.sh (UTF-8 geschützt)"""
    try:
        # Header-Werte für ntfy sicher in UTF-8 kodieren
        headers = {
            "Title": title.encode("utf-8").decode("latin-1"),
            "Tags": tags.encode("utf-8").decode("latin-1"),
        }

        response = requests.post(
            NTFY_URL,
            data=message.encode("utf-8"),
            headers=headers,
            timeout=10,
        )
        if response.status_code == 200:
            print(f"✅ ntfy Benachrichtigung erfolgreich gesendet: '{title}'")
        else:
            print(
                f"❌ Fehler beim Senden an ntfy (Status Code: {response.status_code})"
            )
    except Exception as e:
        print(f"❌ Fehler beim Verbinden mit ntfy: {e}")


def get_current_price(symbol):
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1d")
    if not data.empty:
        return data["Close"].iloc[-1]
    return None


def main():
    tz = pytz.timezone("Europe/Zurich")
    now = datetime.now(tz)

    # Zeitfenster für den 12:30 Uhr Tagesbericht (12:20 bis 13:30 Uhr)
    is_daily_report = (now.hour == 12 and now.minute >= 20) or (
        now.hour == 13 and now.minute <= 30
    )

    print(
        f"--- Modus: {'Täglicher Statusbericht (12:30 Uhr)' if is_daily_report else '2-Stunden-Gewinnprüfung'} ---"
    )

    alert_messages = []
    report_messages = []

    for name, info in PORTFOLIO.items():
        current_price = get_current_price(info["symbol"])

        if current_price is None:
            print(f"❌ Fehler beim Abrufen von {name}")
            continue

        buy_price = info["buy_price"]
        diff = current_price - buy_price
        curr = info["currency"]

        print(
            f" -> [{name}] Kurs: {current_price:.2f} {curr} | Kauf: {buy_price:.2f} {curr} | Diff: {diff:+.2f} {curr}"
        )

        # 1. Bedingung: Gewinn >= +4.00 Einheiten
        if diff >= 4.0:
            alert_messages.append(
                f"🚨 [{name}] Aktuell: {current_price:.2f} {curr} | Gewinn: +{diff:.2f} {curr}"
            )

        # 2. Bedingung: Täglicher Bericht
        if is_daily_report:
            sign = "+" if diff >= 0 else ""
            percent = (diff / buy_price) * 100
            report_messages.append(
                f"• {name}: {current_price:.2f} {curr} ({sign}{diff:.2f} {curr} / {sign}{percent:.2f}%)"
            )

    # ---------------------------------------------------------
    # BENACHRICHTIGUNGEN SENDEN
    # ---------------------------------------------------------
    if alert_messages:
        alert_text = "\n".join(alert_messages)
        send_ntfy_notification(
            title="🚨 Kurs-Gewinn Alarm (+4)!",
            message=alert_text,
            tags="moneybag,rocket",
        )

    if is_daily_report and report_messages:
        report_text = "Tagesübersicht vs. Kaufkurse:\n" + "\n".join(
            report_messages
        )
        send_ntfy_notification(
            title="📊 Täglicher Portfolio-Bericht",
            message=report_text,
            tags="bar_chart,briefcase",
        )


if __name__ == "__main__":
    main()
