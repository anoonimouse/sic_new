from flask import Flask, render_template, request, jsonify, send_file
import requests
import qrcode
from io import BytesIO
import csv

app = Flask(__name__)

# Function to fetch GST rates from the API
def fetch_gst_rates(heading):
    api_url = f"https://zoyop.pythonanywhere.com/getgst?heading={heading}"
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Failed to fetch GST rates"}

# Load the CSV file and convert it to a list of dictionaries
def load_gst_data():
    gst_data = []
    with open('gst-headings.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            gst_data.append({'heading': row[0], 'description': row[1]})
    return gst_data

# Route to return GST data as JSON
@app.route('/gst-data', methods=['GET'])
def get_gst_data():
    data = load_gst_data()
    return jsonify(data)

# Route to serve the landing page (entry point)
@app.route('/')
def landing_page():
    return render_template('landing.html')

# Route for the bill generator page
@app.route('/bill-generator')
def index():
    return render_template('test.html')

# Route for QR code generator page
@app.route('/generate_qr')
def generate_qr_page():
    return render_template('generate_qr.html')

# Route to handle the QR code generation
@app.route('/generate_qr_code', methods=['POST'])
def generate_qr_code_route():
    data = request.json
    price = data.get('price')
    heading = data.get('heading')

    if not price or not heading:
        return {"error": "Price and GST heading are required"}

    qr_data = {"Price": price, "GST Heading": heading}
    qr_buffer = generate_qr_code(qr_data)

    return send_file(qr_buffer, mimetype='image/png')

# Function to generate QR code
def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

# Route to handle the bill calculation
@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.json
    price = float(data.get('price', 0))
    heading = data.get('heading', '')
    includeIgst = data.get('includeIgst', False)

    gst_data = fetch_gst_rates(heading)
    if "error" in gst_data:
        return jsonify({"error": gst_data["error"]})

    try:
        cgst_rate = float(gst_data.get('CGST Rate (%)', '0').replace('%', ''))
        sgst_rate = float(gst_data.get('SGST Rate (%)', '0').replace('%', ''))
        igst_rate = float(gst_data.get('IGST Rate (%)', '0').replace('%', ''))
        descriptionofgoods = gst_data.get('Description of Goods', '')
    except ValueError:
        return jsonify({"error": "Invalid GST rate format"})

    cgst_amount = (cgst_rate / 100) * price if not includeIgst else 0
    sgst_amount = (sgst_rate / 100) * price if not includeIgst else 0
    igst_amount = (igst_rate / 100) * price if includeIgst else 0
    total_gst = cgst_amount + sgst_amount + igst_amount
    total_amount = price + total_gst

    return jsonify({
        "CGST": cgst_amount,
        "CGST Rate": cgst_rate,
        "SGST": sgst_amount,
        "SGST Rate": sgst_rate,
        "IGST": igst_amount,
        "IGST Rate": igst_rate,
        "Total GST": total_gst,
        "Total Amount": total_amount,
        "Description": descriptionofgoods
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
