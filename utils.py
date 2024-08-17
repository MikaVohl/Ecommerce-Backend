from connection import svrconn
from stripe_utils import stripe_charge, stripe_create_cust, stripe_assign_pmethod, stripe_payment_methods, stripe_create_sub, stripe_invoice_success, \
    stripe_remove_pmethod, stripe_cancel_sub, stripe_create_trial, stripe_delete_cust, stripe_create_price, stripe_create_prod, stripe_update_prod, \
    stripe_update_price, stripe_archive_prod, stripe_archive_price, stripe_change_sub
import logging
from stripe.error import StripeError, CardError
import pyodbc

logger = logging.getLogger('stripe_api')
logger.setLevel(logging.WARNING)
handler = logging.FileHandler('exceptions.log', encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

INTERNAL_ERROR = 'Internal error. Please try again later or contact support if the problem persists'
CARD_ERROR = 'Error processing payment method. Please try a different card or contact support for more information'

UNKNOWN = ['call_issuer', 'do_not_honor', 'do_not_try_again', 'generic_decline', 'no_action_taken', 'revocation_of_all_authorizations', 'revocation_of_authorization', 'security_violation', 'service_not_allowed', 'stop_payment_order', 'transaction_not_allowed']
RETRY = ['reenter_transaction', 'try_again_later', 'approve_with_id', 'issuer_not_available']
INCORRECT = ['incorrect_number', 'incorrect_cvc', 'incorrect_zip', 'invalid_cvc', 'invalid_expiry_month', 'invalid_expiry_year', 'invalid_number']


def handle_error(e):
    if isinstance(e, StripeError):
        if isinstance(e, CardError):
            print(e.code, e.error.decline_code)
            msg = "Error processing your card. Please try again later or contact you bank for more information"
            code = e.error.decline_code
            if e.code == "card_declined": # Card declined # https://docs.stripe.com/declines/codes
                if code in UNKNOWN:
                    msg = "Error processing payment. Please contact your card issuer for more information"
                elif code in RETRY:
                    msg = "Error processing payment. Please try again later or contact your card issuer for more information"
                elif code == "card_not_supported":
                    msg = "Your card does not support this type of purchase. Please contact your card issuer for more information."
                elif code == "card_velocity_exceeded" or code == "withdrawal_count_limit_exceeded":
                    msg = "You have exceeded the balance, credit limit, or transaction amount limit available on your card. Please contact your card issuer for more information."
                elif code == "currency_not_supported":
                    msg = "Your card does not support the specified currency. Please contact your card issuer for more information."
                elif code == "duplicate_transaction":
                    msg = "A transaction with identical amount and credit card information was submitted very recently. Please check to see if a recent payment already exists."
                elif code == "fraudulent":
                    msg = "The payment was declined because it was suspected to be fraudulent. Please contact your card issuer for more information."
                elif code == "invalid_account" or code == "new_account_information_available":
                    msg = "The card, or account the card is connected to, is invalid. Please contact your card issuer to check that the card is working correctly."
                elif code == "invalid_amount":
                    msg = "The payment amount is invalid, or exceeds the amount that's allowed. If the amount appears to be correct, please check with your card issuer that you can make purchases of that amount."
                elif code == "lost_card" or code == "merchant_blacklist" or code == "stolen_card":
                    pass
                elif code == "not_permitted":
                    msg = "The payment is not permitted. Please contact your card issuer for more information."
                elif code == "pickup_card" or code == "restricted_card":
                    msg = "You can't use this card to make this payment (it's possible it was reported lost or stolen). Please contact your card issuer for more information."
                else:
                    msg = "Your card was declined. Please try a different card or contact your bank for more information."
            elif e.code == "expired_card":
                msg = "Your card has expired. Please use another card."
            elif e.code == "insufficient_funds":
                msg = "Your card has insufficient funds to complete the purchase. Please use an alternative payment method."
            elif e.code == "processing_error":
                msg = "There was an error processing your card. Please try again later."
            elif e.code in INCORRECT:
                msg = "Your card information is incorrect. Please check the information and try again."
            else:
                msg = "Error processing your card. Please try again later or contact you bank for more information"
            return {'error': {'message': msg, 'type': type(e).__name__}}
        
        else: # InvalidRequestError, APIConnectionError, APIError, AuthenticationError, IdempotencyError, RateLimitError, SignatureVerificationError
            logger.error('%s: %s', e.code, e)
            return {'error': {'message': INTERNAL_ERROR, 'type': type(e).__name__}}
    else: # Non-Stripe Error
        if isinstance(e, InputError): # Raised by programmer
            return {'error' : {'message': str(e), 'type': type(e).__name__}}
        elif isinstance(e, pyodbc.Error): # Database error
            print(e)
            logger.error('%s: %s', type(e).__name__, str(e))
            return {'error': {'message': INTERNAL_ERROR, 'type': type(e).__name__}}
        else: # Other error
            print(e)
            logger.error('%s: %s', type(e).__name__, str(e))
            return {'error' : {'message': INTERNAL_ERROR, 'type': type(e).__name__}}

def get_stripeID(ID, custType):
    conn = svrconn()
    with conn.cursor() as cursor:
        cursor.execute('SELECT stripeCustID FROM Customers WHERE custType = ? and linkedID = ?', [custType, ID])
        result = cursor.fetchone()
        if result is None:
            raise InputError('No customer found with that ID and type')
        return result[0]
    
def get_stripeID(custID):
    conn = svrconn()
    with conn.cursor() as cursor:
        cursor.execute('SELECT stripeCustID FROM Customers WHERE custID = ?', custID)
        result = cursor.fetchone()
        if result is None:
            raise InputError('No customer found with that ID')
        return result[0]  

def get_custID(stripeID): 
    conn = svrconn()
    with conn.cursor() as cursor:
        cursor.execute('SELECT custID FROM Customers WHERE stripeCustID = ?', stripeID)
        result = cursor.fetchone()
        if result is None:
            raise InputError('No customer found with that ID')
        return result[0]

def assign_payment_method(custID, payID):
    stripeID = get_stripeID(custID)
    return stripe_assign_pmethod(stripeID, payID)

def delete_payment_method(payID):
    return stripe_remove_pmethod(payID)

def create_cust(ID, custType, email=None):
    custType = int(custType)
    conn = svrconn()
    with conn.cursor() as cursor:
        if custType == 1:
            raise InputError('Invalid customer type...For now')
        elif custType == 2:
            cursor.execute('SELECT practiceName FROM [Practices] WHERE practiceID = ?', ID)
        elif custType == 3:
            cursor.execute('SELECT locName FROM [Practices.Locations] WHERE locID = ?', ID)
        elif custType == 4:
            cursor.execute('SELECT tFirstName, tLastName FROM [Therapists.SearchResults] WHERE tID = ?', ID)
        else:
            raise InputError('Invalid customer type')
        name = cursor.fetchone()
        if name is None:
            raise InputError('No customer found with that ID and type')
        name = ' '.join(name)
        cursor.execute('SELECT * FROM Customers WHERE custType = ? and linkedID = ?', [custType, ID])
        if cursor.fetchone() is not None:
            raise InputError('Customer already exists')
        cust = stripe_create_cust(name, ID, custType, email)
        try:
            query = 'INSERT INTO Customers (stripeCustID, custType, linkedID, subscriptDate, lastPayDate, status) VALUES (?, ?, ?, ?, ?, ?)'
            cursor.execute(query, [cust.id, custType, ID, None, None, 0])
            conn.commit()
        except Exception as e:
            logger.error('Failed operation: '+query+' with values: '+str([cust.id, custType, ID, None, None, 0]))
        return cust.id

def list_customers():
    conn = svrconn()
    with conn.cursor() as cursor:
        cursor.execute('SELECT custID, custType, linkedID, COALESCE(p.practiceName, l.locName, t.tFirstName + \' \' + t.tLastName) as name FROM Customers c LEFT JOIN Practices p ON c.linkedID = p.practiceID AND c.custType = 2 LEFT JOIN [Practices.Locations] l ON c.linkedID = l.locID AND c.custType = 3 LEFT JOIN [Therapists.SearchResults] t ON c.linkedID = t.tID AND c.custType = 4 ORDER BY custID')
        rows = cursor.fetchall()
        customers = [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
        return customers
    
def list_payment_methods(custID):
    pay_methods = stripe_payment_methods(get_stripeID(custID))
    if pay_methods is None:
        return []
    return pay_methods

def get_item(planID):
    conn = svrconn()
    with conn.cursor() as cursor:
        cursor.execute('SELECT name, custType, amount, description, interval, trialDays FROM Plans WHERE planID = ?', planID)
        result = cursor.fetchone()
    if result is None:
        return None
    return {
        'name': result[0],
        'custType': result[1],
        'price': result[2],
        'description': result[3],
        'recurring': result[4],
        'trialDays': result[5]
    }

def subscribe_item(custID, planID, pay_method=None):
    stripeID = get_stripeID(custID)
    if get_subscription_status(custID) == 1:
        raise InputError('User has an existing subscription')
    conn = svrconn()
    with conn.cursor() as cursor:
        cursor.execute('SELECT priceID FROM Plans WHERE planID = ?', planID)
        result = cursor.fetchone()
        if result is None:
            raise InputError('Plan ID does not exist')
        priceID = result[0]
        subscription = stripe_create_sub(stripeID, priceID, pay_method)
        cursor.execute('UPDATE Customers SET planID = ? WHERE custID = ?', [planID, custID])
    if stripe_invoice_success(subscription.latest_invoice):
        return subscription
    else:
        raise InputError(CARD_ERROR)

def get_signup_date(custID):
    conn = svrconn()
    with conn.cursor() as cursor:
        cursor.execute('SELECT custType, linkedID FROM Customers WHERE custID = ?', custID)
        result = cursor.fetchone()
        if result is None:
            raise InputError('No customer found with that ID')
        custType = result[0]
        linkedID = result[1]
        if custType == 1:
            cursor.execute('SELECT uCreatedDate FROM Users WHERE uID = ?', linkedID)
        elif custType == 2:
            cursor.execute('SELECT pracUCreated FROM [Practices.Users] WHERE pracPracticeID = ?', linkedID)
        elif custType == 3:
            raise InputError('Invalid customer type...For now')
        elif custType == 4:
            cursor.execute('SELECT tCreatedDate FROM tUsers WHERE tTherapistID = ?', linkedID)
        date = cursor.fetchone()
        if date is None:
            return None
        return date[0]
    
def create_charge(customerID, amount, desc, pay_method=None, save_card=None):
    return stripe_charge(get_stripeID(customerID), amount, desc, pay_method, save_card).client_secret

def activate_license(stripeID, timestamp, trial=False):
    conn = svrconn()
    with conn.cursor() as cursor:
        cursor.execute('UPDATE Customers SET status = ? WHERE stripeCustID = ?', [2 if trial else 1, stripeID])
        if cursor.rowcount == 0:
            logger.error('Failed to activate license: No customer found with ID %s. Failed query is: UPDATE Customers SET status = 1 WHERE stripeCustID = %s', stripeID, stripeID)
            raise InputError('No customer found with that ID')
        cursor.execute("UPDATE Customers SET subscriptDate = DATEADD(SECOND, ?,'1970-01-01 00:00:00') WHERE stripeCustID = ?", [timestamp, stripeID])
    conn.commit()
    return { 'status': 'success' }

def deactivate_license(stripeID):
    conn = svrconn()
    with conn.cursor() as cursor:
        cursor.execute('UPDATE Customers SET status = 0 WHERE stripeCustID = ?', stripeID)
        if cursor.rowcount == 0:
            logger.error('Failed to deactivate license: No customer found with ID %s. Failed query is: UPDATE Customers SET status = 0 WHERE stripeCustID = %s', stripeID, stripeID)
            raise InputError('No customer found with that ID')
    conn.commit()
    return { 'status': 'success' }

def log_payment(timestamp, stripeID, amount, success, description=None):
    custID = get_custID(stripeID)
    if custID is None:
        logger.error('Failed to log payment: No customer found with ID %s. Unlogged amount is %s at timestamp %s. ', stripeID, amount, timestamp, description)
        raise InputError('No customer found with that ID')
    conn = svrconn()
    with conn.cursor() as cursor:
        cursor.execute("INSERT INTO Transactions (traTimestamp, traAmount, traCustID, traDesc, traSuccess) VALUES (DATEADD(SECOND, ?,'1970-01-01 00:00:00'), ?, ?, ?, ?)", (timestamp, amount/100, custID, description, success))
    conn.commit()
    return { 'status': 'success' }

def get_checkout_links(custType):
    conn = svrconn()
    with conn.cursor() as cursor:
        if custType is None:
            cursor.execute('SELECT * FROM Plans where active = 1 ORDER BY interval desc')
        else:
            cursor.execute('SELECT * FROM Plans where active = 1 and custType = ? ORDER BY interval desc', custType)
        columns = [column[0] for column in cursor.description]
        plans = [dict(zip(columns, row)) for row in cursor.fetchall()]
    return plans

def handle_dispute(disputeID, amount, timestamp): # ===== UNFINISHED =====
    pass

def create_trial(stripeID):
    custID = get_custID(stripeID)
    signup = get_signup_date(custID)
    conn = svrconn()
    with conn.cursor() as cursor:
        cursor.execute("SELECT TOP(1) custType FROM Customers WHERE custID = ?", custID)
        custType = cursor.fetchone()[0]

        cursor.execute("SELECT TOP(1) trialDays, priceID FROM Plans WHERE custType = ? AND active = 1 ORDER BY amount", custType)
        trial_days, priceID = cursor.fetchone()
        
        if signup is None or trial_days is None:
            return { 'status': 'failed', 'message': 'Invalid trial length' }
        return stripe_create_trial(stripeID, priceID, int(signup.timestamp() + trial_days * 86400))

def unsubscribe(custID):
    stripeID = get_stripeID(custID)
    return stripe_cancel_sub(stripeID)

def get_subscription_status(custID):
    conn = svrconn()
    with conn.cursor() as cursor:
        cursor.execute('SELECT status FROM Customers WHERE custID = ?', custID)
        result = cursor.fetchone()
        if result is None:
            raise InputError('No customer found with that ID')
        return result[0]
    
def get_subscription_info(custID):
    conn = svrconn()
    with conn.cursor() as cursor:
        cursor.execute('SELECT status, subscriptDate, lastPayDate FROM Customers WHERE custID = ?', custID)
        result = cursor.fetchone()
        if result is None:
            raise InputError('No customer found with that ID')
        return result
    
def list_user_transactions(custID, page, maxRecords):
    conn = svrconn()
    with conn.cursor() as cursor:
        offset = (page - 1) * maxRecords
        cursor.execute(f'SELECT traID, traTimestamp, traAmount, traDesc FROM Transactions WHERE traCustID = ? ORDER BY traTimestamp DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY', [custID, offset, maxRecords])
        rows = cursor.fetchall()
        transactions = [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
        return transactions
    
def list_transactions(page, maxRecords):
    conn = svrconn()
    with conn.cursor() as cursor:
        offset = (page - 1) * maxRecords
        cursor.execute(f'SELECT traID, traTimestamp, traAmount, traDesc, traSuccess, c.custID, c.custType, c.linkedID, COALESCE(p.practiceName, l.locName, tr.tFirstName \
                       + \' \' + tr.tLastName) as name FROM Transactions t JOIN Customers c ON t.traCustID = c.custID LEFT JOIN Practices p ON c.linkedID = p.practiceID \
                       AND c.custType = 2 LEFT JOIN [Practices.Locations] l ON c.linkedID = l.locID AND c.custType = 3 LEFT JOIN [Therapists.SearchResults] tr ON \
                       c.linkedID = tr.tID AND c.custType = 4 ORDER BY traTimestamp DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY', [offset, maxRecords])
        rows = cursor.fetchall()
        transactions = [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
        return transactions
    
def num_user_transactions(custID):
    conn = svrconn()
    with conn.cursor() as cursor:
        cursor.execute('SELECT COUNT(traID) FROM Transactions WHERE traCustID = ?', custID)
        result = cursor.fetchone()
        if result is None:
            return 0
        return result[0]

def num_transactions():
    conn = svrconn()
    with conn.cursor() as cursor:
        cursor.execute('SELECT COUNT(traID) FROM Transactions')
        result = cursor.fetchone()
        if result is None:
            return 0
        return result[0]

def update_pay_date(stripeID, timestamp):
    conn = svrconn()
    with conn.cursor() as cursor:
        cursor.execute("UPDATE Customers SET lastPayDate = DATEADD(SECOND, ?,'1970-01-01 00:00:00') WHERE stripeCustID = ?", [timestamp, stripeID])
    conn.commit()
    return { 'status': 'success' }

def delete_customer(custID):
    return stripe_delete_cust(get_stripeID(custID))

def delete_cust_record(stripeID):
    conn = svrconn()
    with conn.cursor() as cursor:
        cursor.execute('DELETE FROM Customers WHERE custID = ?', get_custID(stripeID))
    conn.commit()
    return { 'status': 'success' }

def create_sub_plan(custType, amount, trial_days, interval, name, description):
    product = stripe_create_prod(name, description)
    price = stripe_create_price(product.id, int(round(amount * 100)), interval, trial_days)
    conn = svrconn()
    with conn.cursor() as cursor:
        cursor.execute("SELECT MAX(planHistoryNum) FROM Plans")
        result = cursor.fetchone()
        if result is None:
            max_plan_history_num = 0  # If there are no plans, start with 0
        else:
            max_plan_history_num = result[0]
        max_plan_history_num += 1
        cursor.execute("INSERT INTO Plans (name, amount, priceID, productID, description, interval, trialDays, custType, active, planHistoryNum, created) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, DATEADD(SECOND, ?,'1970-01-01 00:00'))", [name, amount, price.id, product.id, description, interval, trial_days, custType, 1, max_plan_history_num, price.created])
        conn.commit()
    product.default_price = price.id
    return price

def update_sub_plan(planID, new_amount, new_trial_days, new_interval, new_name, new_desc):
    conn = svrconn()
    new_prod, created = None, None
    with conn.cursor() as cursor:
        cursor.execute('SELECT productID, priceID, planHistoryNum, custType, name, amount, description, interval, trialDays, active FROM Plans WHERE planID = ?', planID)
        result = cursor.fetchone()
        if result is None:
            raise InputError('No plan found with that ID')
        productID, priceID, history_num, custType, old_name, old_amount, old_desc, old_interval, old_trial_days, active = result
        if active == 0:
            raise InputError('Cannot update inactive plan')
        if new_name is not None or new_desc is not None:
            new_prod = stripe_update_prod(productID, new_name, new_desc)
            name, desc, productID = new_prod.name, new_prod.description, new_prod.id
            created = new_prod.created
        else:
            name, desc = old_name, old_desc

        if new_amount is not None or new_trial_days is not None or new_interval is not None:
            new_price = stripe_update_price(priceID, new_prod, new_amount * 100, new_interval, new_trial_days)
            amount, interval, trial, priceID = new_price.unit_amount / 100, new_price.recurring.interval, new_price.recurring.trial_period_days, new_price.id
            created = new_price.created
        else:
            amount, interval, trial = old_amount, old_interval, old_trial_days
        
        if created is None:
            raise InputError('No changes to plan')
        
        values = [custType, name, amount, priceID, productID, desc, interval, trial, created, 1, history_num]
        cursor.execute("INSERT INTO Plans (custType, name, amount, priceID, productID, description, interval, trialDays, created, active, planHistoryNum) VALUES (?, ?, ?, ?, ?, ?, ?, ?, DATEADD(SECOND, ?, '1970-01-01 00:00'), ?, ?)", values)
        conn.commit()
        archive_sub_plan(planID, new_prod is not None, new_price is not None)
    return { 'status': 'success' }

def archive_sub_plan(planID, archive_prod, archive_price):
    conn = svrconn()
    with conn.cursor() as cursor:
        cursor.execute('SELECT productID, priceID FROM Plans WHERE planID = ?', planID)
        result = cursor.fetchone()
        if result is None:
            raise InputError('No plan found with that ID')
        productID, priceID = result
        cursor.execute('UPDATE Plans SET active = 0 WHERE planID = ?', planID)
        conn.commit()
    if archive_prod:
        stripe_archive_prod(productID)
    if archive_price:
        stripe_archive_price(priceID)
    return { 'status': 'success' }

def update_user_sub(custID):
    conn = svrconn()
    with conn.cursor() as cursor:
        cursor.execute('SELECT planID FROM Customers WHERE custID = ?', custID)
        result = cursor.fetchone()
        if result is None:
            raise InputError('No plan found for customer')
        old_planID = result[0]
        cursor.execute('SELECT priceID, planHistoryNum FROM Plans WHERE planID = ?', old_planID)
        old_priceID, history_num = cursor.fetchone()
        cursor.execute('SELECT priceID, planID FROM Plans WHERE planHistoryNum = ? and active = 1', history_num)
        new_priceID, new_planID = cursor.fetchone()
        if stripe_change_sub(get_stripeID(custID), old_priceID, new_priceID) is None:
            raise InputError('No subscription found with given priceID')
        cursor.execute('UPDATE Customers SET planID = ? WHERE custID = ?', [new_planID, custID])
    conn.commit()
    return { 'status': 'success' }

class InputError(Exception):
    pass