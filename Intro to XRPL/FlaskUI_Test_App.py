from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os

from FlaskUI_Test_Models import db, User, NFT
from SecondXRPL import XRPAccount
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountLines

app = Flask(__name__)

# XRPL client
client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

# Local account registry (phone -> XRPAccount object)
accounts_registry = {}

# ------------------ XRPL HELPERS ------------------

def create_xrp_account(phone, username):
    if phone in accounts_registry:
        return accounts_registry[phone]

    account = XRPAccount(username=username)
    accounts_registry[phone] = account
    return account


def get_account_by_phone(phone):
    return accounts_registry.get(phone)


def get_or_create_account(phone):
    if phone in accounts_registry:
        return accounts_registry[phone]

    account = XRPAccount(username=phone)
    accounts_registry[phone] = account
    return account


def mint_nft(image_path, phone, royalty=1000):
    account = get_or_create_account(phone)
    account.create_nft_xrp_token(royalty)
    return account.nft_uri


# ------------------ APP CONFIG ------------------

app.config['SECRET_KEY'] = 'supersecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mandla.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db.init_app(app)

with app.app_context():
    db.create_all()


# ------------------ ROUTES ------------------

# START HERE → Register page
@app.route('/')
def index():
    return redirect(url_for('register'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        phone = request.form['phone']
        username = request.form['username']

        # Create XRPL account
        account = create_xrp_account(phone, username)

        # Save user to database if not exists
        user = User.query.filter_by(phone=phone).first()
        if not user:
            user = User(phone=phone, wallet_address=account.address)
            db.session.add(user)
            db.session.commit()

        flash("Registration successful!")
        return redirect(url_for('dashboard', phone=phone))

    return render_template('register.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        phone = request.form['phone']
        file = request.files['image']

        if not file:
            flash("No file selected!")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Mint NFT
        nft_uri = mint_nft(filepath, phone)

        # Save NFT in DB
        user = User.query.filter_by(phone=phone).first()
        if not user:
            flash("User not found!")
            return redirect(url_for('register'))

        nft = NFT(user_id=user.id, image_path=filepath, nft_id=nft_uri)
        db.session.add(nft)
        db.session.commit()

        flash(f"NFT minted! URI: {nft_uri}")
        return redirect(url_for('dashboard', phone=phone))

    return render_template('upload.html')


@app.route('/create_offer', methods=['POST'])
def create_offer():
    nft_id = request.form['nft_id']
    xrp_amount = float(request.form['xrp_amount'])

    nft = NFT.query.filter_by(nft_id=nft_id).first()
    if not nft:
        flash("NFT not found!")
        return redirect(url_for('register'))

    user = User.query.get(nft.user_id)
    account = get_account_by_phone(user.phone)

    if account:
        account.create_offer_nft(buyer_of_nft=None, xrp_amount=xrp_amount)
        flash(f"Offer created for {xrp_amount} XRP")
    else:
        flash("XRPL account not found.")

    return redirect(url_for('dashboard', phone=user.phone))


@app.route('/dashboard/<phone>')
def dashboard(phone):
    user = User.query.filter_by(phone=phone).first()
    if not user:
        flash("User not found!")
        return redirect(url_for('register'))

    nfts = NFT.query.filter_by(user_id=user.id).all()
    account = get_account_by_phone(phone)

    holdings = {}
    if account:
        holdings['XRP'] = account.get_xrp_balance()

        # Get token balances
        request_obj = AccountLines(account=account.address, ledger_index="validated")
        response = client.request(request_obj)

        token_balances = {}
        for line in response.result.get("lines", []):
            token_balances[line["currency"]] = line["balance"]

        holdings['tokens'] = token_balances

    return render_template(
        'dashboard.html',
        user=user,
        nfts=nfts,
        holdings=holdings
    )


# ------------------ RUN ------------------

if __name__ == "__main__":
    app.run(debug=True)