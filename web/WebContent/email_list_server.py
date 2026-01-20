#!/usr/bin/env python3
"""
Simple Email List Server
========================
Low-tech email collection endpoint that saves emails to email_list.json

Usage:
    python3 email_list_server.py --port 5007
    
Or with gunicorn:
    gunicorn -w 1 -b 0.0.0.0:5007 email_list_server:app
"""

import os
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from your website

EMAIL_LIST_FILE = 'email_list.json'

def load_emails():
    """Load existing emails from JSON file"""
    if os.path.exists(EMAIL_LIST_FILE):
        try:
            with open(EMAIL_LIST_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('emails', []), data.get('metadata', {})
        except (json.JSONDecodeError, IOError):
            pass
    return [], {}

def save_emails(emails, metadata):
    """Save emails to JSON file"""
    data = {
        'emails': emails,
        'metadata': metadata,
        'last_updated': datetime.now().isoformat()
    }
    with open(EMAIL_LIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@app.route('/api/subscribe', methods=['POST'])
def subscribe():
    """Add email to the list"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        
        # Basic email validation
        if '@' not in email or '.' not in email.split('@')[1]:
            return jsonify({'success': False, 'error': 'Invalid email format'}), 400
        
        # Load existing emails
        emails, metadata = load_emails()
        
        # Check for duplicates
        if email in emails:
            return jsonify({
                'success': True, 
                'message': 'You\'re already subscribed!',
                'already_subscribed': True
            }), 200
        
        # Add email
        emails.append(email)
        
        # Update metadata
        if 'total_subscribers' not in metadata:
            metadata['total_subscribers'] = 0
        metadata['total_subscribers'] = len(emails)
        metadata['first_subscriber_date'] = metadata.get('first_subscriber_date', datetime.now().isoformat())
        metadata['last_subscriber_date'] = datetime.now().isoformat()
        
        # Save to file
        save_emails(emails, metadata)
        
        return jsonify({
            'success': True,
            'message': 'Thank you! You\'ve been added to our email list.',
            'total_subscribers': len(emails)
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/subscribers', methods=['GET'])
def get_subscribers():
    """Get list of subscribers (for admin use)"""
    try:
        emails, metadata = load_emails()
        return jsonify({
            'emails': emails,
            'metadata': metadata,
            'count': len(emails)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Email List Server')
    parser.add_argument('--port', type=int, default=5007, help='Port to run server on')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to')
    args = parser.parse_args()
    
    print(f"Starting email list server on http://{args.host}:{args.port}")
    print(f"Email list will be saved to: {os.path.abspath(EMAIL_LIST_FILE)}")
    app.run(host=args.host, port=args.port, debug=True)

