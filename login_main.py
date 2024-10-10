from lib.lib import *

# Generating a secret key
app = Flask(__name__)
app.config['SECRET_KEY'] = "7611a581f22da3bae0598462f400e3bc"

# Helper function to interact with the database
def connect_data():
    conn = sqlite3.connect("/home/saturam/Desktop/Python_Project_Folder/"
                           "pythonProject/library_inventory/database/admin.db")
    return conn


# Token verification decorator
def token_required(fun):
    @wraps(fun)
    def decorated(*args,**kwargs):
        token = request.args.get('token')
        if not token:
            return jsonify({'Alert!': "Token is Missing!"})
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])  # Specify the algorithm
            if not payload.get('status'):
                return jsonify({'Alert!': "User not logged in!"}), 403
        except jwt.ExpiredSignatureError:
            return jsonify({'Alert!': "Token has expired!"}), 403
        except jwt.InvalidTokenError:
            return jsonify({'Alert!': "Invalid Token!"}), 403
        return fun(*args,**kwargs)
    return decorated

@app.route("/auth")
@token_required
def auth():
    return 'JWT is verified. Welcome to your dashboard.'

@app.route("/")
def home():
    if not session.get('logged_in'):
        return redirect(url_for("login"))
    else:
        return redirect(f'/auth?token={session["token"]}')

@app.route("/login")
def login():
    user_name = request.args.get("username")
    password = request.args.get("password")
    # Connect to the database
    connection = connect_data()
    cur = connection.cursor()
    cur.execute('SELECT * FROM login_detail WHERE username = ?', (user_name,))
    query = cur.fetchone()
    connection.close()
    # Check if the username and password match
    if query and password == query[2]:
        session['logged_in'] = True
        session["token"] = jwt.encode({
            "user": user_name,
            "exp": datetime.now(timezone.utc) + timedelta(seconds=30),
            "status" : True
        }, app.config['SECRET_KEY'])

        return redirect(f'/auth?token={session["token"]}')
    else:
        return make_response("Unable to verify", 403, {'WWW-Authentication': 'Basic realm:"Authentication Failed!'})

@app.route("/logout")
def logout():
    return redirect(f'/session_logout?token={session["token"]}')

@app.route("/session_logout")
def session_logout():
    try:
        payload = jwt.decode(session["token"], app.config['SECRET_KEY'], algorithms=["HS256"])
        user_name = payload['user']
        # Generate a new token with status=False to simulate logout
        new_token = jwt.encode({
            "user": user_name,
            "status": False,  # Set status to False upon logout
            "exp": datetime.now(timezone.utc) + timedelta(seconds=30)
        }, app.config['SECRET_KEY'], algorithm="HS256")

        session['logged_in'] = False
        return jsonify({"message": "Logged out successfully!", "token": new_token})
    except jwt.InvalidTokenError:
        return jsonify({'Alert!': "Invalid Token!"}), 403

if __name__ == "__main__":
    app.run(debug=True)
