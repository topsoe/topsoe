from flask import Flask, render_template, request
import qrcode
import base64
from io import BytesIO
import vobject

app = Flask(__name__)

def generate_qr_code(vcard_data):
    # Create a new vCard object
    vcard = vobject.vCard()

    # Construct the full name including middle name
    full_name = " ".join(filter(None, [vcard_data.get('first_name', ''), vcard_data.get('middle_name', ''), vcard_data.get('last_name', '')]))

    # Add formatted name (fn)
    vcard.add('fn').value = full_name
    
    # Add name (n)
    name_parts = {
        'given': vcard_data.get('first_name', ''),
        'additional': vcard_data.get('middle_name', ''),
        'family': vcard_data.get('last_name', '')  # Ensure last_name is handled properly
    }
    vcard.add('n').value = vobject.vcard.Name(**name_parts)

    # Add phone numbers
    phone_numbers = [vcard_data.get('phone_work', ''),
                 vcard_data.get('phone_personal', ''),
                 vcard_data.get('phone_personal_2', '')]

    for phone in phone_numbers:
        if phone:  # Only add non-empty phone numbers
            vcard.add('tel').value = phone

    
    # Add email addresses
    emails = [vcard_data.get('email', ''), vcard_data.get('email2', '')]  # Collect all email addresses
    for email in emails:
        if email:  # Check if email is not empty
            vcard.add('email').value = email

    # Add address and website
    vcard.add('adr').value = vobject.vcard.Address(street=vcard_data.get('address', ''),
                                                   city=vcard_data.get('city', ''),
                                                   region=vcard_data.get('state', ''),
                                                   code=vcard_data.get('zip_code', ''),
                                                   country=vcard_data.get('country', ''))
    vcard.add('url').value = vcard_data.get('website', '')

    # Serialize the vCard to a string
    vcard_str = vcard.serialize()

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(vcard_str)
    qr.make(fit=True)

    # Convert the QR code image to base64
    img = qr.make_image(fill_color="black", back_color="white")
    img_bytes_io = BytesIO()
    img.save(img_bytes_io, format='PNG')
    img_bytes_io.seek(0)
    img_b64 = base64.b64encode(img_bytes_io.getvalue()).decode('utf-8')

    return img_b64


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        first_name = request.form['first_name']
        middle_name = request.form['middle_name']
        last_name = request.form['last_name']
        phone_work = request.form['phone_work']
        phone_personal = request.form['phone_personal']
        phone_personal_2 = request.form['phone_personal_2']
        email = request.form['email']
        email2 = request.form['email2']
        address = request.form['address']
        website = request.form['website']

        # Create the vCard data
        vcard_data = {
            'first_name': first_name,
            'middle_name': middle_name,
            'last_name': last_name,
            'phone_work': phone_work,
            'phone_personal': phone_personal,
            'phone_personal2': phone_personal_2,
            'email': email,
            'email2': email2,
            'address': address,
            'website': website,
        }

        # Generate the QR code
        img_b64 = generate_qr_code(vcard_data)

        # Render the result template with the QR code
        return render_template('result.html', img_b64=img_b64)

    # If it's a GET request, render the index template
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
