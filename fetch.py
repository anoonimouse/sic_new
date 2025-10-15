import requests
from bs4 import BeautifulSoup
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

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

# Optional: Clean the DataFrame
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
