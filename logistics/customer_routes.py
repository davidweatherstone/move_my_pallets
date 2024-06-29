from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from logistics.auth import customer_only
from logistics.db import get_db
from logistics.forms import RequestForm


bp = Blueprint("customer_routes", __name__)


@bp.route("/customer-requests")
@customer_only
def customer_requests():
    """
    Display a list of requests created by the current user's company.

    This endpoint retrieves all requests associated with the company of the currently logged-in user 
    and renders them in the 'customer_requests.html' template.

    Returns:
        Response: Rendered template 'customer_requests.html' with the following context variables:
            - requests: A list of dictionaries, each containing the details of a request created by the current user's company. 
    """
    
    db = get_db()
    requests = db.execute(
        """
        SELECT 
            id, 
            collection_address, 
            delivery_address, 
            collection_date, 
            delivery_date, 
            request_status, 
            pallets,
            weight,
            company
        FROM request
        WHERE company = ?
        ORDER BY created_date DESC
        """, (g.user["company"],)
    ).fetchall()
            
    return render_template(
        "/customer/requests/customer_requests.html",
        requests=requests
    )

  
@bp.route("/create-request", methods=("GET", "POST"))
@customer_only
def create_request():
    """
    Handle the creation of a new customer request.

    This endpoint allows a customer to create a new request by filling out and submitting a form.
    It handles both the GET and POST methods:
    - GET: Renders the 'create_request.html' template with an empty RequestForm.
    - POST: Processes the submitted form data, creates a new request record in the database, and redirects to the customer requests page.

    Returns:
        Response: 
        - GET: Renders the 'create_request.html' template with the RequestForm.
        - POST: Redirects to the 'customer_requests' page after successfully creating a new request.

    Context Variables:
        form (RequestForm): The form used to create a new request.
    """
    
    form = RequestForm()
    
    if request.method == "POST":
        created_by = g.user["id"]
        collection_date = form.collection_date.data.strftime("%Y-%m-%d %H:%M:%S")
        delivery_date = form.delivery_date.data.strftime("%Y-%m-%d %H:%M:%S")
        collection_address = form.collection_address.data
        delivery_address = form.delivery_address.data
        pallets = form.pallets.data
        weight = form.weight.data
        company = g.user["company"]

        try:
            db = get_db()
            db.execute(
                """
                INSERT INTO request (created_by, collection_date, delivery_date, collection_address, delivery_address, pallets, weight, company)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (created_by, collection_date, delivery_date, collection_address, delivery_address, pallets, weight, company)
            )
            db.commit()
            return redirect(url_for("customer_routes.customer_requests"))
        except Exception as e:
            db.rollback()
            flash(f"An error occurred while creating the request: {str(e)}", "error")
        
    return render_template(
        "/customer/requests/create_request.html",
        form=form)


def customer_get_request(id):
    """
    Retrieve a specific customer request by its ID.

    This helper function queries the database to fetch the details of a customer request identified by the given ID.
    If the request is not found, it aborts with a 404 error.

    Parameters:
        id (int): The ID of the customer request to be retrieved.

    Returns:
        dict: A dictionary containing the details of the specified customer request. 
        
    Raises:
        404: If the request is not found for the specified ID.
    """
    
    db = get_db()
    request = db.execute(
        """
        SELECT 
            r.id, 
            collection_address, 
            delivery_address, 
            collection_date, 
            delivery_date,
            pallets,
            weight,
            request_status
        FROM request AS r
        WHERE r.id = ?
        """, (id,)
    ).fetchone()
        
    if request is None:
        abort(404, f"Request id {id} doesn't exist.")
        
    return request


def customer_get_bids(id):
    """
    Retrieve all bids associated with a specific customer request.

    This helper function queries the database to fetch all bids related to the given request ID.
    If no bids are found, it aborts with a 404 error.

    Parameters:
        id (int): The ID of the customer request for which bids are to be retrieved.

    Returns:
        list: A list of dictionaries, each containing the details of a bid associated with the specified request. 

    Raises:
        404: If no bids are found for the specified request ID.
    """
    
    db = get_db()
    bids_received = db.execute(
        """
        SELECT
            b.id AS bid_id,
            b.bid_amount,
            b.created_date,
            b.bid_status,
            u.company
        FROM bid b
        LEFT JOIN user u
            ON b.created_by = u.id
        WHERE b.request_id = ?
        """, (id,)
    ).fetchall()
    
    if bids_received is None:
        abort(404, f"Request id {id} doesn't exist.")
    
    return bids_received
    

@bp.route("/<int:id>/customer-request", methods=("GET", "POST"))
@customer_only
def view_request(id):
    """
    Retrieve and display a customer request along with its associated bids.

    This endpoint handles GET and POST requests to display a specific customer request and all bids made against it.
    It fetches the request details and the associated bids from the database and renders them using the 
    'customer_request.html' template.

    Parameters:
        id (int): The ID of the customer request to be retrieved and displayed.

    Returns:
        Response: A rendered template 'customer_request.html' with the following context variables:
            - request: A dictionary containing the details of the specified customer request.
            - bids: A list of dictionaries, each containing details of a bid associated with the specified request.
    """
    
    try:
        request = customer_get_request(id)
        bids = customer_get_bids(id)
    except Exception as e:
        flash(f"An error occurred: {str(e)}", "error")
        return redirect(url_for("customer_routes.customer_requests"))

    return render_template(
        "/customer/requests/customer_request.html",
        request=request,
        bids=bids
    )
    
    
@bp.route("/<int:id>/remove-request", methods=("GET", "POST"))
@customer_only
def remove_request(id):
    """
    Handle the removal of a customer request.

    This route allows a customer to remove a request specified by the ID if the request is not already complete.
    If the request is complete, it cannot be removed and an error message is generated.

    Parameters:
        id (int): The ID of the request to be removed.

    Returns:
        Response: A redirection to the customer requests page if the request is successfully removed.
        If the request is complete, it does not redirect and an error message is generated.
    """
    
    db = get_db()
    error = None
    request_status = db.execute(
        """
        SELECT 
            request_status
        FROM request
        WHERE id = ?
        """, (id,)
    ).fetchone()
    
    if request_status is None:
        error = "Request does not exist. No request to remove."
        flash(error,"error")
        return redirect(url_for("customer_routes.customer_requests"))
    elif request_status and request_status[0] == "Complete":
        error = "Request is complete. Unable to remove."
        flash(error, "error")
    else:
        try:
            db.execute(
                """
                DELETE FROM request 
                WHERE id = ?
                """, (id, )
                )
            db.commit()
            flash("Request deleted successfully.", "success")
        except Exception as e:
            db.rollback()
            flash(f"An error has occurred while attempting to delete the request: {str(e)}", "error")
        
        return redirect(url_for("customer_routes.customer_requests"))
    

@bp.route("/<int:id>/update-request", methods=("GET", "POST"))
@customer_only
def update_request(id):
    """
    Handle the updating of a specific customer request.

    This endpoint allows a customer to update an existing request by filling out and submitting a form.
    It handles both the GET and POST methods:
    - GET: Pre-fills the form with the current details of the request and renders the 'update_request.html' template.
    - POST: Processes the submitted form data, updates the request record in the database, and redirects to the view request page.

    Parameters:
        id (int): The ID of the customer request to be updated.

    Returns:
        Response: 
        - GET: Renders the 'update_request.html' template with the pre-filled RequestForm.
        - POST: Redirects to the 'view_request' page after successfully updating the request.

    Context Variables:
        form (RequestForm): The form used to update the request.
    """
    
    this_request = customer_get_request(id)
    
    form = RequestForm(data=this_request)
    form.submit.label.text = "Update"
    
    if request.method == "POST":
        collection_date = form.collection_date.data.strftime("%Y-%m-%d %H:%M:%S")
        delivery_date = form.delivery_date.data.strftime("%Y-%m-%d %H:%M:%S")
        collection_address = form.collection_address.data
        delivery_address = form.delivery_address.data
        pallets = form.pallets.data
        weight = form.weight.data

        try:
            db = get_db()
            db.execute(
                """
                UPDATE request SET 
                    collection_address = ?, 
                    delivery_address = ?, 
                    collection_date = ?, 
                    delivery_date = ?,
                    pallets = ?,
                    weight = ?
                WHERE id = ?
                """, (collection_address, delivery_address, collection_date, delivery_date, pallets, weight, this_request[0])
            )
            db.commit()
            flash("Request updated successfully.", "success")
            
            return redirect(url_for("customer_routes.view_request", id=id))
        except Exception as e:
            db.rollback()
            flash(f"An error has occurred while attempting to update the request: {str(e)}", "error")
    
    return render_template(
        "/customer/requests/update_request.html",
        form=form
    )    

    
@bp.route("/<int:bid_id>/accept", methods=("GET", "POST"))
@customer_only
def accept_bid(bid_id):
    """
    Handle accepting a bid for a specific request.

    This endpoint allows a customer to accept a bid by its ID. Upon acceptance:
    - Updates the request associated with the bid to 'Complete' status.
    - Updates the accepted bid to 'Accepted' status.
    - Updates all other bids for the same request to 'Rejected' status, except the accepted bid.

    Parameters:
        bid_id (int): The ID of the bid to be accepted.

    Returns:
        Response: Redirects to the 'view_request' page for the request associated with the accepted bid.
    """
    
    db = get_db()
    
    request_id = db.execute(
        """
        SELECT 
            request_id 
        FROM bid 
        WHERE id = ?
        """, (bid_id,)
    ).fetchone()
    
    if request_id:
        request_id = request_id[0]
        
        try:
            db.execute(
                """
                UPDATE request SET request_status = 'Complete'
                WHERE id = ?
                """, (request_id,)
            )
            
            db.execute(
                """
                UPDATE bid SET bid_status = 'Accepted'
                WHERE id = ?
                """, (bid_id,)
            )
            
            db.execute(
                """
                UPDATE bid SET bid_status = 'Rejected'
                WHERE request_id = ? AND id is not ?
                """, (request_id, bid_id)
            )
            
            db.commit()
            return redirect(url_for("customer_routes.view_request", id=request_id))
        except Exception as e:
            db.rollback()
            flash(f"An error has occurred while accepting the request: {str(e)}", "error")
            

@bp.route("/<int:bid_id>/reject", methods=("GET", "POST"))
@customer_only
def reject_bid(bid_id):
    """
    Handle rejecting a bid for a specific request.

    This endpoint allows a customer to reject a bid by its ID. Upon rejection:
    - Updates the status of the bid to 'Rejected'.

    Parameters:
        bid_id (int): The ID of the bid to be rejected.

    Returns:
        Response: Redirects to the 'view_request' page for the request associated with the rejected bid.
    """
    
    db = get_db()
    
    request_id = db.execute(
        """
        SELECT 
            request_id 
        FROM bid 
        WHERE id = ?
        """, (bid_id,)
    ).fetchone()
    
    number_of_bids = db.execute(
        """
        SELECT
            COUNT(request_id) AS count
        FROM bid
        WHERE bid_status is not 'Rejected' AND request_id = ?
        """, (request_id[0],)
    ).fetchone()
    
    try:  
        if request_id:
            request_id = request_id[0]
                    
            db.execute(
                """
                UPDATE bid SET bid_status = 'Rejected'
                WHERE id = ?
                """, (bid_id,)
            )
            
        if number_of_bids["count"] == 1:            
            db.execute(
                """
                UPDATE request SET request_status = "Awaiting bids"
                WHERE id = ?
                """, (request_id,)
            )
            
        db.commit()
        return redirect(url_for("customer_routes.view_request", id=request_id))
    except Exception as e:
        db.rollback()
        flash(f"An error has occurred while attempting to reject the request: {str(e)}", "error")
          