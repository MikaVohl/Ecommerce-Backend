# Ecommerce Backend
This project is a Flask API that combines your own SQL database with Stripe's payment processing library to streamline the Ecommerce functionality needed for your site. Within app.py, there are a range of endpoints defined that will make it easy to manage customers, subscriptions, and individual payments.

## Requirements

### Environmental Variables
```
STRIPE_SECRET_KEY = 'your_stripe_secret_key'
STRIPE_WEBHOOK_KEY = 'your_stripe_webhook_key'

driver = 'your_SQL_driver' (ex. '{ODBC Driver 17 for SQL Server}')
server = 'your_server_destination' (ex. 'company.database.windows.net')
database = 'your_database_name' (ex. production)
username = 'your_username'
password = 'your_password'
```
### Packages
Install the python packages listed in ```requirements.txt```

## How To Run
Run the Flask application by executing $ flask run

## Directory
### ```app.py```
This file defines all API endpoints. app.py uses many functions defined in utils.py.
### ```utils.py```
This file defines various intermediate functions. Its primary function is to handle the bulk of the processing and interact directly with the database.
### ```stripe_utils.py```
This file defines various stripe-related functions. Its primary function is to interact with the stripe API.
### ```/static```
This directory contains sample HTML and JS files for a basic frontend to the application
