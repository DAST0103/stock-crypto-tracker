import os
import sys
import requests
import yfinance as yf
from datetime import datetime, timedelta

# Erzwinge UTF-8 Kodierung für die Konsole (behebt den Emoji 'latin-1' Fehler)
sys.stdout.reconfigure(encoding='utf-8')

# Topic aus den GitHub Secrets auslesen
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "dein_fallback_topic")

# Zu überwachende Titel und ihre Ticker-Symbole
ASSETS = {
    "Dormakaba": "DOKA.SW",
    "Kering": "KER.PA",
    "Beyond Meat": "BYND",
    "Microsoft": "MSFT",
    "Ethereum": "ETH-USD",
    "Chainlink": "LINK-USD"
}

def check_assets():
    print("Starte 2-Stunden-Kursvergleich...")
    
    for name, symbol in ASSETS.items():
        try:
            ticker = yf.Ticker(symbol)
            # 5-Minuten-Intervall-Daten abrufen
            df = ticker.history(period="1d", interval="5m")
            
            if df.empty or len(df) < 2:
                print(f"[{name}] Keine ausreichenden Intraday-Daten verfügbar.")
                continue

            current_time = df.index[-1]
            target_time = current_time - timedelta(hours=2)

            # Suche den Datenpunkt, der am nächsten an 2 Stunden zurückliegt
            df_past = df[df.index <= target_time]
            
            if not df_past.empty:
                ref_price = df_past['Close'].iloc[-1]
                time_diff_str = "letzten 2 Std."
            else:
                ref_price = df['Close'].iloc[0]
                time_diff_str = "Start der Handelszeit"

            current_price = df['Close'].iloc[-1]
            
            # Prozentuale Änderung berechnen
            change_percent = ((current_price - ref_price) / ref_price) * 100
            
            # Währung ermitteln
            currency = ticker.info.get('currency', 'USD')
            if currency == 'USD':
                currency_symbol = "$"
            elif currency == 'EUR':
                currency_symbol = "€"
            elif currency == 'CHF':
                currency_symbol = "CHF"
            else:
                currency_symbol = currency

            # Benachrichtigungs-Details festlegen
            if change_percent >= 0:
                direction_icon = "🚀"
                direction_text = "Anstieg"
                tags = "chart_with_upwards_trend"
            else:
                direction_icon = "📉"
                direction_text = "Rückgang"
                tags = "chart_with_downwards_trend"

            title = f"{direction_icon} {name}: {change_percent:+.2f}% (2h)"
            message = (
                f"{name} ({direction_text})\n"
                f"Aktueller Kurs: {current_price:.2f} {currency_symbol}\n"
                f"Kurs vor {time_diff_str}: {ref_price:.2f} {currency_symbol}\n"
                f"Veränderung: {change_percent:+.2f}%"
            )
            
            # Push-Nachricht senden
            requests.post(
                f"https://ntfy.sh/{NTFY_TOPIC}",
                data=message.encode('utf-8'),
                headers={
                    "Title": title,
                    "Priority": "default",
                    "Tags": tags
                }
            )
            print(f" -> Push-Benachrichtigung gesendet für {name} ({change_percent:+.2f}%)")

        except Exception as e:
            print(f"Fehler bei {name} ({symbol}): {e}")

if __name__ == "__main__":
    check_assets()
