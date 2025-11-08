import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from models.user_model import find_user_by_email, create_user
from models.product_model import create_product, get_all_products
from models.product_model import get_product_by_id  # make sure this exists

from models.product_model import delete_product_by_id, update_product_by_id

app = Flask(__name__)
app.secret_key = "change_this_secret_for_production"
bcrypt = Bcrypt(app)

# --- Image Upload Config ---
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ----- Home -----
@app.route('/')
def home():
    products = get_all_products()
    logged_in = 'user' in session
    username = session.get('user') if logged_in else None
    return render_template('home.html', products=products, logged_in=logged_in, username=username)

# ----- Register -----
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name').strip()
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')

        if not name or not email or not password:
            flash("Please fill all fields", "danger")
            return redirect(url_for('register'))

        if find_user_by_email(email):
            flash("Email already registered. Please login.", "warning")
            return redirect(url_for('login'))

        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        create_user(name, email, hashed)

        session['user'] = name
        flash("Registration successful! Logged in as " + name, "success")
        return redirect(url_for('home'))

    return render_template('register.html')

# ----- Login -----
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')

        user = find_user_by_email(email)
        if user and bcrypt.check_password_hash(user['password'], password):
            session['user'] = user['name']
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid credentials", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

# ----- Logout -----
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out", "info")
    return redirect(url_for('home'))

#####333333333333333333333333333333333333
# ----- Manage Products -----
@app.route('/manage-products')
def manage_products():
    if 'user' not in session:
        flash("Please login to manage products", "warning")
        return redirect(url_for('login'))

    products = get_all_products()
    return render_template('manage_products.html', products=products)

# ----- Delete Product -----
@app.route('/delete-product/<product_id>')
def delete_product(product_id):
    if 'user' not in session:
        flash("Please login first", "warning")
        return redirect(url_for('login'))

    delete_product_by_id(product_id)
    flash("Product deleted successfully!", "info")
    return redirect(url_for('manage_products'))


@app.route('/update-product/<product_id>', methods=['GET', 'POST'])
def update_product(product_id):
    if 'user' not in session:
        flash("Please login to update products", "warning")
        return redirect(url_for('login'))

    product = get_product_by_id(product_id)
    if not product:
        flash("Product not found", "danger")
        return redirect(url_for('manage_products'))

    if request.method == 'POST':
        title = request.form.get('title')
        brand = request.form.get('brand')
        category = request.form.get('category')
        price = float(request.form.get('price') or 0)
        stock = int(request.form.get('stock') or 0)
        description = request.form.get('description')

        # --- Image Update ---
        images = product.get("images", [])  # existing images list
        if 'images' in request.files:
            files = request.files.getlist('images')
            new_images = []
            for i, file in enumerate(files):
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    new_images.append(filepath)
            if new_images:
                images = new_images  # replace with new ones

        update_data = {
            "title": title,
            "brand": brand,
            "category": category,
            "price": price,
            "stock": stock,
            "description": description,
            "images": images
        }

        update_product_by_id(product_id, update_data)
        flash("Product updated successfully!", "success")
        return redirect(url_for('manage_products'))

    return render_template('update_product.html', product=product)











# ----- Product Detail -----
@app.route('/product/<product_id>')
def product_detail(product_id):
    product = get_product_by_id(product_id)
    if not product:
        flash("Product not found", "danger")
        return redirect(url_for('home'))

    logged_in = 'user' in session
    username = session.get('user') if logged_in else None
    return render_template('product_detail.html', product=product, logged_in=logged_in, username=username)

# ----- Add Product -----
@app.route('/add-product', methods=['GET', 'POST'])
def add_product():
    if 'user' not in session:
        flash("Please login to add products", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        # --- Form Fields ---
        name = request.form.get('name').strip()
        title = request.form.get('title').strip()
        description = request.form.get('description').strip()
        brand = request.form.get('brand').strip()
        price = float(request.form.get('price') or 0)
        stock = int(request.form.get('stock') or 0)
        sizes = [s.strip() for s in request.form.get('sizes', '').split(',') if s.strip()]
        colors = [c.strip() for c in request.form.get('colors', '').split(',') if c.strip()]
        category = request.form.get('category').strip()

        # --- Handle Multiple Image Uploads ---
        images = []
        if 'images' in request.files:
            files = request.files.getlist('images')
            for i, file in enumerate(files):
                if i >= 5:  # max 5 images
                    break
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    images.append(filepath)  # store path in DB

        product = {
            "name": name,
            "title": title,
            "description": description,
            "brand": brand,
            "price": price,
            "stock": stock,
            "sizes": sizes,
            "colors": colors,
            "category": category,
            "images": images
        }

        create_product(product)
        flash("Product added successfully", "success")
        return redirect(url_for('home'))    

    return render_template('add_product.html')


# ----------------- Cart Routes -----------------

@app.route('/cart')
def view_cart():
    init_cart()
    cart = session.get('cart', {})
    total, count = cart_total_and_count()
    return render_template('cart.html', cart=cart, total=total, count=count)

@app.route('/cart/add/<product_id>', methods=['POST'])
def add_to_cart(product_id):
    """
    Expects a form field 'quantity' (optional). If called from product page,
    make form action point to url_for('add_to_cart', product_id=product_id).
    """
    init_cart()
    product = get_product_by_id(product_id)
    if not product:
        flash("Product not found", "danger")
        return redirect(url_for('home'))

    try:
        qty = int(request.form.get('quantity', 1))
        if qty < 1:
            qty = 1
    except ValueError:
        qty = 1

    cart = session.get('cart', {})

    # If product already in cart, increment quantity
    if product_id in cart:
        cart[product_id]['qty'] = cart[product_id].get('qty', 0) + qty
    else:
        # store minimal serializable fields
        image = None
        images = product.get('images')
        if isinstance(images, list) and len(images) > 0:
            image = images[0]
        cart[product_id] = {
            "title": product.get('title') or product.get('name') or "",
            "price": float(product.get('price') or 0),
            "qty": qty,
            "image": image
        }

    session['cart'] = cart
    flash(f"Added {qty} x {cart[product_id]['title']} to cart", "success")
    return redirect(request.referrer or url_for('product_detail', product_id=product_id))

@app.route('/cart/update/<product_id>', methods=['POST'])
def update_cart_item(product_id):
    """
    Expects form field 'quantity' to set the exact quantity.
    """
    init_cart()
    cart = session.get('cart', {})
    if product_id not in cart:
        flash("Item not in cart", "warning")
        return redirect(url_for('view_cart'))

    try:
        qty = int(request.form.get('quantity', 0))
    except ValueError:
        qty = cart[product_id].get('qty', 1)

    if qty <= 0:
        cart.pop(product_id, None)
        flash("Item removed from cart", "info")
    else:
        cart[product_id]['qty'] = qty
        flash("Cart updated", "success")

    session['cart'] = cart
    return redirect(url_for('view_cart'))

@app.route('/cart/remove/<product_id>', methods=['POST'])
def remove_cart_item(product_id):
    init_cart()
    cart = session.get('cart', {})
    if product_id in cart:
        cart.pop(product_id, None)
        session['cart'] = cart
        flash("Item removed from cart", "info")
    else:
        flash("Item not found in cart", "warning")
    return redirect(url_for('view_cart'))

@app.route('/cart/clear', methods=['POST'])
def clear_cart():
    session['cart'] = {}
    flash("Cart cleared", "info")
    return redirect(url_for('view_cart'))

# Optional: simple checkout stub
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user' not in session:
        flash("Please login to checkout", "warning")
        return redirect(url_for('login'))
    init_cart()
    cart = session.get('cart', {})
    total, count = cart_total_and_count()
    if request.method == 'POST':
        # Implement your order creation & payment logic here (DB save, payment gateway, etc.)
        # For now, we'll just clear the cart and show a success.
        session['cart'] = {}
        flash("Order placed successfully! (demo)", "success")
        return redirect(url_for('home'))
    return render_template('checkout.html', cart=cart, total=total, count=count)


# ----- Run App -----
# if __name__ == "__main__":
#     app.run(debug=True)
if __name__ == "__main__":
    app.run(debug=True, port=5001)
