from flask import Flask, render_template, request, abort
import qrcode
import base64
from io import BytesIO
import uuid

app = Flask(__name__)

# Temporary in-memory storage for submitted details.
vcard_storage = {}

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
        # Retrieve form data including new fields
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

        # ✅ Use the Vercel-deployed URL instead of localhost
        display_url = f"https://ankul-qr-generator-7dyvouklq-aasthaas-projects.vercel.app/vcard-display.html/{token}"

        # Generate the QR code that encodes this URL.
        img_b64 = generate_qr_code(display_url)

        # Render the result page with the QR code and a clickable link.
        return render_template('result.html', img_b64=img_b64, display_url=display_url)

    return render_template('index.html')

@app.route('/display/<token>')
def display(token):
    # Retrieve the stored details; abort with 404 if token not found.
    vcard_data = vcard_storage.get(token)
    if not vcard_data:
        abort(404)
    return render_template('vcard_display.html', **vcard_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
