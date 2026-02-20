import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.core.keypairs import generate_seed, derive_keypair
from xrpl.account import get_balance
from xrpl.wallet import Wallet, generate_faucet_wallet
from xrpl.transaction import submit_and_wait
from xrpl.models import Payment, Tx
from xrpl.models.requests import AccountInfo, AccountLines

from xrpl.utils import xrp_to_drops
from xrpl.models.transactions import TrustSet, OfferCreate
from xrpl.models.amounts import IssuedCurrencyAmount


# Connecting to TestNet
client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

class XRPAccount():
    def __init__(self, username):
        self.username = username
        self.wallet = Wallet.create()
        self.address = self.wallet.classic_address
        self.seed = self.wallet.seed
        self.private_key = self.wallet.private_key
        self.public_key = self.wallet.public_key
        generate_faucet_wallet(client = client, wallet = self.wallet)

    def send_xrp(self, xrp_amount, recieving_wallet):
        if float(xrp_amount) > float(recieving_wallet.get_account_balance()):
            return ("Sorry. You are sending more XRP than you have in your wallet. If you wish" +
                    " to send XRP, try lowering the amount.")
        payment = Payment(
            account=self.address,
            amount=xrpl.utils.xrp_to_drops(float(xrp_amount)),
            destination=recieving_wallet.address,
        )
        try:
            payment_response = submit_and_wait(payment, client, self.wallet)
            print("Transaction was submitted.")

            # Create a "Tx" request to look up the transaction on the ledger
            tx_response = client.request(Tx(transaction=payment_response.result["hash"]))

            # Check whether the transaction was actually validated on ledger
            print("Validated:", tx_response.result["validated"])
        except xrpl.transaction.XRPLReliableSubmissionException as e:
            return f"Submit failed: {e}"



    def get_account_balance(self):
        acct_info_request = AccountInfo(
            account=self.wallet.classic_address,
            ledger_index="validated",
        )

        # Send the request and get the response
        response = client.request(acct_info_request)
        balance_drops = response.result['account_data']['Balance']

        balance_xrp = int(balance_drops) / 1000000
        return balance_xrp
    def create_TrustSet(self, currency_code, value, recipient):
        trust_set_tx = TrustSet(
            account=self.address,
            limit_amount=IssuedCurrencyAmount(
                currency=currency_code,
                issuer=recipient.address,
                value=value  # I am willing to hold up to value [currency code]
            )
        )
        response = submit_and_wait(trust_set_tx, client, self.wallet)
        if response.is_successful():
            print(f"Success! Your wallet can now hold {currency_code}.")
        else:
            print("Something went wrong.")
    def check_TrustSet(self):
        request = AccountLines(
            account=self.address,
            ledger_index="validated"
        )

        response = client.request(request)

        # 2. Get the list of lines (this contains currency, issuer, balance, etc.)
        all_lines = response.result.get("lines", [])
        if not all_lines:
            print("You have no trust lines. Your wallet is 'clean'.")
        else:
            print(f"You have {len(all_lines)} trust line(s) active.")
            for line in all_lines:
                print(f"- {line['currency']} from issuer {line['account']}")

    def send_token(self, currency_code, amount, recipient):
            payment = Payment(
                account=self.address,
                destination=recipient.address,
                amount=IssuedCurrencyAmount(
                    currency=currency_code,
                    issuer=self.address,
                    value=str(amount)
                )
            )

            submit_and_wait(payment, client, self.wallet)

    def create_offer_buy_xrp(self, aud_amount, xrp_amount, issuer_wallet):
            offer = OfferCreate(
                account=self.address,

                taker_pays=IssuedCurrencyAmount(
                    currency="AUD",
                    issuer=issuer_wallet.address,
                    value=str(aud_amount)
                ),

                taker_gets=xrp_to_drops(xrp_amount)
            )

            response = submit_and_wait(offer, client, self.wallet)

            if response.is_successful():
                print("Offer successfully placed on DEX.")
            else:
                print("Offer failed.")

    def create_offer_sell_xrp(self, xrp_amount, aud_amount, issuer_wallet):
        offer = OfferCreate(
            account=self.address,

            taker_pays=xrp_to_drops(xrp_amount),

            taker_gets=IssuedCurrencyAmount(
                currency="AUD",
                issuer=issuer_wallet.address,
                value=str(aud_amount)
            )
        )

        response = submit_and_wait(offer, client, self.wallet)

        if response.is_successful():
            print("Sell offer successfully placed.")
        else:
            print("Offer failed.")

    def build_amount(self, currency, value, issuer=None):

            # Returns correct XRPL amount format depending on XRP or token


            if currency.upper() == "XRP":
                return xrp_to_drops(value)

            return IssuedCurrencyAmount(
                currency=currency,
                issuer=issuer.address,
                value=str(value)
            )

    def can_hold_currency(self, currency, issuer):
            if currency.upper() == "XRP":
                return True

            request = AccountLines(
                account=self.address,
                ledger_index="validated"
            )

            response = client.request(request)
            lines = response.result.get("lines", [])

            for line in lines:
                if line["currency"] == currency and line["account"] == issuer.address:
                    return True

            return False

    def get_token_balance(self, currency, issuer=None):

        if currency.upper() == "XRP":
            return self.get_account_balance()

        request = AccountLines(
            account=self.address,
            ledger_index="validated"
        )

        response = client.request(request)

        for line in response.result.get("lines", []):
            if line["currency"] == currency and line["account"] == issuer.address:
                return float(line["balance"])

        return 0.0

    def create_offer(
            self,
            pay_currency,
            pay_amount,
            get_currency,
            get_amount,
            pay_issuer=None,
            get_issuer=None
    ):

        # Check holding permissions
        if not self.can_hold_currency(get_currency, get_issuer):
            print(f"You cannot hold {get_currency}. Create trust line first.")
            return

        # Check balance
        balance = self.get_token_balance(pay_currency, pay_issuer)

        if balance < pay_amount:
            print(f"Insufficient balance. You have {balance} {pay_currency}")
            return

        taker_pays = self.build_amount(pay_currency, pay_amount, pay_issuer)
        taker_gets = self.build_amount(get_currency, get_amount, get_issuer)

        offer = OfferCreate(
            account=self.address,
            taker_pays=taker_pays,
            taker_gets=taker_gets
        )

        response = submit_and_wait(offer, client, self.wallet)

        if response.is_successful():
            print(f"Offer created: Pay {pay_amount} {pay_currency} "
                  f"to get {get_amount} {get_currency}")
        else:
            print("Offer failed")

    def get_all_holdings(self):

        holdings = {"XRP": self.get_account_balance()}

        request = AccountLines(
            account=self.address,
            ledger_index="validated"
        )

        response = client.request(request)

        for line in response.result.get("lines", []):
            currency = line["currency"]
            balance = float(line["balance"])
            issuer = line["account"]

            holdings[f"{currency}:{issuer}"] = balance

        return holdings
    def print_all_holdings(self):
        holdings = self.get_all_holdings()

        print("You can sell:")
        for asset, balance in holdings.items():
            print(asset, balance)

# standard account will always have 100 xrp

acct1 = XRPAccount("Joe Biden")
acct2 = XRPAccount("Obama69")
print(acct1.get_account_balance())
print(acct2.get_account_balance())
acct1.send_xrp(5, acct2)
acct2.create_TrustSet("AUD", 1000, acct1)
acct2.check_TrustSet()
print(acct1.get_account_balance())
print(acct2.get_account_balance())

acct2.create_offer(
    pay_currency="XRP",
    pay_amount=50,
    get_currency="AUD",
    get_amount=100,
    get_issuer=acct1
)









