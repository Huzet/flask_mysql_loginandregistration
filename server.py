from flask import Flask, render_template, request, redirect, session, flash
import re
from flask_bcrypt import Bcrypt  
from mysqlconnection import connectToMySQL

app = Flask(__name__)

bcrypt = Bcrypt(app)

app.secret_key = 'password'

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

@app.route('/')
def index():

    return(render_template('index.html'))

@app.route('/add', methods=['POST'])
def add():

    pw_hash = bcrypt.generate_password_hash(request.form['PW'])
    print(pw_hash)

    is_valid = True
    if len(request.form['FN']) < 2:
        is_valid = False
        flash("Please enter a first name")
    if len(request.form['LN']) < 2:
        is_valid = False
        flash("Please enter a last name")
    if len(request.form['EM']) < 2:
        is_valid = False
        flash("Occupation should be at least 2 characters")    
    if len(request.form['PW']) < 2:
        is_valid = False
        flash("Occupation should be at least 2 characters")      
    if not EMAIL_REGEX.match(request.form['EM']):
        is_valid = False
        flash("Invalid email address!")
    
    if is_valid:
        query = 'INSERT INTO registrations (first_name, last_name, email, password, updated_at, created_at) VALUES (%(FN)s, %(LN)s, %(EM)s, %(PW)s, NOW(), NOW())'
        data = {
            'FN' : request.form['FN'], 
            'LN' : request.form['LN'],
            'EM' : request.form['EM'],
            'PW' : pw_hash
        }
        mysql = connectToMySQL('registration_with_email')
        mysql.query_db(query, data)
        flash("Added friend")
    
    return redirect('/')

@app.route("/login", methods=['POST'])
def on_login():
    is_valid = True
    if not EMAIL_REGEX.match(request.form['EM']):
        is_valid = True
        flash("Email is not valid")
    if is_valid :
        query = "SELECT id, password FROM registrations WHERE email= %(EM)s"
        data = {
            'EM': request.form['EM'],
        }
        mysql = connectToMySQL('registration_with_email')
        result = mysql.query_db(query, data)
        print(result)
        if result:
            if not bcrypt.check_password_hash(result[0]['password'], request.form['PW']):
                flash("Incorrect password")
                return redirect("/")
            else:
                print(result)
                session['user_id'] = result[0]['id']
                return redirect ("/success")
        else:
            flash("Email not in database")
        return redirect('/')

@app.route('/success')
def success():

    return render_template('welcome.html') 

if __name__ == '__main__':
    app.run(debug=True)