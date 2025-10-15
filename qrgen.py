import qrcode
import json

# Product data to encode in the QR code
product_data = {
    "price": 100,
    "gst_heading": "502"
}

# Convert the product data to JSON format
product_data_json = json.dumps(product_data)

# Generate QR code
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)
qr.add_data(product_data_json)
qr.make(fit=True)

# Create an image of the QR code
img = qr.make_image(fill='black', back_color='white')

# Save the QR code image
img.save('product_qr_code.png')

print("QR code generated and saved as product_qr_code.png.")
