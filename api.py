from flask import Flask, request, jsonify
import pandas as pd

# Initialize the Flask application
app = Flask(__name__)

# Load GST data from a CSV file
df = pd.read_csv('gst_data.csv')

# Helper function to calculate total GST rates
def calculate_gst_rates(heading):
    # Filter the dataframe based on the Chapter/Heading
    result = df[df['Heading'] == heading]
    
    if result.empty:
        return None  # No match found for the given heading

    # Extract relevant GST rates
    cgst_rate = result.iloc[0]['CGST Rate (%)']
    sgst_rate = result.iloc[0]['SGST Rate (%)']
    igst_rate = result.iloc[0]['IGST Rate (%)']
    compensation_cess = result.iloc[0]['Compensation Cess']
    descpn = result.iloc[0]['Description of Goods']
    
    # Calculate total GST for combined SGST and CGST
    total_gst = cgst_rate + sgst_rate
    
    # Return as a dictionary
    return {
        
        'CGST Rate (%)': cgst_rate,
        'SGST Rate (%)': sgst_rate,
        'IGST Rate (%)': igst_rate,
        'Compensation Cess': compensation_cess,
        'Description of Goods': descpn,
       # 'Total GST (CGST + SGST)': total_gst
    }

# Define a route for the API that accepts the heading/sub-heading as input
@app.route('/getgst', methods=['GET'])
def getgst():
    heading = request.args.get('heading')  # Get the heading/sub-heading from request
    
    # Calculate the GST rates for the given heading
    gst_rates = calculate_gst_rates(heading)
    
    if gst_rates is None:
        return jsonify({"error": "No GST data found for the given heading"}), 404
    
    # Return the GST rates as JSON
    return jsonify(gst_rates)

# Run the application
if __name__ == '__main__':
    app.run(debug=True)
