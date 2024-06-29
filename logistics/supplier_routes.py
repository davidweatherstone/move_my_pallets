from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from logistics.auth import supplier_only
from logistics.db import get_db
from logistics.forms import BidForm

bp = Blueprint("supplier_routes", __name__)

@bp.route("/supplier-requests")
@supplier_only
def supplier_requests():
    """
    Display lists of live requests, requests bid on, and requests where bids have been won by the current user's company.

    This endpoint retrieves and categorizes requests based on their status and associated bids. It renders these categorized lists
    in the 'supplier_requests.html' template.

    Returns:
        Rendered template 'supplier_requests.html' with context variables:
            - live_requests_not_bid: Live requests not yet bid on by the user's company.
            - requests_bid: Requests for which bids have been submitted by the user's company.
            - requests_bid_won: Requests where the user's company bids have been accepted.
    """
    
    user_company = g.user["company"]
    db = get_db()
    
    live_requests_not_bid = db.execute(
        """
        SELECT 
            r.id AS request_id, 
            collection_date, 
            delivery_date, 
            collection_address, 
            delivery_address, 
            pallets,
            weight,
            r.company
        FROM request r
        LEFT JOIN ( SELECT
                        b.id, 
                        b.request_id, 
                        b.created_by, 
                        u.company 
                    FROM bid b
                    LEFT JOIN user u
                        ON u.id = b.created_by
                    WHERE u.company = ?) cb
            ON cb.request_id = r.id
        WHERE cb.company is not ? AND r.request_status is not 'Complete'
        ORDER BY r.id
        """, (user_company, user_company)
    ).fetchall()
    
    requests_bid = db.execute(
        """
        SELECT 
            r.id AS request_id, 
            collection_date, 
            delivery_date, 
            collection_address, 
            delivery_address, 
            pallets,
            weight,
            r.company,
            b.id AS bid_id
        FROM request r
        LEFT JOIN bid b 
            ON r.id = b.request_id
        LEFT JOIN user u
            ON u.id = b.created_by
        WHERE b.id is not null AND u.company = ? AND r.request_status is not 'Complete'
        ORDER BY r.id
        """, (user_company,)
    ).fetchall()
    
    requests_bid_won = db.execute(
        """
        SELECT 
            r.id AS request_id, 
            collection_date, 
            delivery_date, 
            collection_address, 
            delivery_address, 
            pallets,
            weight,
            r.company,
            b.id AS bid_id
        FROM request r
        LEFT JOIN bid b 
            ON r.id = b.request_id
        LEFT JOIN user u
            ON u.id = b.created_by
        WHERE b.bid_status is not 'Rejected' AND u.company = ? AND r.request_status = 'Complete'
        ORDER BY r.id
        """, (user_company,)
    ).fetchall()
    
    return render_template(
        "supplier/supplier_requests.html",
        live_requests_not_bid=live_requests_not_bid,
        requests_bid=requests_bid,
        requests_bid_won=requests_bid_won
    )


@bp.route("/<int:id>/supplier-request")
@supplier_only
def supplier_request(id):
    """
    Display details of a specific request and any associated bid submitted by the current user's company.

    This endpoint retrieves and displays details of a specific request and checks if there is a bid submitted
    by the current user's company for that request. If no bid exists, the 'bid' context variable will be None.

    Parameters:
        id (int): The ID of the request for which details are to be displayed.

    Returns:
        Response: Rendered template 'supplier_request.html' with the following context variables:
            - request: A dictionary containing details of the specific request. 
            - bid: A dictionary containing details of the bid submitted by the current user's company, if any.
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
    
    bid = db.execute(
        """
        SELECT 
        b.id,
        request_id,
        bid_amount,
        bid_status,
        b.created_date
        FROM bid b
        LEFT JOIN user u
            ON b.created_by = u.id
        WHERE request_id = ? AND u.company = ?
        """, (id, g.user["company"],)
    ).fetchone()
    
    if request is None:
        abort(404, f"Post id {id} doesn't exist.")
    
    return render_template(
        "supplier/supplier_request.html",
        request=request,
        bid=bid
    )
    
    
@bp.route("/my-bids")
@supplier_only
def my_bids():
    """
    Display a list of bids submitted by the current user's company.

    This endpoint retrieves all bids submitted by users belonging to the current user's company 
    and renders them in the 'my_bids.html' template.

    Returns:
        Response: Rendered template 'my_bids.html' with the following context variables:
            - bids: A list of dictionaries, each containing details of a bid submitted by the current user's company. 
    """
    
    db = get_db()
    user_company = g.user["company"]
    my_bids = db.execute(
        """
        SELECT 
            b.id,
            b.request_id,
            b.bid_amount,
            b.created_date,
            b.bid_status
        FROM bid b
        LEFT JOIN user u
            ON b.created_by = u.id
        WHERE u.company = ?
        ORDER BY b.created_date DESC
        """, (user_company, )
    ).fetchall()

    return render_template(
        "/supplier/my_bids.html",
        bids=my_bids
    )
    

@bp.route("/<int:id>/submit-bid", methods=("GET", "POST"))
@supplier_only
def submit_bid(id):
    """
    Handle the submission of a bid for a specific request.

    This endpoint provides a form for suppliers to submit a bid against a customer request identified by its ID.
    It handles both the GET and POST methods:
    - GET: Renders the 'submit_bid.html' template with an empty BidForm.
    - POST: Processes the submitted form data, creates a new bid record in the database, and updates the status
      of the associated request.

    Parameters:
        id (int): The ID of the request for which the bid is being submitted.

    Returns:
        Response: 
        - GET: Renders the 'submit_bid.html' template with the BidForm.
        - POST: Redirects to the 'my_bids' page after successfully submitting the bid.

    Context Variables:
        form (BidForm): The form used to submit a bid.
    """
    
    form = BidForm()
    
    if request.method == "POST":
        created_by = g.user["id"]
        bid_amount = form.bid_amount.data

        try:
            db = get_db()
            db.execute(
                """
                INSERT INTO bid (request_id, created_by, bid_amount)
                VALUES (?, ?, ?)                
                """, (id, created_by, bid_amount)
            )
            
            db.execute(
                """
                UPDATE request SET request_status = "Bid(s) received"
                WHERE id = ?
                """, (id, )
            )
             
            db.commit()
            return redirect(url_for("supplier_routes.my_bids"))
        except Exception as e:
            db.rollback()
            flash(f"An error occurred while submitting the bid: {str(e)}", "error")
        
    return render_template(
        "supplier/submit_bid.html",
        form=form
    )