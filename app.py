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
@ShopBoss.route("/panel", methods=["GET","POST"])
def panel():
    conn = db()

    if request.method == "POST":
        if "add" in request.form:
            conn.execute("INSERT INTO products (name,price,image) VALUES (?,?,?)",
                         (request.form["name"], request.form["price"], request.form["image"]))
        if "delete" in request.form:
            conn.execute("DELETE FROM products WHERE id=?", (request.form["id"],))
        conn.commit()
    if "update" in request.form:
        conn.execute("UPDATE products SET name=?, price=?, image=? WHERE id=?",
                 (request.form["name"], request.form["price"], request.form["image"], request.form["id"]))
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()

    html = header() + "<div style='padding:30px;'>"

    html += """
    <form method="post">
        <input name="name" placeholder="Name">
        <input name="price" placeholder="Price">
        <input name="image" placeholder="Image URL">
        <button name="add">Add</button>
    </form><hr>
    """

    for p in products:
        html += f"""
       <form method="post">
    <input type="hidden" name="id" value="{p[0]}">
    
    <input name="name" value="{p[1]}">
    <input name="price" value="{p[2]}">
    <input name="image" value="{p[3]}">

    <button name="update">Update</button>
    <button name="delete">Delete</button>
    </form>
    """

    html += "</div>"
    return html
# -------- ADDRESS --------
@ShopBoss.route("/address", methods=["GET","POST"])
def address():

    # अगर cart empty है → home पर भेजो
    if not session.get("cart"):
        return redirect("/")

    if request.method == "POST":

        # login check
        if "user" not in session:
            return redirect("/login")

        mobile = request.form.get("mobile", "").strip()
        address = request.form.get("address", "").strip()
        payment = request.form.get("payment", "").strip()

        # -------- VALIDATION --------
        if not mobile.isdigit() or len(mobile) != 10:
            return "<h3 style='color:red;'>❌ Enter valid 10-digit mobile number</h3><a href='/address'>Go Back</a>"

        if not address:
            return "<h3 style='color:red;'>❌ Address required</h3><a href='/address'>Go Back</a>"

        # -------- MESSAGE --------
        message = f"""New Order

User: {session.get('user')}
Mobile: {mobile}
Address: {address}
Payment: {payment}

Items:
"""

        conn = db()
        total = 0

        for pid, qty in session.get("cart", {}).items():
            p = conn.execute(
                "SELECT name, price FROM products WHERE id=?",
                (pid,)
            ).fetchone()

            if p:
                name, price = p
                total += price * qty
                message += f"{name} (₹{price}) - Qty: {qty}\n"

        conn.close()

        message += f"\nTotal: ₹{total}"

        # -------- EMAIL SEND --------
        import requests

        r = requests.post(
            "https://api.emailjs.com/api/v1.0/email/send",
            headers={"Content-Type": "application/json"},
            json={
                "service_id": "service_shopboss",
                "template_id": "template_shopboss",
                "user_id": "9bTfVOFVe_u1Mt51L",
                "template_params": {
                    "name": session.get("user"),
                    "email": "kfayizwani@gmail.com",
                    "message": message
                }
            }
        )

        print(r.text)

        # -------- CLEAR CART --------
        session["cart"] = {}

        # -------- SUCCESS UI --------
        return f"""
        <div style="background:#eaeded;height:100vh;display:flex;justify-content:center;align-items:center;">
            <div style="background:white;padding:40px;width:500px;border-radius:10px;text-align:center;">
                
                <div style="font-size:60px;color:green;">✔</div>

                <h2 style="color:#067d62;">Order Placed Successfully</h2>

                <p><b>Mobile:</b> {mobile}</p>
                <p><b>Total Paid:</b> ₹{total}</p>

                <a href="/" style="display:inline-block;margin-top:20px;background:#ffd814;padding:12px 20px;color:black;text-decoration:none;">
                    Continue Shopping
                </a>

            </div>
        </div>
        """

    # -------- FORM UI --------
    return """
<div style="display:flex;justify-content:center;align-items:center;height:100vh;background:#f2f2f2;">
    <form method="post" style="background:white;padding:30px;width:350px;">
        
        <h2 style="text-align:center;">Checkout</h2>

        <input name="mobile" placeholder="Enter Mobile Number"
        style="width:100%;margin:10px 0;padding:8px;" required>

        <input name="address" placeholder="Enter Address"
        style="width:100%;margin:10px 0;padding:8px;" required>
        

        <h3>Payment Options</h3>

        <div style="margin:10px 0;">
            <input type="radio" name="payment" value="Cash on Delivery" onclick="codSelected()" required> Cash on Delivery<br><br>

            <input type="radio" name="payment" value="Online Payment" onclick="showQR()"> Online Payment
        </div>

        <!-- QR -->
        <div id="qrBox" style="display:none;text-align:center;">
            <img src="/static/qr.png" style="width:200px;margin-top:10px;">
            <p>Scan & Pay</p>

            <button type="button" onclick="confirmPayment()"
            style="background:#28a745;color:white;padding:8px;border:none;">
                Confirm Payment
            </button>
        </div>

        <button id="placeOrderBtn"
        style="width:100%;padding:10px;margin-top:15px;background:#ffd814;border:none;">
            Place Order
        </button>
    </form>
</div>

<script>
let paid = false;

function showQR(){
    document.getElementById("qrBox").style.display = "block";
    document.getElementById("placeOrderBtn").disabled = true;
}

function confirmPayment(){
    paid = true;
    document.getElementById("placeOrderBtn").disabled = false;
    alert("Payment Confirmed ✅");
}

function codSelected(){
    document.getElementById("qrBox").style.display = "none";
    document.getElementById("placeOrderBtn").disabled = false;
}

document.querySelector("form").onsubmit = function(){
    let p = document.querySelector('input[name="payment"]:checked');

    if(p && p.value === "Online Payment" && !paid){
        alert("Confirm QR payment first!");
        return false;
    }
}
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