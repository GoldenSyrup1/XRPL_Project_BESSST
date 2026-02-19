import xrpl
from xrpl import *
from xrpl.clients import JsonRpcClient
from xrpl.wallet import generate_faucet_wallet
from xrpl.models.transactions import Payment
from xrpl.transaction import submit_and_wait

# Connecting to TestNet
client = JsonRpcClient("https://s.altnet.rippletest.net:51234")
# fund two test accounts (1,000 XRP each for free)
wallet1 = generate_faucet_wallet(client)
wallet2 = generate_faucet_wallet(client)
print(f"Sender Address: {wallet1.classic_address}")
print(f"Reciever Address: {wallet2.classic_address}")
# preparing payment
my_payment = Payment(account = wallet1.classic_address, amount = xrpl.utils.xrp_to_drops(10), destination = wallet2.classic_address)
# sign and submit the transaction
response = submit_and_wait(my_payment, client, wallet1)

# results
print(f"Transaction result: {response.result["meta"]["TransactionResult"]}")






