from functools import wraps

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from logistics.db import get_db
from logistics.forms import RegisterForm, LoginForm


bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=("GET", "POST"))
def register():
    """
    Handle requests to the /register endpoint for user registration.

    Validates and processes user registration form data.
    Inserts a new user record into the 'user' table upon successful validation.
    Redirects to the login page upon successful registration.

    Returns:
        Response: Rendered template 'register.html' with the following context variable:
            - form: An instance of RegisterForm for user registration.

    On form submission:
        - Validates the submitted form data (email, password, company, user_type, full_name).
        - Hashes the password using generate_password_hash() for security.
        - Inserts a new user record into the database.
        - Redirects to the 'auth.login' endpoint for user login.

    Displays error messages via flash() for missing or invalid form data.

    Raises:
        IntegrityError: If the email provided already exists in the database, displays an error message.
    """

    form = RegisterForm()
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        company = request.form["company"]
        user_type = request.form["user_type"]
        full_name = request.form["full_name"]
        db = get_db()
        error = None
        
        if not email:
            error = "email is required."
        elif not password:
            error = "password is required."
        elif not company:
            error = "company is required."
        elif not user_type:
            error = "user type is required"
        elif not full_name:
            error = "full name is required"
            
        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (email, password, company, user_type, full_name) VALUES (?, ?, ?, ?, ?)",
                    (email, generate_password_hash(password), company, user_type, full_name),
                )
                db.commit()
            except db.IntegrityError:
                error = f"User {email} is already registered."
            else:
                return redirect(url_for("auth.login"))
            
        flash(error)
    
    return render_template(
        "auth/register.html",
        form=form
    )


@bp.route("/login", methods=("GET", "POST"))
def login():
    """
    Handle requests to the /login endpoint for user authentication.

    Validates and processes user login form data.
    Checks if the provided email exists in the database and verifies the password.
    Initiates a user session upon successful login and redirects to the index page.

    Returns:
        Response: Rendered template 'login.html' with the following context variable:
            - form: An instance of LoginForm for user login.

    On form submission:
        - Retrieves the submitted email and password from the login form.
        - Queries the database for a user record with the provided email.
        - Checks if the user exists and verifies the password using check_password_hash().
        - Initiates a session by setting 'user_id' in the session object upon successful login.
        - Redirects to the 'index' endpoint after successful authentication.

    Displays error messages via flash() for incorrect email or password.

    Raises:
        KeyError: If 'user_id' is not found in the session object.
    """
    
    form = LoginForm()
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        db = get_db()
        error = None
        user = db.execute(
            "SELECT * FROM user WHERE email = ?", (email,)
        ).fetchone()
        
        if user is None:
            error = "Incorrect email."
        elif not check_password_hash(user["password"], password):
            error = "Incorrect password."
            
        if error is None:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("index"))
        
        flash(error)
        
    return render_template(
        "auth/login.html",
        form=form
    )


@bp.before_app_request
def load_logged_in_user():
    """
    Before handling each request, load the logged-in user's information into the global 'g' object.

    Retrieves the 'user_id' from the session object.
    If 'user_id' exists:
        - Fetches the user record from the database using the 'user_id'.
        - Stores the user information in the global 'g.user' for access during request handling.
    If 'user_id' does not exist:
        - Sets 'g.user' to None.

    This function ensures that the logged-in user's information is available globally for each request.
    """
    
    user_id = session.get("user_id")
    
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()
        

@bp.route("/logout")
def logout():
    """
    Handle requests to the /logout endpoint for user logout.

    Clears the user session, effectively logging out the current user.
    Redirects to the 'index' endpoint after clearing the session.

    Returns:
        Response: Redirect response to the 'index' endpoint.

    Notes:
        Clears the session by calling session.clear().
        Redirects to the 'index' endpoint using redirect(url_for('index')).
    """
    session.clear()
    return redirect(url_for("index"))


# Create logged in-only decorators
def login_required(view):
    """
    Decorator function to enforce user authentication for a view function.

    Checks if a user is logged in by inspecting the global 'g.user' object.
    If 'g.user' is None (i.e., user is not logged in):
        - Redirects to the 'auth.login' endpoint for user login.
    If 'g.user' is not None (i.e., user is logged in):
        - Calls the decorated view function with any provided keyword arguments.

    Args:
        view (function): The view function to be decorated.

    Returns:
        function: Decorated view function.

    Notes:
        Uses Flask's redirect() and url_for() functions for redirection.
        Preserves the original view function's metadata using functools.wraps.
    """
    
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        
        return view(**kwargs)
    
    return wrapped_view


def supplier_only(f):
    """
    Decorate function that is the same as login_required decorator but specifically
    checks that a users "user_type" is equal to "Supplier"
    """
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If user_type is not Supplier then redirect to login page
        if g.user["user_type"] != "Supplier":
            return redirect(url_for("auth.login"))
        # Otherwise continue with the route function
        return f(*args, **kwargs)

    return decorated_function


def customer_only(f):
    """
    Decorate function that is the same as login_required decorator but specifically
    checks that a users "user_type" is equal to "Customer"
    """
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If user_type is not Customer then redirect to login page
        if g.user["user_type"] != "Customer":
            return redirect(url_for("auth.login"))
        # Otherwise continue with the route function
        return f(*args, **kwargs)

    return decorated_function