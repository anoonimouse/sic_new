from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# Function to scrape GST data
def fetch_and_upload_gst_data():
    # Step 1: Web Scraping the GST Page
    url = 'https://cbic-gst.gov.in/gst-goods-services-rates.html'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the table on the page
    table = soup.find('table')

    # Extract table rows and columns
    rows = table.find_all('tr')
    data = []
    for row in rows:
        cols = row.find_all(['td', 'th'])
        cols = [col.text.strip() for col in cols]
        data.append(cols)

    # Convert data to a DataFrame
    df = pd.DataFrame(data)

    # Clean the DataFrame
    df.columns = df.iloc[0]  # Set the first row as header
    df = df.drop(0)  # Drop the first row

    # Step 2: Google Sheets Setup
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file('samsung-india-hackathon-0438e3346997.json', scopes=SCOPES)
    client = gspread.authorize(creds)

    # Access the Google Sheet
    spreadsheet = client.open('gst fetch')  # Replace with your sheet name
    worksheet = spreadsheet.get_worksheet(0)  # Select the first sheet

    # Step 3: Upload data to Google Sheets (clear old data first)
    worksheet.clear()  # Clear previous data
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())  # Upload new data

# Function to fetch data based on heading
def get_gst_data_by_heading(heading):
    # Access the Google Sheet
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = Credentials.from_service_account_file('samsung-india-hackathon-0438e3346997.json', scopes=SCOPES)
    client = gspread.authorize(creds)

    spreadsheet = client.open('gst fetch')  # Replace with your sheet name
    worksheet = spreadsheet.get_worksheet(0)  # Select the first sheet

    # Fetch all data from the sheet
    data = worksheet.get_all_records()

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Match the input heading and return the corresponding row
    result = df[df['Heading'].str.contains(heading, case=False, na=False)]

    if not result.empty:
        return result.to_dict(orient='records')[0]
    else:
        return None

@app.route('/api/gst', methods=['GET'])
def gst_api():
    heading = request.args.get('heading')
    if not heading:
        return jsonify({"error": "Heading is required"}), 400

    # Fetch and upload data if necessary
    fetch_and_upload_gst_data()

    # Get GST data for the given heading
    gst_data = get_gst_data_by_heading(heading)

    if gst_data:
        return jsonify(gst_data)
    else:
        return jsonify({"error": "No data found for the given heading"}), 404

if __name__ == '__main__':
    app.run(debug=True)
