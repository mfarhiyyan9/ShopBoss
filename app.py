from flask import Flask, request, redirect, session
import sqlite3
import requests

ShopBoss = Flask(__name__)
ShopBoss.secret_key = "secret123"

# -------- DATABASE --------
def db():
    return sqlite3.connect("shopboss.db")

# -------- COMMON FORM UI --------
def form_ui(title, fields, button):
    inputs = ""
    for f in fields:
        inputs += f

    return f"""
    <div style="display:flex;justify-content:center;align-items:center;height:100vh;background:#f2f2f2;">
        <form method="post" style="background:white;padding:30px;width:300px;">
            <h2 style="text-align:center;">{title}</h2>
            {inputs}
            <button style="width:100%;padding:10px;background:#ffd814;border:none;">
                {button}
            </button>
        </form>
    </div>
    """
# --------- HEADER ----------
def header():
    cart = session.get("cart", {})
    count = sum(cart.values())

    return f"""
    <div style="background:#131921;color:white;padding:10px;display:flex;align-items:center;">

        <!-- LOGO -->
        <div style="color:#ff9900;font-size:22px;font-weight:bold;margin-right:20px;">
            ShopBoss
        </div>

        <!-- SEARCH BAR (CENTER BIG) -->
        <form action="/" method="get" style="flex:1;display:flex;margin:0 20px;">
            <input name="q" placeholder="Search products"
                   style="flex:1;padding:9px;border:none;font-size:13px;">
            <button style="background:#febd69;border:none;padding:8px 20px;">
                Search
            </button>
        </form>

        <!-- RIGHT SIDE MENU -->
        <div style="display:flex;gap:20px;white-space:nowrap;">
            <a href="/" style="color:white;text-decoration:none;">Home</a>
            <a href="/cart" style="color:white;text-decoration:none;">Cart ({count})</a>
            <a href="/admin" style="color:white;text-decoration:none;">Admin</a>
            <a href="/signup" style="color:white;text-decoration:none;">SignUp</a>
        </div>

    </div>
    """
# -------- HOME --------
@ShopBoss.route("/")
def home():
    query = request.args.get("q")   # 🔥 GET SEARCH TEXT

    conn = db()

    # 🔍 SEARCH LOGIC
    if query:
        products = conn.execute(
            "SELECT * FROM products WHERE LOWER(name) LIKE LOWER(?)",
            ('%' + query + '%',)
        ).fetchall()
    else:
        products = conn.execute("SELECT * FROM products").fetchall()

    conn.close()

    html = header() + '<div style="display:flex;flex-wrap:wrap;padding:25px;background:#eaeded;">'

    if not products:
        html += "<h2 style='padding:20px;'>No products found</h2>"

    for p in products:
        html += f"""
        <div style="background:white;width:120px;margin:10px;padding:20px;">
            <img src="{p[3]}" style="width:100%;height:135px;">
            <h4>{p[1]}</h4>
            <b> ₹{p[2]}</b>
            <a href="/add/{p[0]}" style="display:block;background:#ffd814;padding:10px;text-align:center;color:black;text-decoration:none">
                Add to Cart
            </a>
        </div>
        """

    html += "</div>"
    return html

# -------- ADD --------
@ShopBoss.route("/add/<int:id>")
def add(id):
    cart = session.get("cart", {})
    cart[str(id)] = cart.get(str(id), 0) + 1
    session["cart"] = cart
    return redirect("/cart")

# -------- CART --------
@ShopBoss.route("/cart")
def cart():
    cart = session.get("cart", {})
    conn = db()

    total = 0
    html = header() + '<div style="display:flex;padding:30px;background:#eaeded;">'

    html += '<div style="width:70%;">'

    for pid, qty in cart.items():
        p = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
        if p:
            subtotal = p[2] * qty
            total += subtotal

            html += f"""
            <div style="background:white;margin:10px;padding:15px;display:flex;">
                <img src="{p[3]}" style="width:150px;height:170px;margin-right:15px;">
                <div>
                    <h3>{p[1]}</h3>
                    <p>₹{p[2]} × {qty}</p>

<div style="margin:10px 0;">
    <a href="/dec/{pid}" style="padding:5px 10px;background:#ddd;text-decoration:none;">-</a>
    <a href="/inc/{pid}" style="padding:5px 10px;background:#ddd;text-decoration:none;">+</a>
    <a href="/remove/{pid}" style="padding:5px 10px;background:green;color:white;text-decoration:none;">Delete</a>
</div>

<b>Subtotal: ₹{subtotal}</b>
                </div>
            </div>
            """

    html += "</div>"

    html += f"""
    <div style="width:30%;">
        <div style="background:white;padding:20px;">
            <h2>Subtotal</h2>
            <h3>₹{total}</h3>
            <a href="/address" style="display:block;background:#ffd814;padding:12px;text-align:center;color:black;text-decoration:none">
                Proceed to Buy
            </a>
        </div>
    </div>
    """

    html += "</div>"
    conn.close()
    return html
# -------- INCREASE --------
@ShopBoss.route("/inc/<id>")
def inc(id):
    cart = session.get("cart", {})
    cart[id] = cart.get(id, 0) + 1
    session["cart"] = cart
    return redirect("/cart")

# -------- DECREASE --------
@ShopBoss.route("/dec/<id>")
def dec(id):
    cart = session.get("cart", {})
    if id in cart:
        cart[id] -= 1
        if cart[id] <= 0:
            del cart[id]
    session["cart"] = cart
    return redirect("/cart")

# -------- DELETE --------
@ShopBoss.route("/remove/<id>")
def remove(id):
    cart = session.get("cart", {})
    if id in cart:
        del cart[id]
    session["cart"] = cart
    return redirect("/cart")
# -------- LOGIN --------
@ShopBoss.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        conn = db()
        user = conn.execute("SELECT * FROM users WHERE username=? AND password=?",
                            (request.form["u"], request.form["p"])).fetchone()
        conn.close()

        if user:
            session["user"] = request.form["u"]
            return redirect("/")

        return "INVALID LOGIN"
        

    return form_ui("----------User Login---------", [
        '<input name="m" placeholder="Mobile No" style="width:100%;padding:10px;margin:10px 0;">',
        '<input name="u" placeholder="Username" style="width:100%;padding:10px;margin:10px 0;">',
        '<input name="p" type="password" placeholder="Password" style="width:100%;padding:10px;margin:10px 0;">'
    ], "LOGIN")
# -------- SIGNUP --------
@ShopBoss.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        conn = db()
        conn.execute("INSERT INTO users (username,password) VALUES (?,?)",
                     (request.form["u"], request.form["p"]))
        conn.commit()
        conn.close()
        return redirect("/login")

    return form_ui("----------User Sign Up---------", [
        '<input name="m" placeholder="Mobile No" style="width:100%;padding:10px;margin:10px 0;">',
        '<input name="u" placeholder="Username" style="width:100%;padding:10px;margin:10px 0;">',
        '<input name="p" type="password" placeholder="Password" style="width:100%;padding:10px;margin:10px 0;">'
    ], "SIGN UP")

# -------- ADMIN --------
@ShopBoss.route("/admin", methods=["GET","POST"])
def admin():
    if request.method == "POST":
        if (request.form["u"] in ["admin","owner"]) and (request.form["p"] in ["admin","owner"]):
            return redirect("/panel")

    return form_ui("----------Admin Login---------", [
        '<input name="u" placeholder="Username" style="width:100%;padding:10px;margin:10px 0;">',
        '<input name="p" type="password" placeholder="Password" style="width:100%;padding:10px;margin:10px 0;">'
    ], "LOGIN")

# -------- PANEL --------

@ShopBoss.route("/panel", methods=["GET", "POST"])
def panel():
    # 🔒 Protect panel (optional but recommended)
    if session.get("admin") != True:
        return redirect("/admin")

    conn = db()

    if request.method == "POST":
        action = request.form.get("action")

        name = request.form.get("name")
        price = request.form.get("price")
        image = request.form.get("image")
        pid = request.form.get("id")

        # 🟢 ADD PRODUCT
        if action == "add":
            conn.execute(
                "INSERT INTO products (name,price,image) VALUES (?,?,?)",
                (name, price, image)
            )

        # 🔴 DELETE PRODUCT
        elif action == "delete":
            conn.execute(
                "DELETE FROM products WHERE id=?",
                (pid,)
            )

        # 🔵 UPDATE PRODUCT (FIXED ✅)
        elif action == "update":
            conn.execute(
                "UPDATE products SET name=?, price=?, image=? WHERE id=?",
                (name, price, image, pid)
            )

        conn.commit()

    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()

    # 🖼️ UI
    html = header() + """
    <div style='padding:30px;background:#eaeded;'>

    <h2>Admin Panel</h2>

    <!-- ADD PRODUCT -->
    <form method="post" style="background:white;padding:15px;margin-bottom:20px;">
        <h3>Add Product</h3>
        <input name="name" placeholder="Product Name" required style="padding:8px;margin:5px;">
        <input name="price" placeholder="Price" required style="padding:8px;margin:5px;">
        <input name="image" placeholder="Image URL" required style="padding:8px;margin:5px;">
        <button name="action" value="add" style="padding:8px 15px;background:green;color:white;border:none;">
            Add
        </button>
    </form>

    <hr>
    """

    # 📦 PRODUCT LIST
    for p in products:
        html += f"""
        <form method="post" style="background:white;margin:10px;padding:15px;display:flex;align-items:center;gap:10px;">

            <input type="hidden" name="id" value="{p[0]}">

            <img src="{p[3]}" style="width:80px;height:80px;object-fit:cover;">

            <input name="name" value="{p[1]}" style="padding:5px;width:150px;">
            <input name="price" value="{p[2]}" style="padding:5px;width:80px;">
            <input name="image" value="{p[3]}" style="padding:5px;width:200px;">

            <button name="action" value="update"
                style="background:blue;color:white;padding:6px 12px;border:none;">
                Update
            </button>

            <button name="action" value="delete"
                style="background:red;color:white;padding:6px 12px;border:none;">
                Delete
            </button>

        </form>
        """

    html += "</div>"
    return html
    #--- ADDRESS --------
from flask import request, session, redirect, send_from_directory

# ✅ QR ROUTE (since qr.png is in main folder)
@ShopBoss.route('/qr.png')
def qr():
    return send_from_directory('.', 'qr.png')


# ✅ ADDRESS + PAYMENT PAGE
@ShopBoss.route("/address", methods=["GET", "POST"])
def address():

    if request.method == "POST":
        name = request.form.get("name")
        mobile = request.form.get("mobile")
        address = request.form.get("address")
        payment = request.form.get("payment")

        cart = session.get("cart", {})

        # Convert product IDs to names (IMPORTANT FIX)
        product_details = []
        conn = db()
        cur = conn.cursor()

        for pid, qty in cart.items():
            cur.execute("SELECT name FROM products WHERE id=?", (pid,))
            product = cur.fetchone()
            if product:
                product_details.append(f"{product[0]} (x{qty})")

        conn.close()

        order_summary = ", ".join(product_details)

        message = f"""
✅ ORDER CONFIRMED

👤 Name: {name}
📞 Mobile: {mobile}
🏠 Address: {address}

🛒 Products:
{order_summary}

💳 Payment: {payment}
"""

        print(message)  # You can replace with email/WhatsApp later

        session["cart"] = {}  # clear cart

        return f"""
        <h2 style="text-align:center;">✅ Order Placed Successfully</h2>
        <p style="text-align:center;">{message}</p>
        <div style="text-align:center;">
            <a href="/">Continue Shopping</a>
        </div>
        """

    # ✅ FRONTEND UI
    return """
    <h2 style="text-align:center;">Enter Delivery Details</h2>

    <form method="POST" style="width:300px;margin:auto;">

        <input type="text" name="name" placeholder="Full Name" required
        style="width:100%;padding:10px;margin:5px;"><br>

        <input type="text" name="mobile" placeholder="Mobile Number" required
        style="width:100%;padding:10px;margin:5px;"><br>

        <textarea name="address" placeholder="Full Address" required
        style="width:100%;padding:10px;margin:5px;"></textarea><br>

        <h3>Select Payment Method</h3>

        <input type="radio" name="payment" value="Cash on Delivery" onclick="codSelected()" required> COD<br>

        <input type="radio" name="payment" value="Online Payment" onclick="showQR()"> Online Payment<br>

        <div id="qrBox" style="display:none;text-align:center;">
            <p>Scan & Pay</p>

            <img src="/qr.png"
                 style="width:200px;margin-top:10px;"
                 onerror="this.src='https://via.placeholder.com/200?text=QR+Missing'">

            <br><br>

            <button type="button" onclick="confirmPayment()">
                I Have Paid
            </button>
        </div>

        <br>

        <button type="submit" id="placeOrderBtn">Place Order</button>

    </form>

    <script>
    document.addEventListener("DOMContentLoaded", function(){

        let paid = false;

        window.showQR = function(){
            document.getElementById("qrBox").style.display = "block";
            document.getElementById("placeOrderBtn").disabled = true;
        }

        window.confirmPayment = function(){
            paid = true;
            document.getElementById("placeOrderBtn").disabled = false;
            alert("Payment Confirmed ✅");
        }

        window.codSelected = function(){
            document.getElementById("qrBox").style.display = "none";
            document.getElementById("placeOrderBtn").disabled = false;
        }

        document.querySelector("form").onsubmit = function(){
            let p = document.querySelector('input[name="payment"]:checked');

            if(p && p.value === "Online Payment" && !paid){
                alert("Please confirm QR payment first!");
                return false;
            }
        }

    });
    </script>
    """
# ================== #
conn = db()
conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT)")
conn.commit()
conn.close()
# -------- RUN --------
if __name__ == "__main__":
    ShopBoss.run(debug=True)

# 9bTfVOFVe_u1Mt51L
