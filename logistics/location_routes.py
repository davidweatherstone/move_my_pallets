from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from logistics.auth import customer_only
from logistics.db import get_db
from logistics.forms import LocationForm


bp = Blueprint("location_routes", __name__)


@bp.route("/manage-locations", methods=("GET", "POST"))
@customer_only
def manage_locations():
    """
    Handle requests to the /manage-locations endpoint for managing customer locations.

    Retrieves and displays all locations created by the current user's company from the database.
    Displays a list of locations with details including ID, name, street, city, country, zipcode, 
    and the company that created each location.

    Returns:
        Response: Rendered template 'manage_locations.html' with the following context variable:
            - locations: A list of dictionaries representing locations, each containing:
    """
    
    db = get_db()
    locations = db.execute(
        """
        SELECT 
            l.id, 
            name, 
            street, 
            city, 
            country, 
            zipcode,
            u.company
        FROM location l
        LEFT JOIN user u 
            ON u.id = l.created_by
        WHERE u.company = ?
        """, (g.user["company"],)
    ).fetchall()
        
    return render_template(
        "/customer/locations/manage_locations.html",
        locations=locations
    )


@bp.route("/create-location", methods=("GET", "POST"))
@customer_only
def create_location():
    """
    Handle requests to the /create-location endpoint for creating a new customer location.

    Provides a form for users to input details such as name, street, city, country, and zipcode
    for a new location. On form submission, validates and inserts the new location into the database
    associated with the current user's company.

    Returns:
        Response: Rendered template 'create_location.html' with the following context variable:
            - form: An instance of LocationForm used for creating a new location.

    On successful form submission:
        - Inserts a new record into the 'location' table with details provided by the user.
        - Redirects the user to the 'manage_locations' endpoint to view the updated list of locations.
    """
    
    form = LocationForm()
    if request.method == "POST":
        created_by = g.user["id"]
        name = form.name.data
        street = form.street.data
        city = form.city.data
        country = form.country.data
        zipcode = form.zipcode.data
        error = None
    
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO location (created_by, name, street, city, country, zipcode)'
                ' VALUES (?, ?, ?, ?, ?, ?)',
                (created_by, name, street, city, country, zipcode))
            db.commit()
            return redirect(url_for("location_routes.manage_locations"))
        
    return render_template(
        "/customer/locations/create_location.html",
        form=form
    )
    

def get_location(id, check_created_by=True):
    """
    Retrieve a location from the database by its ID.

    Args:
        id (int): The ID of the location to retrieve.
        check_created_by (bool, optional): Whether to check if the current user created the location.
            Defaults to True.

    Returns:
        dict: A dictionary representing the location with the following keys:

    Raises:
        404 Error: If no location with the specified ID exists in the database.
        403 Error: If check_created_by is True and the current user did not create the location.
    """
    
    db = get_db()
    location = db.execute(
        """
        SELECT 
            l.id, 
            created_by, 
            name, 
            street, 
            city, 
            country, 
            zipcode, 
            created_date
        FROM location l
        WHERE l.id = ?
        """, (id,)
    ).fetchone()
    
    if location is None:
        abort(404, f"Location id {id} does not exist.")
    
    if check_created_by and location["created_by"] != g.user["id"]:
        abort(403)
        
    return location
    
    
@bp.route("/<int:id>/update-location", methods=("GET", "POST"))
@customer_only
def update_location(id):
    """
    Handle requests to the /<int:id>/update-location endpoint for updating a customer location.

    Retrieves the location with the specified ID from the database using get_location().
    Pre-fills a form with existing location details for editing.
    On form submission, updates the location record in the database with new details.

    Args:
        id (int): The ID of the location to update.

    Returns:
        Response: Rendered template 'update_location.html' with the following context variable:
            - form: An instance of LocationForm pre-filled with location details for editing.

    On successful form submission:
        - Updates the corresponding record in the 'location' table with edited details.
        - Redirects the user to the 'manage_locations' endpoint to view the updated list of locations.
    """
    
    location = get_location(id)
    
    form = LocationForm(data=location)
    form.submit.label.text = "Update"
    
    if request.method == "POST":
        name = form.name.data
        street = form.street.data
        city = form.city.data
        country = form.country.data
        zipcode = form.zipcode.data

        try:
            db = get_db()
            db.execute(
                'UPDATE location SET name = ?, street = ?, city = ?, country = ?, zipcode = ?'
                ' WHERE id = ?',
                (name, street, city, country, zipcode, id))
            db.commit()
            return redirect(url_for("location_routes.manage_locations"))
        except Exception as e:
            db.rollback()
            flash(f"An error occured while creating the location: {str(e)}", "error")

    return render_template(
        "customer/locations/update_location.html",
        form=form
    )


@bp.route("/<int:id>/delete-location", methods=("GET", "POST"))
@customer_only
def delete_location(id):
    """
    Handle requests to the /<int:id>/delete-location endpoint for deleting a customer location.

    Retrieves the location with the specified ID from the database using get_location().
    Deletes the location record from the database upon confirmation.

    Args:
        id (int): The ID of the location to delete.

    Returns:
        Response: Redirects to the 'manage_locations' endpoint after successfully deleting the location.
    """
    
    if get_location(id) is not None:    
        db = get_db()
        
        try:
            db.execute("DELETE FROM location WHERE id = ?", (id,))
            db.commit()
        except Exception as e:
            db.rollback()
            flash(f"An error has occurred while attempting to delete the location: {str(e)}", "error")
            
    return redirect(url_for("location_routes.manage_locations"))