from flask import Flask, request, send_from_directory, jsonify
from utils import InputError, assign_payment_method, create_cust, list_customers, list_payment_methods, get_item, log_payment, delete_payment_method, \
    deactivate_license, activate_license, handle_error, create_charge, get_checkout_links, handle_dispute, unsubscribe, get_subscription_status, \
    list_user_transactions, list_transactions, get_subscription_info, num_user_transactions, num_transactions, update_pay_date, subscribe_item, create_trial, \
    delete_customer, delete_cust_record, create_sub_plan, update_sub_plan, update_user_sub
import stripe, logging, os

app = Flask(__name__, static_url_path='')

webhook_logger = logging.getLogger('webhooks')
webhook_logger.setLevel(logging.WARNING)
handler = logging.FileHandler('webhooks.log', encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(message)s')
handler.setFormatter(formatter)
webhook_logger.addHandler(handler)

STRIPE_WEBHOOK_KEY = os.environ['STRIPE_WEBHOOK_KEY']

@app.route('/')
def home():
    return send_from_directory('static', 'index.html')
@app.route('/customers')
def customers():
    return send_from_directory('static', 'customers.html')
@app.route('/checkout')
def checkout():
    return send_from_directory('static', 'checkout.html')

def reject_params(data, required):
    for field in required:
        if field not in data or data[field] == '' or data[field] is None:
            raise InputError('Missing required field: ' + field)

@app.route('/create_charge', methods=['POST'])
def create_charge_route():
    try:
        data = request.json
        reject_params(data, ['custID', 'price', 'quantity'])
        return jsonify(create_charge(data['custID'], int(data['price']) * 100 * int(data['quantity']), data.get('description', 'Flat Fee'), data.get('payment_method'), data.get('save_card')))
    except Exception as e:
        return handle_error(e)

@app.route('/add_payment_method', methods=['POST'])
def add_payment_method():
    try:
        data = request.json
        reject_params(data, ['custID', 'payMethodID'])
        return jsonify(assign_payment_method(data['custID'], data['payMethodID']))
    except Exception as e:
        return handle_error(e)

@app.route('/remove_payment_method', methods=['POST'])
def remove_payment_method():
    try:
        data = request.json
        reject_params(data, ['payMethodID'])
        return jsonify(delete_payment_method(data['payMethodID']))
    except Exception as e:
        return handle_error(e)

@app.route('/create_customer', methods=['POST'])
def create_customer():
    try:
        data = request.json
        reject_params(data, ['ID', 'custType'])
        return jsonify(create_cust(data['ID'], data['custType'], data.get('email')))
    except Exception as e:
        return handle_error(e)

@app.route('/get_customers', methods=['GET'])
def get_customers():
    try:
        return jsonify(list_customers())
    except Exception as e:
        return handle_error(e)
    
@app.route('/get_payment_methods', methods=['POST'])
def get_cards():
    try:
        data = request.json
        reject_params(data, ['custID'])
        return jsonify(list_payment_methods(data['custID']))
    except Exception as e:
        return handle_error(e)

@app.route('/get_item', methods=['POST'])
def get_item_route():
    try:
        data = request.json
        reject_params(data, ['planID'])
        return jsonify(get_item(data['planID'])) # from the array of priceIDs in data, use get_item to get information and return each one in a json array
    except Exception as e:
        return handle_error(e)
    
@app.route('/checkout_links', methods=['POST'])
def checkout_links():
    try:
        data = request.json
        return jsonify(get_checkout_links(data.get('custType')))
    except Exception as e:
        return handle_error(e)
    
@app.route('/unsubscribe', methods=['POST'])
def cancel_sub():
    try:
        data = request.json
        reject_params(data, ['custID'])
        return jsonify(unsubscribe(data['custID']))
    except Exception as e:
        return handle_error(e)
    
# Get subscription / get subscription status
@app.route('/get_sub_status', methods=['POST']) # Returns only the status of the subscription, intended to determine access to services
def get_sub_status():
    try:
        data = request.json
        reject_params(data, ['custID'])
        return jsonify(get_subscription_status(data['custID']))
    except Exception as e:
        return handle_error(e)
    
@app.route('/get_user_transactions', methods=['POST'])
def get_user_transactions():
    try:
        data = request.json
        reject_params(data, ['custID'])
        page, max = data.get('page', 1), data.get('maxRecords', 10)
        if page < 1 or max < 0:
            raise InputError('Page and maxRecords must be positive integers')
        if max > 200:
            raise InputError('Max records must be less than or equal to 200')
        return jsonify(list_user_transactions(data['custID'], page, max))
    except Exception as e:
        return handle_error(e)
    
@app.route('/get_transactions', methods=['POST'])
def get_transactions():
    try:
        data = request.json
        page, max = data.get('page', 1), data.get('maxRecords', 20)
        if page < 1 or max < 0:
            raise InputError('Page and maxRecords must be positive integers')
        if max > 200:
            raise InputError('Max records must be less than or equal to 200')
        return jsonify(list_transactions(page, max))
    except Exception as e:
        return handle_error(e)
    
@app.route('/get_num_user_transactions', methods=['POST'])
def get_num_user_transactions():
    try:
        data = request.json
        reject_params(data, ['custID'])
        return jsonify(num_user_transactions(data['custID']))
    except Exception as e:
        return handle_error(e)
    
@app.route('/get_num_transactions', methods=['GET'])
def get_num_transactions():
    try:
        return jsonify(num_transactions())
    except Exception as e:
        return handle_error(e)

@app.route('/get_sub_info', methods=['POST'])
def get_sub_info():
    try:
        data = request.json
        reject_params(data, ['custID'])
        return jsonify(get_subscription_info(data['custID']))
    except Exception as e:
        return handle_error(e)
    
@app.route('/delete_customer', methods=['POST'])
def delete_cust():
    try:
        data = request.json
        reject_params(data, ['custID'])
        return jsonify(delete_customer(data['custID']))
    except Exception as e:
        return handle_error(e)
    
@app.route('/subscribe', methods=['POST'])
def create_sub():
    try:
        data = request.json
        reject_params(data, ['custID', 'planID'])
        return jsonify(subscribe_item(data['custID'], data['planID'], data.get('payment_method')))
    except Exception as e:
        return handle_error(e)
    
@app.route('/create_plan', methods=['POST'])
def create_plan():
    try:
        data = request.json
        reject_params(data, ['custType', 'price', 'trial_days', 'interval', 'name', 'description'])
        return jsonify(create_sub_plan(data['custType'], data['price'], data['trial_days'], data['interval'], data['name'], data['description']))
    except Exception as e:
        return handle_error(e)
    
@app.route('/update_plan', methods=['POST'])
def update_plan():
    try:
        data = request.json
        reject_params(data, ['planID'])
        return jsonify(update_sub_plan(data['planID'], data.get('price'), data.get('trial_days'), data.get('interval'), data.get('name'), data.get('description')))
    except Exception as e:
        return handle_error(e)
    
@app.route('/update_user_sub', methods=['POST'])
def update_user_subscription():
    try:
        data = request.json
        reject_params(data, ['custID'])
        return jsonify(update_user_sub(data['custID']))
    except Exception as e:
        return handle_error(e)

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.data
    sig_header = request.headers['STRIPE_SIGNATURE']
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_KEY
        )
    except ValueError as e:
        # Invalid payload
        handle_error(e)
        raise e
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        handle_error(e)
        raise e
    except Exception as e:
        handle_error(e)

    try:
        # Handle the event
        webhook_logger.warning('Received event: %s', event['type'])
        obj = event['data']['object']

        if event['type'] == 'charge.succeeded': # Called any time money is successfully transfered
            log_payment(event['created'], obj['customer'], obj['amount'], True, obj['description'])
        elif event['type'] == 'invoice.paid': # Called when an invoice is paid
            if obj['amount_due'] == 0:
                log_payment(event['created'], obj['customer'], 0, True, "Free trial created")
            else:
                update_pay_date(obj['customer'], event['created'])
            if obj['billing_reason'] == 'subscription_create':
                activate_license(obj['customer'], event['created'], obj['amount_due'] == 0)
        elif event['type'] == 'charge.failed': # Called any time a charge fails
            log_payment(event['created'], obj['customer'], obj['amount'], False, obj['description'])
        elif event['type'] == 'customer.subscription.deleted': # Called when a subscription is deleted
            deactivate_license(obj['customer'])
        elif event['type'] == 'customer.subscription.paused':
            deactivate_license(obj['customer'])
        elif event['type'] == 'customer.subscription.resumed':
            activate_license(obj['customer'], event['created'])
        elif event['type'] == 'charge.dispute.created': # Called when a customer creates a dispute
            handle_dispute(obj['id'], obj['amount'], obj['created'])
        elif event['type'] == 'customer.created':
            create_trial(obj['id'])
        elif event['type'] == 'customer.deleted':
            delete_cust_record(obj['id'])
            
    except Exception as e:
        handle_error(e)
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=4242)