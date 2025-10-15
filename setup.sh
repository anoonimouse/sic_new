#!/bin/bash

# Flask Production Setup Script for DigitalOcean
# Server IP: 159.89.173.16
# Domain: apps.uditc.me
# Run as root: bash setup.sh

set -e  # Exit on any error

echo "=========================================="
echo "Flask Production Setup Script"
echo "Server IP: 159.89.173.16"
echo "Domain: apps.uditc.me"
echo "=========================================="

# Configuration variables
APP_NAME="app1"
DOMAIN="apps.uditc.me"
GIT_REPO="https://github.com/anoonimouse/sic_new.git"
APP_DIR="/root/sic_new"
FLASK_APP="app:app"  # app.py with Flask instance named 'app'

echo "Step 1: Updating system packages..."
apt update
apt upgrade -y

echo "Step 2: Installing required software..."
apt install -y python3 python3-pip python3-venv nginx git build-essential libssl-dev libffi-dev python3-dev

echo "Step 3: Cloning repository..."
cd /root
if [ -d "$APP_DIR" ]; then
    echo "Directory exists, pulling latest changes..."
    cd $APP_DIR
    git pull
else
    git clone $GIT_REPO
    cd $APP_DIR
fi

echo "Step 4: Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Step 5: Installing Python dependencies..."
pip install --upgrade pip
pip install flask gunicorn

# Install from requirements.txt if it exists
if [ -f "requirements.txt" ]; then
    echo "Found requirements.txt, installing dependencies..."
    pip install -r requirements.txt
fi

deactivate

echo "Step 6: Creating Gunicorn systemd service..."
cat > /etc/systemd/system/${APP_NAME}.service << EOF
[Unit]
Description=Gunicorn instance to serve Flask ${APP_NAME}
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=${APP_DIR}
Environment="PATH=${APP_DIR}/venv/bin"
ExecStart=${APP_DIR}/venv/bin/gunicorn --workers 3 --bind unix:${APP_DIR}/${APP_NAME}.sock -m 007 ${FLASK_APP}

[Install]
WantedBy=multi-user.target
EOF

echo "Step 7: Starting and enabling Gunicorn service..."
systemctl daemon-reload
systemctl start ${APP_NAME}
systemctl enable ${APP_NAME}

echo "Step 8: Configuring Nginx..."
cat > /etc/nginx/sites-available/${DOMAIN} << 'EOF'
server {
    listen 80;
    server_name apps.uditc.me;

    # App1 - at /app1 path
    location /app1 {
        rewrite ^/app1(/.*)$ $1 break;
        
        include proxy_params;
        proxy_pass http://unix:/root/sic_new/app1.sock;
        
        proxy_set_header X-Script-Name /app1;
        proxy_set_header X-Forwarded-Prefix /app1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Serve static files directly (if your app has a static folder)
    location /app1/static {
        alias /root/sic_new/static;
    }

    # Root path
    location / {
        return 200 "Apps Portal - Available apps: /app1";
        add_header Content-Type text/plain;
    }
}
EOF

echo "Step 9: Enabling Nginx site..."
ln -sf /etc/nginx/sites-available/${DOMAIN} /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default  # Remove default site

echo "Step 10: Testing Nginx configuration..."
nginx -t

echo "Step 11: Restarting Nginx..."
systemctl restart nginx

echo "Step 12: Configuring firewall..."
ufw --force enable
ufw allow OpenSSH
ufw allow 'Nginx HTTP'
ufw allow 'Nginx HTTPS'

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "📊 Service Status:"
systemctl status ${APP_NAME} --no-pager -l || true
echo ""
echo "📋 Next Steps:"
echo "1. Configure DNS: Point apps.uditc.me A record to 159.89.173.16"
echo "2. Wait 5-15 minutes for DNS propagation"
echo "3. Visit: http://apps.uditc.me/app1"
echo ""
echo "🔒 Optional - Install SSL (after DNS is configured):"
echo "   apt install certbot python3-certbot-nginx -y"
echo "   certbot --nginx -d apps.uditc.me"
echo ""
echo "🛠️  Useful Commands:"
echo "   systemctl status ${APP_NAME}     # Check service status"
echo "   systemctl restart ${APP_NAME}    # Restart after code changes"
echo "   journalctl -u ${APP_NAME} -f     # View live logs"
echo "   nginx -t                         # Test nginx config"
echo "   systemctl restart nginx          # Restart nginx"
echo ""
echo "📁 Application Directory: ${APP_DIR}"
echo "🌐 Server IP: 159.89.173.16"
echo "🔗 Domain: ${DOMAIN}"
echo "=========================================="
