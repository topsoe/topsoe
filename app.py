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
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            background-color: #f4f4f4;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }}

        .card {{
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            text-align: center;
            max-width: 400px;
            width: 90%;
        }}

        .info p {{
            margin: 5px 0;
        }}

        .label {{
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="card">
        <h1>{first_name} {middle_name} {last_name}</h1>
        {"<p><span class='label'>Designation:</span> " + designation + "</p>" if designation else ""}
        {"<p><span class='label'>Company:</span> " + company_name + "</p>" if company_name else ""}
        {"<p><span class='label'>Work Phone:</span> " + phone_work + "</p>" if phone_work else ""}
        {"<p><span class='label'>Personal Phone:</span> " + phone_personal + "</p>" if phone_personal else ""}
        {"<p><span class='label'>Alternate Phone:</span> " + phone_personal_2 + "</p>" if phone_personal_2 else ""}
        {"<p><span class='label'>Email:</span> <a href='mailto:" + email + "'>" + email + "</a></p>" if email else ""}
        {"<p><span class='label'>Alternate Email:</span> <a href='mailto:" + email2 + "'>" + email2 + "</a></p>" if email2 else ""}
        {"<p><span class='label'>Address:</span> " + address + "</p>" if address else ""}
        {"<p><span class='label'>Website:</span> <a href='" + website + "' target='_blank'>" + website + "</a></p>" if website else ""}
    </div>
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
