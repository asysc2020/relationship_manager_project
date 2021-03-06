"""My web app's online structure."""

#################
#### Imports ####
#################

# Jinja is a popular template system for Python, used by Flask.
from jinja2 import StrictUndefined

# Flask: A class that we import. An instance of this class will be the
# WSGI application.
# session: A Flask object (class) that allows you to store information specific to a
# user from one request to the next. It's a dictionary that preserves type.
# It is a customized cookie.
from flask import Flask, render_template, request, session, flash, redirect, url_for, jsonify

from model import connect_to_db, db, User, Recommendation, Relationship, Event

# Imported or 'DEBUG' to prevent from Flask Traceback error showing.
import os

import arrow

from flask_bcrypt import Bcrypt

#######################
#### Configuration ####
#######################

# Instantiates Flask. "__name__" is a special Python variable for the name of
# the current module. This is needed so that Flask knows where to look for
# templates, static files, and so on.
app = Flask(__name__)

# Required to use Flask sessions and the debug DebugToolbarExtension. The user could look at
# the contents of your cookie but not modify it, unless they know the secret key
# used for signing.
app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY", "abcdef")
# Another way of generating a secret key:
# >>>import os
# >>>os.urandom(24)

# Raises an error when an undefined variable is used in Jinja2.
app.jinja_env.undefined = StrictUndefined

# Prevents the need to restart server when HTML/CSS is changed.
app.jinja_env.auto_reload = True

bcrypt = Bcrypt(app)


# @app.route('/') is a Python decorator.
# '/' in the decorator maps directly to the homepage.
# The index function is triggered when the URL is visited.
@app.route('/')
def index():
    """Homepage."""

    return render_template('homepage.html')


# GET: The browser tells the server to just get the information stored on
# that page and send it.
# POST: The browser tells the server that it wants to post some new
# information to that URL and that the server must ensure the data is stored and
# only stored once. This is how HTML forms usually transmit data to the server.
@app.route('/login')
def display_login():
    """Login page."""

    return render_template('login_form.html')


@app.route('/login', methods=['POST'])
def handle_login():
    """Process login. Store user in session."""

    # Grab the users input.
    email = request.form.get("email")
    password = bcrypt.generate_password_hash(request.form.get("password"))

    # Check that the user exists.
    uq = User.query
    user_object = uq.filter_by(email=email).first()

    if user_object and bcrypt.check_password_hash(password, user_object.password):
        flash("Hello again!")
        session["user_email"] = user_object.email
        session["user_id"] = user_object.id

        return redirect("/landing-page")
    else:
        flash("Oops! Email / Password mismatch: Try again.")
        return redirect("/login")


@app.route('/register')
def register():
    """Registration page."""

    fb_id = request.args.get('fb_id')

    session["fb_id"] = fb_id

    return render_template('registration_form.html')


@app.route('/registration-success', methods=['POST'])
def registration_success():
    """Inform new user that they've been added."""

    first_name = request.form.get('fname')
    last_name = request.form.get('lname')
    email = request.form.get('email')
    password = request.form.get('password')
    fb_id = request.form.get('fb_id')

    # Add the user as long as the email isn't already taken.
    email_exists = db.session.query(User).filter_by(email=email).first()

    if email_exists is None:
        new_user = User(fb_id=fb_id, first_name=first_name, last_name=last_name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        session["email"] = email
    else:
        flash("Email {} is taken.".format(email))
        return redirect('/register')

    # Grab the id of the user that just signed in.
    user_id = db.session.query(User.id).filter_by(email=email).first()[0]

   # Add the user to the session.
    email = request.form['email']
    password = request.form['password']

    user = User.query.filter_by(email=email).first()
    session["user_id"] = user.id

    return render_template('registration_success.html',
                           first_name=first_name,
                           email=email,
                           user_id=user_id)


@app.route('/check_email_existence')
def query_db_for_email():
    """Hidden route that processes Facebook's API results."""

    email = request.args.get('email')
    fb_id = request.args.get('id')

    # Check to see whether the email address exists in the database.
    # If so, return the user_id.
    email_exists = db.session.query(User.id).filter_by(email=email).first()

    # If the email exists, take the user to the landing page.
    if email_exists:
        url = '/landing-page/%s' % (email_exists[0])
        return redirect(url)
    # Otherwise, check for the existence of the fb_id in the database.
    else:
        # Grab the associated user_id to feed to the landing page url.
        fb_id_exists = db.session.query(User.id).filter_by(fb_id=fb_id).first()

        # If the fb_id exists, take the user to the landing page.
        if fb_id_exists:
            url = '/landing-page/%s' % (fb_id_exists[0])
            return redirect(url)
        # Otherwise, take them to the registration page.
        else:
            return redirect(url_for('register', fb_id=fb_id))


@app.route('/add-contacts')
def add_contacts():
    """User manually adds contacts and categorizes them as a friend, family, or professional."""

    return render_template("add_contact.html")


@app.route('/contact-added', methods=['POST'])
def contact_added():
    """Confirmation page that user has been added."""

    first_name = request.form.get('fname')
    last_name = request.form.get('lname')
    relatp = request.form.get('relatp')

    relatp_type = ''

    # Change the relapt_type to match the table it will be committed to.
    if relatp == 'friend':
        relatp_type = 'fr'
    elif relatp == 'family':
        relatp_type = 'fam'
    else:
        relatp_type = 'prf'

    # Add the new contact to the db.
    new_contact = Relationship(user_id=user_id, first_name=first_name, last_name=last_name, relatp_type=relatp_type)
    db.session.add(new_contact)
    db.session.commit()

    # Grab the id of the relationship that was just created.
    new_contact_info = db.session.query(Relationship.id).filter_by(user_id=user_id, first_name=first_name, last_name=last_name, relatp_type=relatp_type).all()[0][0]

    return render_template("contact_added.html",
                           first_name=first_name,
                           last_name=last_name,
                           relatp=relatp,
                           user_id=user_id,
                           relatp_id=new_contact_info)


@app.route('/methods-of-reaching-out/<int:user_id>/<int:relatp_id>')
def specify_methods_of_reaching_out(user_id, relatp_id):
    """User can select methods of reaching out from a list."""

    # Given the relatp_id, grab the relationship type (friend, family, or professional).
    relatp_type = db.session.query(Relationship.relatp_type).filter_by(id=relatp_id).all()[0][0]

    # Grab the recommendation list associated with the relationship type.
    rcmdn_list = db.session.query(Recommendation).filter_by(relatp_type=relatp_type).all()

    return render_template('reach_out.html',
                           user_id=user_id,
                           relatp_type=relatp_type,
                           relatp_id=relatp_id,
                           rcmdn_list=rcmdn_list)


@app.route('/methods-success/<int:user_id>/<int:relatp_id>', methods=['POST'])
def method_specification_success(user_id, relatp_id):
    """Add the methods specified to the relationship."""

    # Grab the recommendation list specified for the relationship.
    desired_list = request.form.getlist('rcmdn')

    # Add the customized list to the respective relationship.
    update_relatp = Relationship.query.filter_by(user_id=user_id, id=relatp_id).first()
    update_relatp.rcmdn_list = desired_list

    # The created_at column should be placed in the Relationship table.
    created_at = db.session.query(Relationship.created_date).filter_by(id=relatp_id).one()

    # Turn the query result (a tuple of datetime) into an Arrow-friendly format.
    arrow_created_at = arrow.get(created_at[0])

    # The start date of all events will be a month from the date he/she was added.
    start_date = arrow_created_at.replace(months=+1)

    # Events will be scheduled for a max of a year for demo purposes.
    yr_from_now = start_date.replace(years=+1)

    # Create events for the duration of the year.
    # Friends and family should have an event a month.
    # Professional contacts should have an event per quarter.
    while start_date < yr_from_now:

        for desired_item in desired_list:

            if update_relatp.relatp_type == 'fr' or update_relatp.relatp_type == 'fam':

                # Convert from arrow format to datetime format for db storage.
                new_event = Event(user_id=user_id, relatp_id=relatp_id, rcmdn=desired_item, scheduled_at=start_date.datetime)
                db.session.add(new_event)

                start_date = start_date.replace(months=+1)

            else:
                new_event = Event(user_id=user_id, relatp_id=relatp_id, rcmdn=desired_item, scheduled_at=start_date.datetime)
                db.session.add(new_event)

                start_date = start_date.replace(months=+4)

    db.session.commit()

    return render_template('reach_out_added.html',
                           user_id=user_id,
                           desired_list=desired_list)


@app.route('/landing-page')
def landing_page():
    """Page where users land after logging in or signing up."""

    # Display the name of all of the reltionships a user has.
    # A list of tuples are returned.
    # The relationships id will be used to create a link to their profile.
    # The user_id is needed in the query results to pass into my Jinja for loop.
    print session["user_id"]
    contact_name_and_id = db.session.query(Relationship.id, Relationship.first_name, Relationship.last_name).filter_by(user_id=session["user_id"]).order_by(Relationship.first_name).all()

    return render_template("landing_page.html",
                           contact_name_and_id=contact_name_and_id)


@app.route('/contact-display/<int:relatp_id>')
def contact_display(relatp_id):
    """Display a selected contacts profile."""

    # Query for all the data related to a relationship.
    # Returns a list of objects.
    relatp_info = db.session.query(Relationship).filter_by(id=relatp_id).all()

    session['user_id'] = 'user_id'
    return render_template("contact_display.html",
                           relatp_id=relatp_id,
                           relatp_info=relatp_info)


@app.route('/contact-display-handler', methods=['POST'])
def contact_display_hander():
    """Handle the updates on the relationships."""

    relatp_id = request.form.get("id")

    # Assign a var to the inputted value of the new information.
    value = request.form.get("value")

    # Assign a var to the field getting updated.
    type_button = request.form.get("typeButton")

    # Grab the person getting updated.
    relationship = Relationship.query.get(relatp_id)

    # Update the existing record for the relationship.
    setattr(relationship, type_button, value)

    db.session.commit()

    user_info = {'typeButton': type_button,
                 'value': value}

    return jsonify(user_info)


@app.route('/event-display')
def event_display():
    """Display a selected contacts profile."""

    # Store all of a users events in a list.
    all_events = []

    # Grab the text and time of all of the users relationship.
    # Returns a list of tuples.
    rcmdn_and_date = db.session.query(Event.rcmdn, Event.scheduled_at, Event.relatp_id).filter_by(user_id=user_id).order_by(Event.scheduled_at).all()

    # Grab the name of the relationship.
    # Store the name, text, and time in the all_events list.
    for rcmdn in rcmdn_and_date:
        relatp_id = rcmdn.relatp_id
        relatp_name = db.session.query(Relationship.first_name, Relationship.last_name).filter_by(id=relatp_id).one()
        all_events.append([relatp_name.first_name, relatp_name.last_name, rcmdn[0], rcmdn[1].date()])

    return render_template("event.html",
                           all_events=all_events)


@app.route('/logout')
def process_logout():
    """Log user out."""

    del session["user_id"]
    flash("Logged out.")
    return render_template('logout.html')


@app.route("/error")
def error():
    raise Exception("Error!")


# App will only run if we ask it to run.
if __name__ == "__main__":

    # Setting this to be true so that I can invoke the DebugToolbarExtension
    app.debug = True

    # Use the DebugToolbar
    # DebugToolbarExtension(app)

    connect_to_db(app)

    # Connection for Heroku.
    # connect_to_db(app, os.environ.get("DATABASE_URL"))

    # Create the tables we need from our models (if they already
    # exist, nothing will happen here, so it's fine to do this each
    # time on startup)
    # db.create_all(app=app)

    DEBUG = "NO_DEBUG" not in os.environ
    PORT = int(os.environ.get("PORT", 5000))

    # debug=True runs Flask in "debug mode". It will reload my code when it
    # changes and provide error messages in the browser.
    # The host makes the server publicly available by adding 0.0.0.0. This
    # tells my operating system to listen on all public IPs.
    # Port 5000 required for Flask.
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG)
