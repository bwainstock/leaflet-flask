from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, oid
from .forms import KeyForm, LoginForm
from .models import User, Feed
from spot_api_scraper import SPOT_URL, get_spot_json, db_write


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.before_request
def before_request():
    g.user = current_user


@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        return oid.try_login(form.openid.data, ask_for=['nickname', 'email'])
    return render_template('login.html',
                           title='Sign In',
                           form=form,
                           providers=app.config['OPENID_PROVIDERS'])


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@oid.after_login
def after_login(resp):
    if resp.email is None or resp.email == "":
        flash('Invalid login.  Please try again.')
        return redirect(url_for('login'))
    user = User.query.filter_by(email=resp.email).first()
    if user is None:
        nickname = resp.nickname
        if nickname is None or nickname == "":
            nickname = resp.email.split('@')[0]
        nickname = User.make_unique_nickname(nickname)
        user = User(nickname=nickname, email=resp.email)
        db.session.add(user)
        db.session.commit()
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(user, remember=remember_me)
    return redirect(request.args.get('next') or url_for('index'))


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = KeyForm()
    if form.validate_on_submit():
        feed = Feed(spot_id=form.spot_id.data, description=form.description.data, user=g.user)
        db.session.add(feed)
        db.session.commit()
        flash('Feed added!')
        data = get_spot_json(SPOT_URL.format(feed.spot_id))
        if data:
            db_write(data, feed)
            flash('Markers added!')
        else:
            flash('No markers found.')
        return redirect(url_for('index'))
    feeds = g.user.feeds.all()
    return render_template('index.html', title='Home', form=form, feeds=feeds)


@app.route('/delete/<spot_id>')
@login_required
def delete(spot_id):
    feed = Feed.query.filter_by(spot_id=spot_id).first()
    markers = feed.markers.all()
    for marker in markers:
        db.session.delete(marker)
    if feed is None:
        flash('Feed not found.')
        redirect(url_for('index'))
    db.session.delete(feed)
    db.session.commit()
    flash('You have deleted SPOT ID {}'.format(spot_id))
    return redirect(url_for('index'))


@app.route('/feed/<spot_id>')
@login_required
def feed(spot_id):
    feed = Feed.query.filter_by(spot_id=spot_id).first()
    if feed is None:
        flash('Feed not found.')
        redirect(url_for('index'))
    return render_template('feed.html', title='Feed {}'.format(feed.spot_id), feed=feed)