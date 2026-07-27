import os
import requests
import yfinance as yf

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

# Schwellenwert für den Anstieg in Prozent (0.1 = ab +0,1% Anstieg)
MIN_RISE_PERCENT = 0.1
LOOKBACK_PERIOD = "1d"  # Vergleichszeitraum (1 Tag / 24 Stunden)

def check_assets():
    print("Starte Aktien- & Crypto-Überprüfung...")
    
    for name, symbol in ASSETS.items():
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=LOOKBACK_PERIOD)
            
            if df.empty or len(df) < 2:
                print(f"[{name}] Keine ausreichenden Kursdaten gefunden.")
                continue

            ref_price = df['Close'].iloc[0]
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

            print(f"[{name}] Aktuell: {current_price:.2f} {currency_symbol} | Änderung: {change_percent:+.2f}%")

            # Nur benachrichtigen, wenn der Kurs steigt
            if change_percent >= MIN_RISE_PERCENT:
                title = f"🚀 {name}: +{change_percent:.2f}%"
                message = (
                    f"{name} steigt!\n"
                    f"Aktueller Kurs: {current_price:.2f} {currency_symbol}\n"
                    f"Referenzkurs ({LOOKBACK_PERIOD}): {ref_price:.2f} {currency_symbol}\n"
                    f"Anstieg: +{change_percent:.2f}%"
                )
                
                requests.post(
                    f"https://ntfy.sh/{NTFY_TOPIC}",
                    data=message.encode('utf-8'),
                    headers={
                        "Title": title,
                        "Priority": "default",
                        "Tags": "chart_with_upwards_trend,rocket"
                    }
                )
                print(f" -> Push-Benachrichtigung gesendet für {name}")
            else:
                print(f" -> Kein Anstieg. Keine Benachrichtigung gesendet.")

        except Exception as e:
            print(f"Fehler bei {name} ({symbol}): {e}")

if __name__ == "__main__":
    check_assets()
