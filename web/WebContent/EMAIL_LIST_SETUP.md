# Email List Setup

Simple low-tech email collection that saves to `email_list.json`.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install flask flask-cors
   ```

2. **Start the server:**
   ```bash
   python3 email_list_server.py --port 5007
   ```

   Or with gunicorn (for production):
   ```bash
   pip install gunicorn
   gunicorn -w 1 -b 0.0.0.0:5007 email_list_server:app
   ```

3. **Update the API endpoint in `index.html`:**
   - For local testing: `http://localhost:5007/api/subscribe`
   - For production: Change to your actual server URL (e.g., `https://yourdomain.com/api/subscribe`)

## Where to Find Emails

All emails are saved in **`email_list.json`** in the same directory as the server.

The file structure:
```json
{
  "emails": ["user1@example.com", "user2@example.com"],
  "metadata": {
    "total_subscribers": 2,
    "first_subscriber_date": "2024-01-15T10:30:00",
    "last_subscriber_date": "2024-01-16T14:20:00"
  },
  "last_updated": "2024-01-16T14:20:00"
}
```

## Viewing Subscribers

You can:
1. **Open the JSON file directly** - Just read `email_list.json`
2. **Use the API endpoint** - Visit `http://localhost:5007/api/subscribers` (GET request)
3. **Export programmatically** - The JSON file is easy to parse with any script

## API Endpoints

- **POST `/api/subscribe`** - Add an email to the list
  - Body: `{"email": "user@example.com"}`
  - Returns: `{"success": true, "message": "...", "total_subscribers": 5}`

- **GET `/api/subscribers`** - Get all subscribers (for admin use)
  - Returns: `{"emails": [...], "metadata": {...}, "count": 5}`

- **GET `/health`** - Health check

## Production Deployment

When deploying to production:

1. Update the API endpoint URL in `index.html` JavaScript
2. Make sure the server is running and accessible
3. Consider adding basic authentication to `/api/subscribers` if needed
4. Set up proper file permissions for `email_list.json`

## Future Migration

When you're ready to move to Mailchimp or another service:
- Export emails from `email_list.json`
- Use their import/API to add subscribers
- Update the JavaScript to point to their API

