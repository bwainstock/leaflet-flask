from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from sqlalchemy.exc import IntegrityError

from app import app, db, lm, oid
from .forms import KeyForm, LoginForm, DateForm
from .models import User, Feed, Marker


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
        flash('Invalid login.  Please try again.', 'warning')
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
        try:
            db.session.commit()
        except IntegrityError:
            flash('Duplicate feed.  Please check SPOT ID.', 'danger')
            db.session.rollback()
        else:
            flash('Feed added!', 'success')
            data = get_spot_json(SPOT_URL.format(feed.spot_id))
            if data:
                db_write(data, feed)
                flash('Markers added!', 'success')
            else:
                flash('No markers found.', 'danger')
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
    flash('You have deleted SPOT ID {}'.format(spot_id), 'info')
    return redirect(url_for('index'))


@app.route('/feed/<spot_id>', methods=['GET', 'POST'])
# @login_required
def feed(spot_id):
    form = DateForm()
    feed = Feed.query.filter_by(spot_id=spot_id).first()
    if feed is None:
        flash('Feed not found.', 'warning')
        redirect(url_for('index'))
    if form.is_submitted():
        if not form.start.data:
            start = feed.oldest_marker.datetime
        else:
            start = form.start.data
        if not form.end.data:
            end = feed.newest_marker.datetime
        else:
            end = form.end.data
        changed = feed.toggle_markers_by_date(start, end)
        flash(changed)
        db.session.commit()
    markers = feed.markers.order_by(Marker.datetime.desc()).all()
    map_markers = feed.markers.filter(Marker.active==True).order_by(Marker.datetime.asc()).all()
    return render_template('feed.html', title='Feed {}'.format(feed.spot_id), feed=feed, markers=markers, map_markers=map_markers, form=form)


@app.route('/feed/<spot_id>/toggle')
@login_required
def toggle_feed_active(spot_id):
    feed = Feed.query.filter_by(spot_id=spot_id).first()
    feed.toggle_active()
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/feed/<spot_id>/activate_all')
@login_required
def activate_all(spot_id):
    feed = Feed.query.filter_by(spot_id=spot_id).first()
    if g.user.id == feed.user_id:
        feed.activate_all_markers()
        db.session.commit()
    else:
        flash('Only the feed owner can do that.', 'warning')
    return redirect(url_for('feed', spot_id=feed.spot_id))

@app.route('/feed/<spot_id>/deactivate_all')
@login_required
def deactivate_all(spot_id):
    feed = Feed.query.filter_by(spot_id=spot_id).first()
    if g.user.id == feed.user_id:
        feed.deactivate_all_markers()
        db.session.commit()
    else:
        flash('Only the feed owner can do that.', 'warning')
    return redirect(url_for('feed', spot_id=feed.spot_id))

@app.route('/marker/<int:id>/toggle')
@login_required
def toggle_marker_active(id):
    marker = Marker.query.get(id)
    if g.user.id == marker.user_id:
        marker.toggle_active()
        db.session.commit()
    else:
        flash('Only the feed owner can do that.', 'warning')
    return redirect(url_for('feed', spot_id=marker.spot_id))
