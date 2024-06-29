## enter the venv: source venv/Scripts/activate
## run the application: flask --app APP_FOLDER_NAME_HERE run --debug
## initialize the database (i.e. reset/create): flask --app APP_NAME_HERE init-db


# company1customer1@company1.com - customer
# company1customer2@company1.com - customer
# company2customer3@company2.com - customer
# company2customer4@company2.com - customer
# company3supplier1@company3.com - supplier
# company3supplier2@company3.com - supplier
# company4supplier3@company4.com - supplier
# company4supplier4@company4.com - supplier

import os

from flask import Flask, render_template
from flask_bootstrap import Bootstrap5


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    Bootstrap5(app)

    # app.config.from_mapping(
    #     SECRET_KEY="dev",
    #     DATABASE=os.path.join(app.instance_path, "logistics.sqlite")
    # )

    app.config.from_mapping(
        SECRET_KEY=os.environ.get('FLASK_KEY'),
        DATABASE=os.path.join(app.instance_path, "logistics.sqlite")
    )
     
    
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)
        
    # ensure that the instance folder exists
    try:
        os.mkdir(app.instance_path)
    except OSError:
        pass
    
    
    @app.route("/")
    def home():
        return render_template(
            "index.html"
        )
    
    
    # Database c
    from . import db
    db.init_app(app)
    
    
    # Files that provide the routes within the app
    from . import auth
    app.register_blueprint(auth.bp)
        
    
    from . import location_routes
    app.register_blueprint(location_routes.bp)
    app.add_url_rule("/", endpoint="index")
    
    
    from . import customer_routes
    app.register_blueprint(customer_routes.bp)
    app.add_url_rule("/", endpoint="index")
    
    
    from . import supplier_routes
    app.register_blueprint(supplier_routes.bp)
    app.add_url_rule("/", endpoint="index")
  
  
    return app



if __name__ == "__main__":
    create_app()