from flask import Flask, render_template, request, jsonify
import re
import smtplib
import dns.resolver

app = Flask(__name__)

def verify_email_address(email):
    # Address used for SMTP MAIL FROM command
    fromAddress = 'test@test.com'

    # Email address to verify
    addressToVerify = email

    # Get domain for DNS lookup
    splitAddress = addressToVerify.split('@')
    domain = str(splitAddress[1])

    try:
        # MX record lookup
        records = dns.resolver.resolve(domain, 'MX')
        mxRecord = records[0].exchange
        mxRecord = str(mxRecord)

        # SMTP lib setup
        server = smtplib.SMTP()
        server.set_debuglevel(0)

        # SMTP Conversation
        server.connect(mxRecord)
        server.helo(server.local_hostname)
        server.mail(fromAddress)
        code, _ = server.rcpt(str(addressToVerify))
        server.quit()

        # Assume SMTP response 250 is success
        if code == 250:
            return 'Valid'
        else:
            return 'Invalid'
    except Exception as e:
        print(f"Error verifying email: {str(e)}")
        return 'Invalid'

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

if __name__ == '__main__':
    app.run(debug=True)
