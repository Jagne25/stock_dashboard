from alpaca.trading.client import TradingClient

API_KEY = "PKXBR37EUJIDZ6TEDR57272UZ3"
SECRET   = "EomZsLEN3KXWTVxeGPFggq8Wj8fLNjcZJ9FQXrXvqAsN"

client = TradingClient(API_KEY, SECRET, paper=True)

account = client.get_account()
print(f"Cash:          ${float(account.cash):,.2f}")
print(f"Portfolio val: ${float(account.portfolio_value):,.2f}")
print(f"Buying power:  ${float(account.buying_power):,.2f}")
print("Spojenie funguje!")
