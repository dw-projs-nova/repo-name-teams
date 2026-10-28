from email.message import EmailMessage
from smtplib import SMTP, SMTP_SSL

from flask import current_app, render_template, url_for

from controllers_shared import get_product


def send_smtp_message(message):
    smtp_class = SMTP_SSL if current_app.config['SMTP_USE_SSL'] else SMTP
    with smtp_class(
        current_app.config['SMTP_HOST'],
        current_app.config['SMTP_PORT'],
        timeout=15,
    ) as smtp:
        if current_app.config['SMTP_STARTTLS']:
            smtp.starttls()
        if current_app.config['SMTP_USERNAME']:
            smtp.login(
                current_app.config['SMTP_USERNAME'],
                current_app.config['SMTP_PASSWORD'] or '',
            )
        smtp.send_message(message)


def send_review_approved_email(review):
    if review.author is None:
        return

    review_url = url_for(
        'main.product',
        product_id=review.product_id,
        _external=True,
        _anchor=f'review-{review.id}',
    )
    product = get_product(review.product_id)
    message = EmailMessage()
    message['Subject'] = f"Your review of {product['name']} was approved"
    message['From'] = current_app.config['SMTP_FROM']
    message['To'] = review.author.email
    message.set_content(
        f"Your review, \"{review.title}\", was approved and is now public.\n\n"
        f"View your review: {review_url}\n\n"
        "Thank you for sharing your feedback."
    )
    message.add_alternative(
        render_template(
            'mail/review_approved.html',
            product=product,
            review=review,
            review_url=review_url,
        ),
        subtype='html',
    )
    send_smtp_message(message)
