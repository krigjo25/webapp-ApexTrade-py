#   Importing responsories
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from markupsafe import Markup
from helpers import apology, login_required, lookup, usd

from lib.config.app_config import DevelopmentConfig


# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config.from_object(DevelopmentConfig)
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == 'POST':
        try:  # Examine for Exceptions

            #   Ensure the user has inputted the fields
            if not request.form['username'] or not request.form['password'] or not request.form['confirmation']:
                raise Exception('User name / password left blank')

            #   Ensure the user name is unique
            for key in db.execute("SELECT * FROM users;"):
                if key['username'] == request.form['username']:
                    raise Exception('Username unavailable')

            #   Ensure the passwords matches
            if str(request.form['password']) != str(request.form['confirmation']):
                raise Exception('passwords miss match')

        except Exception as e:
            return apology(f"{e}", 400)

        #   Insert a new Record
        db.execute('INSERT INTO users (username, hash) VALUES (?,?)',
                   request.form['username'], generate_password_hash(request.form['confirmation']))

        #   Message the user
        flash("Registration Complete, Thank you for registering.")
        return redirect('/login')
    return render_template('register.html')


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    #   Buy a share, sell a share, quote a share
    #   Selecting the user information | add stock_value to users
    user = db.execute('SELECT username, cash, total FROM users WHERE id = ?;', int(session['user_id']))

    # Creates a new tables if it doesnt already exists
    db.execute("""CREATE TABLE IF NOT EXISTS ? (
                                -- Description :    Track user's investments portefolio
                                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                abbrivation TEXT NOT NULL,
                                qty INT NOT NULL,
                                price REAL NOT NULL,
                                total REAL NOT NULL,
                                UNIQUE (abbrivation));""", str(user[0]['username']))

    db.execute("""CREATE TABLE IF NOT EXISTS trading_history (
                                --  Description : Track trading history
                                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                                user_id INTEGER NOT NULL,
                                abbrivation TEXT NOT NULL,
                                status TEXT NOT NULL DEFAULT UNKOWN,
                                qty INT NOT NULL,
                                price REAL NOT NULL,
                                time_stamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                                FOREIGN KEY (user_id) REFERENCES users(id));""")

    return render_template('index.html', userinfo=user,  stocks=db.execute('SELECT  abbrivation, qty, price, total FROM ?;', user[0]['username']), history = db.execute('SELECT * FROM trading_history WHERE user_id =?;', session['user_id']))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    #   Initializing databases
    user = db.execute('SELECT username, cash, total FROM users WHERE id = ?;', session['user_id'])

    if request.method == 'POST':

        try:
            #   Fetch the total price
            share = lookup(request.form['symbol'])
            #   Ensure symbol field is not blank & share exists
            if not request.form['symbol'] or not lookup(request.form['symbol']):
                raise Exception("Blank fields can not be requested / Share Does not exists")

            #   Ensure the user requests a valid quanity
            if not request.form['shares'] or int(request.form['shares']) < 1:
                raise Exception("Minimum one share must be bought")

            #   Ensure the user has enough cash to purchase a share
            if user[0]['cash'] < (int(request.form['shares']) * share['price']): raise Exception(f"You need atlast ${user[0]['cash'] - (int(request.form['shares']) * share['price'])} more to purchase this type of share")

        except Exception as e: return apology(f'{e}', 400)

        #   Updates the transaction history
        db.execute("INSERT INTO trading_history (user_id, abbrivation, status, qty, price) VALUES (?, ?, ?, ?, ?);", session['user_id'], request.form['symbol'], "BOUGHT", request.form['shares'], share['price'])

        #   Message the user
        #   flash(Markup(f"You bought <b>{request.form['shares']}</b> of <b>{share['symbol']}</b>, total paid <b>{price}</b>"))

        #   Calculate total
        total = user[0]['cash']
        for i in db.execute('SELECT * FROM ?', user[0]['username']):
            total += i['total']

        #   Ensure the symbol is not already in the users portofolio
        for row in db.execute('SELECT * FROM ?', user[0]['username']):
            if row['abbrivation'] == request.form['symbol']:

                db.execute("UPDATE ? SET qty = ?, price = ?, total = ? WHERE abbrivation = ?;", user[0]['username'], row['qty'] + int(request.form['shares']),  share['price'], row['total'] + (int(request.form['shares']) * share['price']), request.form['symbol'])

                #   Updates the record with new values
                db.execute('UPDATE users SET cash = ?, total = ? WHERE id = ?;', user[0]['cash'] - (int(request.form['shares']) * share['price']), total, session['user_id'])

                #   Clear memory
                del share

                return render_template('index.html', userinfo=db.execute('SELECT username, cash, total FROM users WHERE id = ?;', session['user_id']),  stocks=db.execute('SELECT abbrivation, qty, price, total FROM ?;', user[0]['username']), history=db.execute('SELECT * FROM trading_history WHERE user_id = ?;', int(session['user_id'])))

        #   Inserting a new element into user's portefolio table
        db.execute("INSERT INTO ? (qty, price, total, abbrivation) VALUES (?,?,?,?);", user[0]['username'], request.form['shares'], share['price'], (int(request.form['shares']) * share['price']), request.form['symbol'])

        #   Updates the record with new values
        db.execute('UPDATE users SET cash = ?, total = ? WHERE id = ?;', user[0]['cash'] - (int(request.form['shares']) * share['price']), total, session['user_id'])
        #   Clear memory
        del share

        return render_template('index.html', userinfo=user,  stocks=db.execute('SELECT  abbrivation, qty, price, total FROM ?;',  user[0]['username']), history=db.execute('SELECT * FROM trading_history WHERE user_id = ?;', int(session['user_id'])))

    return render_template('buy.html')


@app.route("/history")
@login_required
def history():
    user = db.execute('SELECT username, cash, total FROM users WHERE id = ?;', session['user_id'])
    return render_template('index.html', userinfo=user, history=db.execute('SELECT * FROM trading_history WHERE user_id = ?;', int(session['user_id'])), stocks=db.execute('SELECT  abbrivation, qty, price, total FROM ?;', user[0]['username']))


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    user = db.execute('SELECT username, cash, total FROM users WHERE id = ?;', int(session['user_id']))

    if request.method == 'POST' and request.path == '/quote':

        try:
            #   Ensure symbol field is not blank & share exists
            if not request.form['symbol'] or request.form['symbol'].isdigit():
                raise Exception("Blank fields can not be requested / Invalid characters")

            #   Ensure the share exist
            if not lookup(request.form['symbol']):
                raise Exception('Share not found')

        except Exception as e:
            return apology(f"{e}", 400)

        #   Fetch symbol and price
        arg = lookup(request.form['symbol'])

        flash(Markup(f"<b>{arg['symbol']}</b>, costs $<b>{arg['price']}</b>"))

        return render_template('index.html', symbol=arg, userinfo=db.execute('SELECT username, cash, total FROM users WHERE id = ?;', int(session['user_id'])),  stocks=db.execute('SELECT  abbrivation, qty, price, total FROM ?;',  user[0]['username']), history=db.execute('SELECT * FROM trading_history WHERE user_id = ?;', int(session['user_id'])))

    return render_template('index.html')


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    #   Initializing databases
    user = db.execute('SELECT username, cash, total FROM users WHERE id = ?;', session['user_id'])
    if request.method == 'POST' and request.path == '/sell':

        #   Initializing databases
        stocks = db.execute('SELECT * FROM ? WHERE abbrivation = ?;', user[0]['username'], request.form['symbol'])
        user = db.execute('SELECT username, cash, total FROM users WHERE id = ?;', session['user_id'])

        try:

            #   Ensure the user requests a valid quanity
            if int(request.form['shares']) < 1: raise Exception("Minimum one share must be selected")

            #   Ensure the user has enough shares to sell
            if int(stocks[0]['qty']) < int(request.form['shares']): raise Exception('Can not sell more shares than you have available')

        #   Throw an exception
        except Exception as e: return apology(f'{e}', 400)

        #   Fetch the total price
        share = lookup(request.form['symbol'])
        price = float(request.form['shares']) * share['price']

        #   Updates the transaction history
        db.execute("INSERT INTO trading_history (user_id, abbrivation, status, qty, price) VALUES (?, ?, ?, ?, ?);",
                   session['user_id'], request.form['symbol'], "SOLD", int(request.form['shares']), price)

        #   Updates the record with new values
        db.execute('UPDATE users SET cash = ? WHERE id = ?;', float(user[0]['cash']) + price, session['user_id'])

        #   Ensure updates the users portofolio
        db.execute("UPDATE ? SET qty = ?, price = ?, total = ? WHERE abbrivation = ?;", user[0]['username'], stocks[0]['qty'] - int(request.form['shares']), share['price'], stocks[0]['total'] - price, request.form['symbol'])
        db.execute("DELETE FROM ? WHERE qty = 0;", user[0]['username'])

        #   Embeds a message to the user
        flash(Markup(f"You Sold <b>{request.form['shares']}</b><b>{share['symbol']}</b> share, Total paid to your account $<b>{price}</b>"))

        shares = [share['symbol'], request.form['shares'], price]

        #   Clear memory
        del share, price, stocks
        return render_template('index.html', userinfo= db.execute('SELECT username, cash, total FROM users WHERE id = ?;', session['user_id']),  stocks= db.execute('SELECT  abbrivation, qty, price, total FROM ?;',  user[0]['username']), history=db.execute('SELECT * FROM trading_history WHERE user_id = ?;', int(session['user_id'])))
    return render_template('sell.html', options = db.execute('SELECT abbrivation FROM ?;', user[0]['username']))
