from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import re
import smtplib
import dns.resolver
import io
import sys
import os

app = Flask(__name__)

PY3 = sys.version_info[0] == 3

# Function to verify single email address
def verify_email_address(email):
    try:
        domain = email.split('@')[-1]
        records = dns.resolver.resolve(domain, 'MX')
        mxRecord = records[0].exchange.to_text()

        server = smtplib.SMTP()
        server.connect(mxRecord)
        server.helo(server.local_hostname)
        server.mail('test@test.com')
        code, _ = server.rcpt(email)
        server.quit()

        return 'Valid' if code == 250 else 'Invalid'
    except smtplib.SMTPConnectError as e:
        return f'Connection failed: {str(e)}'
    except smtplib.SMTPServerDisconnected as e:
        return f'Server disconnected: {str(e)}'
    except dns.resolver.NoAnswer as e:
        return f'No DNS answer for MX record: {str(e)}'
    except Exception as e:
        return f'Error verifying email: {str(e)}'

# Function to verify batch of email addresses from CSV
def verify_emails_from_csv(csv_file):
    try:
        if PY3:
            csv_data = io.StringIO(csv_file.stream.read().decode("UTF8"), newline=None)
        else:
            csv_data = io.StringIO(csv_file.stream.read().decode("UTF8"), newline=None)

        df = pd.read_csv(csv_data)

        if 'email' not in df.columns:
            return [{'Email': '', 'Result': 'Error: CSV file does not contain "email" column.'}]

        emails = df['email'].tolist()
        results = []

        for email in emails:
            email = email.strip()
            if re.match(r"[^@]+@[^@]+\.[^@]+", email):
                result = verify_email_address(email)
                print(email, result)
                results.append({'Email': email, 'Result': result})
            else:
                results.append({'Email': email, 'Result': 'Invalid email format'})
        return results
    except Exception as e:
        return [{'Email': '', 'Result': f'Error verifying emails from CSV: {str(e)}'}]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/verify_email', methods=['POST'])
def verify_email():
    email = request.form['email']
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({'status': 'error', 'message': 'Invalid email address'})

    result = verify_email_address(email)
    return jsonify({'status': 'success', 'message': result})

@app.route('/verify_emails_from_csv', methods=['POST'])
def verify_emails_from_csv_route():
    try:
        csv_file = request.files['file']
        if not csv_file:
            return jsonify({'status': 'error', 'message': 'No file provided'})

        results = verify_emails_from_csv(csv_file)

        # Get the absolute path of the directory where this script resides
        BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        print(BASE_DIR)
        # Save DataFrame to CSV with absolute path
        csv_path = os.path.join(BASE_DIR, 'validated_emails.csv')
        df = pd.DataFrame(results)
        df.to_csv(csv_path, index=False)
        print(df)

        # Return CSV file as response
        return send_file(
            path_or_file=csv_path,
            as_attachment=True,
            download_name='validated_emails.csv',
        )
        print("done")
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Failed to process CSV file: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True)
