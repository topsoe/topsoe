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
        # Retrieve form data, using `.get()` to avoid missing key errors
        first_name = request.form.get('first_name', '').strip()
        middle_name = request.form.get('middle_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        designation = request.form.get('designation', '').strip()
        company_name = request.form.get('company_name', '').strip()
        phone_work = request.form.get('phone_work', '').strip()
        phone_personal = request.form.get('phone_personal', '').strip()
        phone_personal_2 = request.form.get('phone_personal_2', '').strip()
        email = request.form.get('email', '').strip()
        email2 = request.form.get('email2', '').strip()
        address = request.form.get('address', '').strip()
        website = request.form.get('website', '').strip()

        # Ensure at least one required field is filled
        if not first_name and not last_name:
            return "Error: First Name or Last Name must be provided!", 400

        # Generate a unique filename
        token = str(uuid.uuid4())[:8]  # Shortened token for readability
        filename = f"display-{token}.html"

        # Generate the HTML content with CSS
        # Generate the HTML content with the new design
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{first_name} {last_name} - Business Card</title>
    
</head>
<body>
    <div class="card">
        <div class="profile-icon">👤</div>
        <div class="name">{first_name} {middle_name} {last_name}</div>
        
        {"<div class='designation'>" + designation + (" at " + company_name if company_name else "") + "</div>" if designation else ""}
        
        {"<div class='info'><span class='label'>Reception</span> " + phone_work + "</div>" if phone_work else ""}
        {"<div class='info'><span class='label'>Mobile</span> " + phone_personal + "</div>" if phone_personal else ""}
        {"<div class='info'><span class='label'></span> " + phone_personal_2 + "</div>" if phone_personal_2 else ""}
        
        {"<div class='info'><span class='label'>Email</span> <a href='mailto:" + email + "'>" + email + "</a></div>" if email else ""}
        {"<div class='info'><span class='label'></span> <a href='mailto:" + email2 + "'>" + email2 + "</a></div>" if email2 else ""}
        {f"<div class='info'><table class='info'>"
    f"<tr><td class='label'><strong>Address</strong></td><td>{address.replace(',', '<br>')}</td></tr>"
    f"</table></div>" if address else ""}


        {"<div class='info'><span class='label'>Website</span> <a href='" + website + "' target='_blank'>" + website + "</a></div>" if website else ""}
        
        
        <div class="footer">Scanned via Ankul Reprographics QR Generator</div>
    </div>

    <script>
        function downloadVCard() {{
            const vCardData = `BEGIN:VCARD
VERSION:3.0
FN:{first_name} {last_name}
ORG:{company_name}
TITLE:{designation}
TEL;TYPE=WORK:{phone_work}
EMAIL:{email}
ADR:{address}
URL:{website}
END:VCARD`;

            const blob = new Blob([vCardData], {{ type: 'text/vcard' }});
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = "contact.vcf";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }}
    </script>

    </body>
    </html>
    """


        # Save the HTML file
        with open(f"static/{filename}", "w", encoding="utf-8") as f:
            f.write(html_content)

        # ✅ **Corrected GitHub URL**
        github_username = "topsoe"  # Change this to your GitHub username
        repo_name = "topsoe"  # Change this to your GitHub repo name
        github_url = f"https://{github_username}.github.io/{repo_name}/static/{filename}"

        # Generate the QR code with this GitHub-hosted URL
        img_b64 = generate_qr_code(github_url)

        return render_template('result.html', img_b64=img_b64, display_url=github_url)

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
