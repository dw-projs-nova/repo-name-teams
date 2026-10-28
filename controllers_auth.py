from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from hashlib import sha256
from secrets import token_urlsafe
from smtplib import SMTPException

from flask import (
    abort,
    current_app,
    g,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from controllers_mail import send_smtp_message
from controllers_shared import main, require_login
from models import LoginToken, Review, User, db


def login_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='review-login')


def token_hash(token):
    return sha256(token.encode('utf-8')).hexdigest()


def send_login_email(user):
    nonce = token_urlsafe(32)
    token = login_serializer().dumps({'user_id': user.id, 'nonce': nonce})
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=30)
    db.session.add(LoginToken(
        token_hash=token_hash(token),
        user_id=user.id,
        expires_at=expires_at,
    ))
    db.session.commit()
    login_url = url_for('main.verify_login', token=token, _external=True)

    message = EmailMessage()
    message['Subject'] = 'Sign in to Review App'
    message['From'] = current_app.config['SMTP_FROM']
    message['To'] = user.email
    message.set_content(
        f"Sign in to Review App using this link:\n\n{login_url}\n\n"
        "This link expires after 30 minutes.\n"
        "If you did not request this email, you can safely ignore it."
    )
    message.add_alternative(
        render_template('mail/login_email.html', login_url=login_url),
        subtype='html',
    )
    send_smtp_message(message)


@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        next_url = request.form.get('next')
        if next_url and next_url.startswith('/'):
            session['login_next'] = next_url
        email = request.form.get('email', '').strip().lower()
        if '@' not in email or len(email) > 320:
            return render_template('account/login.html', error='Enter a valid email address.'), 400

        user = User.query.filter_by(email=email).first()
        expected_role = 'admin' if email == current_app.config['ADMIN_EMAIL'] else 'user'
        if user is None:
            user = User(email=email, display_name=email.split('@', 1)[0], role=expected_role)
            db.session.add(user)
            db.session.commit()
        elif user.role != expected_role:
            user.role = expected_role
            db.session.commit()
        try:
            send_login_email(user)
        except (OSError, SMTPException) as exc:
            current_app.logger.exception('Could not send sign-in email')
            return render_template('account/login.html', error=f'Could not send email: {exc}'), 502
        return render_template('account/login.html', message='Check your email for a secure sign-in link.')
    return render_template('account/login.html')


def load_login_token(token):
    try:
        data = login_serializer().loads(token, max_age=30 * 60)
        nonce = data['nonce']
        user_id = data['user_id']
        record = db.session.get(LoginToken, token_hash(token))
    except (BadSignature, SignatureExpired, KeyError, TypeError):
        abort(400)

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if (
        not nonce
        or record is None
        or record.user_id != user_id
        or record.used_at is not None
        or record.expires_at <= now
    ):
        abort(400)
    user = db.session.get(User, user_id)
    if user is None:
        abort(400)
    return record, user


@main.route('/login/verify/<token>', methods=['GET', 'POST'])
def verify_login(token):
    record, user = load_login_token(token)
    if request.method == 'GET':
        response = make_response(render_template('account/verify_login.html'))
        response.headers['Cache-Control'] = 'no-store'
        return response

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    consumed = LoginToken.query.filter(
        LoginToken.token_hash == record.token_hash,
        LoginToken.used_at.is_(None),
        LoginToken.expires_at > now,
    ).update({LoginToken.used_at: now}, synchronize_session=False)
    if consumed != 1:
        db.session.rollback()
        abort(400)

    next_url = session.pop('login_next', None)
    session.clear()
    session['user_id'] = user.id
    db.session.commit()
    return redirect(next_url or url_for('main.account'))


@main.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('main.index'))


@main.route('/account', methods=['GET', 'POST'])
def account():
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    message = None
    if request.method == 'POST':
        display_name = request.form.get('display_name', '').strip()
        if not display_name or len(display_name) > 120:
            return render_template(
                'account/profile.html',
                reviews=g.current_user.reviews.order_by(Review.created_at.desc()).all(),
                error='Display name is required and must be 120 characters or fewer.',
            ), 400
        g.current_user.display_name = display_name
        for review in g.current_user.reviews:
            review.reviewer_name = display_name
        db.session.commit()
        message = 'Profile updated.'

    reviews = g.current_user.reviews.order_by(Review.created_at.desc()).all()
    return render_template('account/profile.html', reviews=reviews, message=message)
