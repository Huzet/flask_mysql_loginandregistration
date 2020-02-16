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
    if not request.form['PW'] == request.form['Confirm_PW']:
        is_valid = False
        flash("Password does not match")
    if not EMAIL_REGEX.match(request.form['EM']):
        is_valid = False
        flash("Invalid email address!")

    if is_valid:
        query = 'INSERT INTO registrations (first_name, last_name, email, password, updated_at, created_at) VALUES (%(FN)s, %(LN)s, %(EM)s, %(PW)s, NOW(), NOW())'
        data = {
            'FN': request.form['FN'],
            'LN': request.form['LN'],
            'EM': request.form['EM'],
            'PW': pw_hash
        }
        mysql = connectToMySQL('registration_with_email')
        mysql.query_db(query, data)
        flash("Made User")

    return redirect('/')


@app.route("/login", methods=['POST'])
def on_login():
    is_valid = True

    if not EMAIL_REGEX.match(request.form['EM']):
        is_valid = True
        flash("Email is not valid")

    if is_valid:
        query = "SELECT id, password FROM registrations WHERE email= %(EM)s"
        data = {
            'EM': request.form['EM'],
        }
        mysql = connectToMySQL('registration_with_email')
        result = mysql.query_db(query, data)
        if result:
            if not bcrypt.check_password_hash(result[0]['password'], request.form['PW']):
                flash("Incorrect password")
                return redirect("/")
            else:
                session['user_id'] = result[0]['id']
                return redirect("/success")
        else:
            flash("Email not in database")
        return redirect('/')


@app.route('/success')
def success():
    if 'user_id' not in session:
        return redirect('/')

    query = 'SELECT * FROM registrations WHERE id=%(id)s'
    data = {
        'id': session['user_id']
    }
    mysql = connectToMySQL('registration_with_email')
    result = mysql.query_db(query, data)
    
    if result:
        query = 'SELECT tweets.id, tweets.author, tweets.tweet, registrations.first_name, registrations.last_name FROM registrations JOIN tweets ON registrations.id = tweets.author'
        mysql = connectToMySQL('registration_with_email')
        tweets = mysql.query_db(query)

        # Users following
        query = 'SELECT * FROM follows WHERE follower = %(user_id)s'
        data = {'user_id': session['user_id']}
        mysql = connectToMySQL('registration_with_email')
        followed_user = [info['followed'] for info in mysql.query_db(query, data)]
        followed_user.append(session['user_id'])

        tweets_of_followed_user = []

        for tweet in tweets:
            if tweet['author'] in followed_user:
                tweets_of_followed_user.append(tweet)



        query = 'SELECT tweets_id FROM tweets_users_have_liked WHERE registrations_id = %(user)s'
        data = {
        'user': session['user_id']
        }
        mysql = connectToMySQL('registration_with_email')
        user_likes = mysql.query_db(query, data)

        liked_list = []
        for tweet in user_likes:
            liked_list.append(tweet['tweets_id'])

        # liked_list = [tweet['tweets_id'] for tweet in userlikes] SAME AS ^^^^^

        return render_template('welcome.html', user=result[0], tweets=tweets ,liked_list=liked_list, tweets_of_followed_user=tweets_of_followed_user)
    else:
        return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/on_tweet', methods=['POST'])
def on_tweet():
    print(request.form['tweet_content'])
    
    is_valid=True
    if len(request.form['tweet_content']) < 1:
        is_valid=False
        flash('nothing in text box')   
    if is_valid:
            query = 'INSERT INTO tweets (tweet, author, updated_at, created_at) VALUES (%(TW)s, %(FK)s, NOW(), NOW());'
            data = {
                    'TW' : request.form.get('tweet_content'),
                    'FK' : session['user_id']
                   }
            mysql = connectToMySQL('registration_with_email')
            mysql.query_db(query, data)

    return redirect('/success')

@app.route('/on_delete/<tweet_id>')
def on_delete_tweet(tweet_id):
    if 'user_id' not in session:
        return redirect("/")
    query = "DELETE FROM tweets WHERE tweets.id = %(tweet_id)s"
    data = {'tweet_id': tweet_id}
    mysql = connectToMySQL('registration_with_email')
    mysql.query_db(query, data)
    
    query = "DELETE FROM tweets_users_have_liked WHERE tweets_users_have_liked.tweets_id = %(tweet_id)s"
    data = {'tweet_id': tweet_id}
    mysql = connectToMySQL('registration_with_email')
    mysql.query_db(query, data)

    return redirect("/success")

@app.route('/edit/<tweet_id>')
def edit_tweet(tweet_id):
    query = "SELECT tweets.id, tweets.tweet FROM tweets WHERE tweets.id = %(tweet_id)s"
    data = {'tweet_id': tweet_id}
    mysql = connectToMySQL('registration_with_email')
    tweet = mysql.query_db(query, data)
    if tweet:
        return render_template('tweet_edit.html', tweet=tweet[0])

    return redirect("/success")

@app.route('/on_edit/<tweet_id>', methods=['POST'])
def on_edit(tweet_id):
    query = "UPDATE tweets SET tweets.tweet = %(tweet)s WHERE tweets.id = %(tweet_id)s"
    data = {
        'tweet_id' : tweet_id,
        'tweet' : request.form.get('tweet_edit'),
        }
    mysql = connectToMySQL('registration_with_email')
    mysql.query_db(query, data)
    
    return redirect('/success')

@app.route('/like/<tweet_id>')
def likes(tweet_id):
    query = "INSERT INTO tweets_users_have_liked (tweets_id, registrations_id) VALUES ( %(tweet_id)s, %(user_id)s);"
    data = {
        'user_id' : session['user_id'],
        'tweet_id': tweet_id
    }
    mysql = connectToMySQL('registration_with_email')
    mysql.query_db(query, data)
    return redirect('/success')

@app.route('/details/<tweet_id>')
def details_tweet(tweet_id):
    query  = 'SELECT tweets_users_have_liked.tweets_id,  tweets_users_have_liked.registrations_id, registrations.first_name, registrations.last_name FROM tweets_users_have_liked JOIN registrations ON tweets_users_have_liked.registrations_id = registrations.id WHERE tweets_users_have_liked.tweets_id = %(id)s;'
    data = {'id': tweet_id}
    mysql = connectToMySQL('registration_with_email')
    liked = mysql.query_db(query, data)

    query  = 'SELECT registrations.first_name, registrations.last_name, tweets.tweet, tweets.created_at, tweets.updated_at FROM registrations JOIN tweets ON registrations.id = tweets.author WHERE tweets.id = %(id)s;'
    data = {'id': tweet_id}
    mysql = connectToMySQL('registration_with_email')
    details = mysql.query_db(query, data)

    return render_template('details.html', liked=liked, details=details[0]) 

@app.route('/unlike/<tweet_id>')
def unlike(tweet_id):
    query = "DELETE FROM tweets_users_have_liked WHERE tweets_id = %(tweet_id)s and registrations_id = %(user_id)s"
    data = {
        'tweet_id': tweet_id,
        'user_id' : session['user_id']
    }
    mysql = connectToMySQL('registration_with_email')
    mysql.query_db(query, data)
    return redirect('/success')

@app.route('/follow')
def follow():
    query = "SELECT registrations.id, registrations.first_name, registrations.last_name FROM registrations"
    mysql = connectToMySQL('registration_with_email')
    all_users = mysql.query_db(query)

    query = "SELECT * FROM follows WHERE follower = %(user_id)s"
    data = {'user_id' : session['user_id'] }
    mysql = connectToMySQL('registration_with_email')
    following = [info['followed'] for info in mysql.query_db(query, data)]

    followed = []
    not_followed = []

    for user in all_users:
        if user['id'] in following:
            followed.append(user)
        else:
            not_followed.append(user)

    return render_template('followers.html', followed=followed, not_followed=not_followed)

@app.route('/un_follow/<user_id>')
def un_follow(user_id):
    query = "DELETE FROM follows WHERE followed = %(followed)s and follower = %(follower)s"
    data = {
        'followed' : user_id,
        'follower' : session['user_id']
    }
    mysql = connectToMySQL('registration_with_email')
    mysql.query_db(query, data)
    return redirect('/follow')

@app.route('/on_follow/<user_id>')
def on_follow(user_id):
    query = "INSERT INTO follows (followed, follower) VALUES (%(followed)s, %(follower)s)"
    data = {
        'followed' : user_id,
        'follower' : session['user_id']
    }
    mysql = connectToMySQL('registration_with_email')
    mysql.query_db(query, data)
    return redirect('/follow')

if __name__ == '__main__':
    app.run(debug=True)
