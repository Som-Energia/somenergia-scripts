from datetime import datetime as dt
from dateutil.relativedelta import relativedelta


def customer_email_in_erp(conversation, erp_emails):
    if not conversation:
        return False

    from_customer = conversation.get('primaryCustomer', {}).get('email', '') in erp_emails
    cc_customer = (conversation['cc'] and conversation['cc'][0] or '') in erp_emails
    bcc_customer = (conversation['bcc'] and conversation['bcc'][0] or '') in erp_emails
    to_email = conversation['_embedded'].get('threads', [{}])[-1].get('to', [''])
    to_customer = (to_email and to_email[0] or '') in erp_emails

    return from_customer or to_customer or cc_customer or bcc_customer


def newer_than_4y(email_creation):
    if not email_creation:
        return False

    email_creation_datetime = dt.strptime(email_creation, '%Y-%m-%dT%H:%M:%SZ')
    four_yrs_ago = dt.now() - relativedelta(years=4)
    return email_creation_datetime > four_yrs_ago
