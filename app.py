from flask import Flask, render_template, request, abort, jsonify
import qrcode
import base64
from io import BytesIO
import uuid
import json
import os

app = Flask(__name__)

# Store data persistently in a JSON file
DATA_FILE = "vcard_data.json"

# Function to load stored data
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as file:
        return json.load(file)

# Function to save data persistently
def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

# Load existing data
vcard_storage = load_data()

def generate_qr_code(url):
    """Generate a base64 encoded QR code image for a given URL."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img_bytes_io = BytesIO()
    img.save(img_bytes_io, format='PNG')
    img_bytes_io.seek(0)
    return base64.b64encode(img_bytes_io.getvalue()).decode('utf-8')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Retrieve form data
        first_name = request.form['first_name']
        middle_name = request.form['middle_name']
        last_name = request.form['last_name']
        designation = request.form['designation']
        company_name = request.form['company_name']
        phone_work = request.form['phone_work']
        phone_personal = request.form['phone_personal']
        phone_personal_2 = request.form['phone_personal_2']
        email = request.form['email']
        email2 = request.form['email2']
        address = request.form['address']
        website = request.form['website']

        # Package the data into a dictionary.
        vcard_data = {
            'first_name': first_name,
            'middle_name': middle_name,
            'last_name': last_name,
            'designation': designation,
            'company_name': company_name,
            'phone_work': phone_work,
            'phone_personal': phone_personal,
            'phone_personal_2': phone_personal_2,
            'email': email,
            'email2': email2,
            'address': address,
            'website': website,
        }

        # Generate a unique token and store the details.
        token = str(uuid.uuid4())
        vcard_storage[token] = vcard_data
        save_data(vcard_storage)  # Save data persistently

        # ✅ FIXED: Use the correct Vercel URL (replace with your real project URL)
        display_url = f"https://ankul-qr-generator.vercel.app/display/{token}"

        # Generate the QR code that encodes this URL.
        img_b64 = generate_qr_code(display_url)

        # Render the result page with the QR code and a clickable link.
        return render_template('result.html', img_b64=img_b64, display_url=display_url)

    return render_template('index.html')

@app.route('/display/<token>')
def display(token):
    # Load latest data
    vcard_storage = load_data()

    # Retrieve the stored details; abort with 404 if token not found.
    vcard_data = vcard_storage.get(token)
    if not vcard_data:
        abort(404)
    return render_template('vcard_display.html', **vcard_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)