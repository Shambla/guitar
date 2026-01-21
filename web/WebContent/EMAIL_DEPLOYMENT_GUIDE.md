# Email List Deployment Guide

## The Problem
Your website is trying to POST to `/api/subscribe` but the Flask server isn't running or isn't accessible on your production server.

## Solution Options

### Option 1: Deploy Flask Server (Recommended if you have a VPS/server)

If your site is hosted on a VPS, dedicated server, or cloud instance where you can run Python:

1. **SSH into your production server**

2. **Navigate to your web directory:**
   ```bash
   cd /path/to/your/web/WebContent
   ```

3. **Install dependencies:**
   ```bash
   pip3 install flask flask-cors gunicorn
   ```

4. **Test the server locally first:**
   ```bash
   python3 email_list_server.py --port 5007
   ```

5. **Run with Gunicorn (production-ready):**
   ```bash
   gunicorn -w 1 -b 0.0.0.0:5007 email_list_server:app
   ```

6. **Set up as a systemd service (so it auto-starts):**
   
   Create `/etc/systemd/system/email-list.service`:
   ```ini
   [Unit]
   Description=Email List Server
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/path/to/your/web/WebContent
   Environment="PATH=/usr/bin:/usr/local/bin"
   ExecStart=/usr/local/bin/gunicorn -w 1 -b 127.0.0.1:5007 email_list_server:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   Then:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable email-list
   sudo systemctl start email-list
   ```

7. **Configure Nginx to proxy `/api/subscribe`:**
   
   Add to your Nginx config (usually in `/etc/nginx/sites-available/your-site`):
   ```nginx
   location /api/subscribe {
       proxy_pass http://127.0.0.1:5007;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
   }
   ```

   Then:
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

### Option 2: Use a Simple Third-Party Service (Quick Fix)

If you're using static hosting (GitHub Pages, Netlify, etc.) or want a quick solution:

1. **Sign up for Formspree** (free): https://formspree.io/
2. **Create a new form** and get your endpoint URL
3. **Update the API endpoint in `index.html`** (line 322) to your Formspree URL

### Option 3: AWS Lambda / Serverless Function

If you're using AWS or similar cloud provider, you can convert the Flask app to a serverless function.

## Testing

After deployment, test your endpoint:
```bash
curl -X POST https://brianstreckfus.com/api/subscribe \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'
```

You should get a JSON response like:
```json
{"success": true, "message": "Thank you! You've been added to our email list.", "total_subscribers": 1}
```

## Where Emails Are Stored

All emails are saved in `email_list.json` in the same directory as `email_list_server.py`.

You can view them:
- Directly: `cat email_list.json`
- Via API: `curl https://brianstreckfus.com/api/subscribers` (add auth if needed)

## Troubleshooting

- **"Unable to connect to server"**: The Flask server isn't running or Nginx isn't configured to proxy `/api/subscribe`
- **"502 Bad Gateway"**: Flask server is down or not accessible on port 5007
- **"404 Not Found"**: Nginx proxy configuration is missing or incorrect
- **CORS errors**: Make sure `flask-cors` is installed and `CORS(app)` is in the Flask code

