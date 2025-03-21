from flask import Flask, render_template, request
import qrcode
import base64
from io import BytesIO
import uuid
import os

app = Flask(__name__, static_url_path='', static_folder='static')

# Ensure the 'static/' folder exists
if not os.path.exists("static"):
    os.makedirs("static")

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

        # Generate a unique filename
        token = str(uuid.uuid4())[:8]  # Shortened token for readability
        filename = f"display-{token}.html"

        # Generate the HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{first_name} {last_name} - Business Card</title>
        </head>
        <body>
            <h1>{first_name} {middle_name} {last_name}</h1>
            <p><strong>Designation:</strong> {designation}</p>
            <p><strong>Company:</strong> {company_name}</p>
            <p><strong>Work Phone:</strong> {phone_work}</p>
            <p><strong>Personal Phone:</strong> {phone_personal}</p>
            <p><strong>Alternate Phone:</strong> {phone_personal_2}</p>
            <p><strong>Email:</strong> <a href="mailto:{email}">{email}</a></p>
            <p><strong>Alternate Email:</strong> <a href="mailto:{email2}">{email2}</a></p>
            <p><strong>Address:</strong> {address}</p>
            <p><strong>Website:</strong> <a href="{website}" target="_blank">{website}</a></p>
        </body>
        </html>
        """

        # Save the HTML file
        with open(f"static/{filename}", "w", encoding="utf-8") as f:
            f.write(html_content)

        # ✅ **Corrected GitHub URL**
        github_username = "aasthaarora21"  # Change this to your GitHub username
        repo_name = "QRCode"   # Change this to your GitHub repo name
        github_url = f"https://{github_username}.github.io/{repo_name}/static/{filename}"

        # Generate the QR code with this GitHub-hosted URL
        img_b64 = generate_qr_code(github_url)

        return render_template('result.html', img_b64=img_b64, display_url=github_url)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
