import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd, password_check

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    # implement help from stackexchange
    rows = db.execute(
    """
        SELECT symbol, SUM(shares) as totalshares
        FROM history
        WHERE user_id = :user_id
        GROUP BY symbol
    """, user_id=session["user_id"])
    # create a local variable
    totals_assets = 0
    totals = []
    for row in rows:
        stock = lookup(row["symbol"])
        totals.append({
            "symbol" : stock["symbol"],
            "name"   : stock["name"],
            "shares" : row["totalshares"],
            "price"  : usd(stock["price"]),
            "total"  : usd(stock["price"] * row["totalshares"])
        })
        totals_assets += stock["price"] * row["totalshares"]
    # cash avail
    cash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id = session["user_id"])[0]["cash"]
    # grand total
    totals_assets += cash

    return render_template("index.html", totals=totals, cash=usd(cash),totals_assets=usd(totals_assets))



@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        find = lookup(request.form.get("symbol"))
        # check for symbol exist
        if find == None:
            return apology("invalid symbols", 400)
        # check for shares and casting into int
        shares = int(request.form.get("shares"))
        #  look up a stock’s current price * shares to find total values
        price = find["price"] * shares
        # SELECT how much cash the user currently has in users
        user = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])

        cash = user[0]["cash"]
        # check if the user can afford the shares or not
        if cash < price:
            return apology("insufficient cash!", 400)
        else:
            # update DB (cash - values)
            db.execute("UPDATE users SET cash = cash - :price WHERE id = :user_id", price=price, user_id=session["user_id"])
            # add transaction to history
            db.execute("INSERT INTO history (user_id, symbol, operation, shares, price) VALUES (:user_id, :symbol, 'BUY', :shares, :price)",
            user_id = session["user_id"],
            symbol = request.form.get("symbol"),
            shares = shares,
            price = find["price"])

            # if transaction succes, flash the user
            flash("Bought!")
            # return to index to see if the transaction was updated
            return redirect("/")
    else:
        return render_template("buy.html")

# DONE!!

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # get spesific table from history
    rows = db.execute("SELECT symbol, operation, shares, price, time FROM history WHERE user_id = :user_id",
                       user_id = session["user_id"])
    # itereate through row
    for i in range(len(rows)):
        rows[i]["price"] = usd(rows[i]["price"])

    return render_template("history.html", rows=rows)



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

# CLEAR!!

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

# CLEAR !!

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Get stock quote."""
    if request.method == "POST":
        # add cash
        db.execute("UPDATE users SET cash = cash + :add WHERE id = :user_id", add = request.form.get("money"), user_id=session["user_id"])
        flash("Thanks for the Cash!")
        return redirect("/")
    else:
        return render_template("add.html")
# DONE!!

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        find = lookup(request.form.get("symbol"))
        if find == None:
            return apology("symbol don't exist!", 400)
        else:
            return render_template("quoted.html", name=find["name"],symbol=find["symbol"],price=usd(find["price"]))
    else:
        return render_template("quote.html")
# DONE!!

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        passwd = password

         # check username was submitted
        if not username:
            return apology("must provide username", 400)

        # check password was submitted
        elif not password:
            return apology("must provide password", 400)

        # check confirmation password was submitted
        elif not request.form.get("confirmation"):
            return apology("re-type ur password", 400)

        # check Password match with Confirmation
        elif not request.form.get("password") == request.form.get("confirmation"):
             return apology("passwords are not the same", 400)

        elif (password_check(passwd)):
            return apology("have at least one number,upper,lower,special symbol,and min 6 long", 400)
        #check exist username
        exist = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))
        if exist:
            return apology("username already exist!", 400)
        else:
            pass
        # insert to database
        result = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                            username=request.form.get("username"),
                            hash=generate_password_hash(request.form.get("password")))

        #session
        session["user_id"] = result

        # redirect main root
        return redirect("/")

    else:
        return render_template("register.html")
# DONE!

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "POST":
        find = lookup(request.form.get("symbol"))
        if not request.form.get("symbol") or find == None:
            return apology("missing stock", 400)

        # check for shares and casting into int
        stock = int(request.form.get("shares"))
        # check for shares
        if stock == None or stock < 1:
            return apology("Invalid Shares!", 400)

        #  look up a stock’s current price * shares to find total values
        price = find["price"] * stock

        # get symbol
        symbol = request.form.get("symbol").upper()

        # get user cash
        user = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])
        cash = user[0]["cash"]

        # get user shares
        rows = db.execute("SELECT symbol, SUM(shares) as totalshares FROM history WHERE user_id = :user_id GROUP BY symbol",
                           user_id=session["user_id"])
        for row in rows:
            if row["symbol"] == symbol:
                if stock > row["totalshares"]:
                    return apology("insufficient shares!", 400)

        # update DB (cash + values)
        db.execute("UPDATE users SET cash = cash + :price WHERE id = :user_id", price=price, user_id=session["user_id"])
        # checked!

        # update to history
        db.execute("INSERT INTO history (user_id, symbol, operation, shares, price) VALUES (:user_id, :symbol, 'SELL', :shares, :price)",
            user_id = session["user_id"],
            symbol = symbol,
            shares = stock,
            price = find["price"])

        # update shares
        if row["totalshares"] == stock:
            db.execute("DELETE FROM history WHERE id = :user_id AND symbol = :symbol",
                        user_id=session["user_id"], symbol=symbol)

        #  update DB shares
        elif row["totalshares"] > stock:
            db.execute("UPDATE history SET shares = shares - :stock WHERE id = :user_id", stock=stock, user_id=session["user_id"])

        # if transaction succes, flash the user
        flash("Sold!")
        # return to index to see if the transaction was updated
        return redirect("/")

    else:
        rows = db.execute("SELECT symbol FROM history WHERE user_id = :user_id GROUP BY symbol", user_id=session["user_id"])
        return render_template("sell.html", symbols=[row["symbol"].upper() for row in rows])


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
