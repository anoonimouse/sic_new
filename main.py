from flask import Flask, render_template, request, jsonify, send_file
import requests
import qrcode
from io import BytesIO
import csv
import qrcode
import io
import json
import os

app = Flask(__name__)

FINNHUB_API_KEY = 'crq37i1r01qutsn365a0crq37i1r01qutsn365ag'

# Finnhub API URLs for global stocks (12 stocks)
STOCK_API_URLS = {
    'AAPL': f'https://finnhub.io/api/v1/quote?symbol=AAPL&token={FINNHUB_API_KEY}',   # Apple
    'MSFT': f'https://finnhub.io/api/v1/quote?symbol=MSFT&token={FINNHUB_API_KEY}',   # Microsoft
    'GOOGL': f'https://finnhub.io/api/v1/quote?symbol=GOOGL&token={FINNHUB_API_KEY}', # Google
    'TSLA': f'https://finnhub.io/api/v1/quote?symbol=TSLA&token={FINNHUB_API_KEY}',   # Tesla
    'AMZN': f'https://finnhub.io/api/v1/quote?symbol=AMZN&token={FINNHUB_API_KEY}',   # Amazon
    'META': f'https://finnhub.io/api/v1/quote?symbol=META&token={FINNHUB_API_KEY}',   # Meta (Facebook)
    'NFLX': f'https://finnhub.io/api/v1/quote?symbol=NFLX&token={FINNHUB_API_KEY}',   # Netflix
    'NVDA': f'https://finnhub.io/api/v1/quote?symbol=NVDA&token={FINNHUB_API_KEY}',   # Nvidia
    'V': f'https://finnhub.io/api/v1/quote?symbol=V&token={FINNHUB_API_KEY}',         # Visa
    'JPM': f'https://finnhub.io/api/v1/quote?symbol=JPM&token={FINNHUB_API_KEY}',     # JPMorgan Chase
    'BRK.B': f'https://finnhub.io/api/v1/quote?symbol=BRK.B&token={FINNHUB_API_KEY}', # Berkshire Hathaway
    'DIS': f'https://finnhub.io/api/v1/quote?symbol=DIS&token={FINNHUB_API_KEY}'      # Walt Disney
}


def fetch_gst_rates(heading):
    """
    Fetch GST rates from the API
    """
    api_url = f"https://zoyop.pythonanywhere.com/getgst?heading={heading}"
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Failed to fetch GST rates"}

def load_gst_data():
    """
    Load the CSV file and convert it to a list of dictionaries
    """
    gst_data = []
    with open('gst-headings.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            gst_data.append({'heading': row[0], 'description': row[1]})
    return gst_data

    

def generate_qr_code(data):
    """
    Generate a QR code
    """
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

@app.route('/gst-data', methods=['GET'])
def get_gst_data():
    """
    Return GST data as JSON
    """
    data = load_gst_data()
    return jsonify(data)

@app.route('/')
def landing_page():
    
    return render_template('landing.html')

@app.route('/finance')
def finance():
    return render_template('finance.html')  

@app.route('/gstworld')
def gstworld():
    return render_template('gstworld.html')      

@app.route('/get_stock_data')
def get_stock_data():
    stock_data = {}
    for stock, url in STOCK_API_URLS.items():
        try:
            response = requests.get(url)
            data = response.json()
            stock_data[stock] = {
                'current_price': data['c'],
                'high_price': data['h'],
                'low_price': data['l'],
                'previous_close': data['pc'],
                'change_color': 'green' if data['c'] > data['pc'] else 'red'  # Gain (green) or Loss (red)
            }
        except Exception as e:
            print(f"Error fetching data for {stock}: {e}")
            stock_data[stock] = {'error': 'Data not available'}
    
    return jsonify(stock_data)
   

@app.route('/bill-generator')
def bill_generator_page():
    """
    Serve the bill generator page
    """
    return render_template('bill_generator.html')

@app.route('/generate_qr')
def generate_qr_page():
    """
    Serve the QR code generator page
    """
    return render_template('generate_qr.html')

@app.route('/generate_qr_code', methods=['POST'])
def generate_qr_code():
    # Get data from the POST request
    data = request.get_json()

    # Construct the product data in the desired format
    product_data = {
        "price": data['price'],         # Use price from request data
        "heading": data['heading']  # Use heading from request data
    }

    # Convert the product data to JSON
    product_data_json = json.dumps(product_data)

    # Generate the QR code with this data
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(product_data_json)
    qr.make(fit=True)

    # Create the QR code image
    img = qr.make_image(fill='black', back_color='white')
    
    # Save the image to a bytes buffer instead of a file
    byte_io = io.BytesIO()
    img.save(byte_io, 'PNG')
    byte_io.seek(0)

    # Send the image as a response
    return send_file(byte_io, mimetype='image/png')

@app.route('/calculate', methods=['POST'])
def calculate():
    """
    Handle the bill calculation
    """
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
    app.run(host='0.0.0.0', port=8000, debug=True, ssl_context=('cert.pem', 'key.pem'))
    