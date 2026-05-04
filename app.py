from flask import Flask, render_template, request, redirect, url_for, session
import google.generativeai as genai
import mysql.connector

app = Flask(__name__)
app.secret_key = "medai_secret_key"

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="", 
        database="medai_db"
    )

genai.configure(api_key="AIzaSyBg0YyhOZWZf0dicxX-nB8VIou4HtsjgXI")

@app.route("/", methods=["GET", "POST"])
def home():
    response_text = ""
    warning = ""
    search_history = []
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT symptoms, diagnosis FROM history ORDER BY id DESC LIMIT 5")
        search_history = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database Error: {e}")

    if request.method == "POST":
        user_input = request.form["symptoms"]
        emergency_list = ["chest pain", "breathless", "heart attack", "unconscious"]
        if any(word in user_input.lower() for word in emergency_list):
            warning = "⚠️ জরুরি সতর্কতা: আপনার লক্ষণগুলো গুরুতর। দ্রুত হাসপাতালে যোগাযোগ করুন!"

        try:
            models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            model = genai.GenerativeModel(models[0].name)
            prompt = f"Act as a professional medical expert. Patient: '{user_input}'. Provide response in BENGALI with points: ১. রোগ ২. কারণ ৩. পরামর্শ ৪. ঔষধ।"
            response = model.generate_content(prompt)
            response_text = response.text

            conn = get_db_connection()
            cursor = conn.cursor()
            query = "INSERT INTO history (symptoms, diagnosis) VALUES (%s, %s)"
            cursor.execute(query, (user_input, response_text))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            response_text = f"Error: {str(e)}"

    return render_template("index.html", result=response_text, warning=warning, history=search_history)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            if user:
                session['user'] = username
                return redirect(url_for('home'))
            else:
                return "ভুল ইউজারনেম বা পাসওয়ার্ড"
        except:
            return "ডাটাবেস টেবিল 'users' তৈরি করুন"
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route("/track", methods=["GET", "POST"])
def track():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    records = []
    if request.method == "POST":
        pressure = request.form['pressure']
        sugar = request.form['sugar']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO health_tracking (username, pressure, sugar) VALUES (%s, %s, %s)", 
                       (session['user'], pressure, sugar))
        conn.commit()
        cursor.close()
        conn.close()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM health_tracking WHERE username = %s ORDER BY id DESC", (session['user'],))
    records = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("track.html", records=records)

@app.route("/all-history")
def all_history():
    records = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM history ORDER BY id DESC")
        records = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        print(e)
    return render_template("history.html", records=records)

if __name__ == "__main__":
    app.run(debug=True)