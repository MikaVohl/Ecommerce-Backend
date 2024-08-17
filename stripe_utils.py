import stripe, time, os

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

def stripe_create_price(prodID, amount, interval, trial_days):
    return stripe.Price.create(
        unit_amount=amount, # in cents
        currency='usd',
        recurring={
            'interval': interval,
            "trial_period_days": trial_days,
        },
        product=prodID,
    )

def stripe_create_prod(name, desc):
    return stripe.Product.create(
        name=name,
        description=desc
    )

def stripe_list_subs(customerID):
    return stripe.Subscription.list(customer=customerID)

def stripe_create_sub(customerID, priceID, payment_method=None):
    # Cancel existing trialing subscriptions
    subscriptions = stripe.Subscription.list(customer=customerID, status='trialing')
    for sub in subscriptions.auto_paging_iter():
        sub.delete()

    if payment_method:
        p_methods = stripe_payment_methods(customerID)
        if p_methods is None or payment_method not in p_methods:
            stripe_assign_pmethod(customerID, payment_method)
    subscription = stripe.Subscription.create(
        customer=customerID,
        items=[{"price": priceID}],
        default_payment_method=payment_method,
        payment_settings={"save_default_payment_method": "on_subscription"},
    )

    return subscription

def stripe_create_trial(customerID, priceID, end_date=None): # Will create a trial that will not renew the subscription when it ends
    subscription = stripe.Subscription.create(
        customer=customerID,
        items=[{"price": priceID}],
        trial_settings={"end_behavior": {"missing_payment_method": "cancel"}},
        trial_end=int(end_date) if end_date > time.time() else None,
        cancel_at_period_end=True
    )
    return subscription

def stripe_assign_pmethod(stripeID, payID):
    pmethod = stripe.PaymentMethod.attach(
        payID,
        customer=stripeID
    )
    # set default
    stripe.Customer.modify(
        stripeID,
        invoice_settings={
            'default_payment_method': payID
        }
    )
    return pmethod
    
def stripe_remove_pmethod(payID):
    return stripe.PaymentMethod.detach(
        payID
    )

def stripe_payment_methods(customerID):
    payment_methods = stripe.PaymentMethod.list(
        type="card",
        customer=customerID,
    )
    if len(payment_methods['data']) == 0:
        return None
    return payment_methods['data']

def stripe_create_cust(name, ID, custType, email=None):
    if email:
        cust = stripe.Customer.create(
            name = name,
            email = email,
            metadata={
                'ID': ID,
                'custType': custType
            }
        )
    else:
        cust = stripe.Customer.create(
            name = name,
            metadata={
                'ID': ID,
                'custType': custType
            }
        )
    return cust

def stripe_cancel_sub(stripeID):
    subscriptions = stripe.Subscription.list(customer=stripeID)
    return stripe.Subscription.delete(subscriptions['data'][0]['id'])

def stripe_get_price(priceID):
    return stripe.Price.retrieve(priceID)

def stripe_get_prod(prodID):
    return stripe.Product.retrieve(prodID)

def stripe_get_dispute_cust(disputeID):
    chargeID = stripe.Dispute.retrieve(disputeID).charge
    return stripe.Charge.retrieve(chargeID).customer

def stripe_get_user_creation(stripeID):
    customer = stripe.Customer.retrieve(stripeID)
    if customer is None:
        return None
    return customer.created

def stripe_delete_cust(stripeID):
    return stripe.Customer.delete(stripeID)

def stripe_archive_price(priceID):
    return stripe.Price.modify(
    priceID,
    active=False,
    )

def stripe_archive_prod(prodID):
    return stripe.Product.modify(
    prodID,
    active=False,
    )

def stripe_charge(customerID, amount, desc, payment_method=None, save_card=None): 
    future_usage = 'off_session' if save_card else None
    payment_method_params = {'payment_method': payment_method} if payment_method else {'payment_method_types': ['card']}

    payment_intent = stripe.PaymentIntent.create(
        customer=customerID,
        amount=amount,
        currency='usd',
        description=desc,
        confirm=False,
        setup_future_usage=future_usage,
        automatic_payment_methods={
            'enabled': True if payment_method else False,
            'allow_redirects': 'never' if payment_method else None,
        },
        **payment_method_params,
    )
    return payment_intent

def stripe_invoice_success(invoiceID):
    pay_intent = stripe.PaymentIntent.retrieve(stripe.Invoice.retrieve(invoiceID).payment_intent)
    if pay_intent.status == 'succeeded':
        return True
    return False

def stripe_update_prod(prodID, name, desc):
    old_product = stripe.Product.retrieve(prodID)
    new_product_params = {
        "name": name if name is not None else old_product.name,
        "description": desc if desc is not None else old_product.description,
    }
    return stripe.Product.create(**new_product_params)

def stripe_update_price(priceID, prodID, amount, interval, trial_days):
    old_price = stripe.Price.retrieve(priceID)
    
    new_price_params = {
        "product": prodID if prodID is not None else old_price.product,
        "currency": old_price.currency,
        "recurring": {
            "interval": interval if interval is not None else old_price.recurring.interval,
            "trial_period_days": trial_days if trial_days is not None else old_price.recurring.trial_period_days,
        },
        "unit_amount": amount if amount is not None else old_price.unit_amount,
        "metadata": old_price.metadata,
    }    
    return stripe.Price.create(**new_price_params)

def stripe_change_sub(stripeCustID, old_priceID, new_priceID):
    subscriptions = stripe.Subscription.list(customer=stripeCustID, price=old_priceID)
    if not subscriptions:
        return None
    sub = subscriptions.data[0]
    sub_item = sub['items']['data'][0]
    return stripe.SubscriptionItem.modify(sub_item.id, price=new_priceID)