from flask import render_template, flash, redirect, session, url_for, request, g, jsonify
from flask.ext.login import login_user, logout_user, current_user, login_required
from sqlalchemy.exc import IntegrityError

from app import app, db, lm, oid
from .forms import KeyForm, LoginForm, DateForm, RegistrationForm
from .models import User, Feed, Marker, bg_router

from datetime import datetime

import spot_api_scraper


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.before_request
def before_request():
    g.user = current_user


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, username=form.username.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('You\'ve successfully registered {}'.format(form.username.data))
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.verify_password(form.password.data):
            flash('Invalid username or password', 'warning')
            return redirect(url_for('login'))
        login_user(user)
        flash('{} is now logged in.'.format(user.username))
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


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
            data = spot_api_scraper.get_spot_json(spot_api_scraper.SPOT_URL.format(feed.spot_id))
            if data:
                spot_api_scraper.db_write(data, feed)
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
    if feed is None:
        flash('Feed not found.')
        redirect(url_for('index'))
    db.session.delete(feed)
    db.session.commit()
    flash('You have deleted SPOT ID {}'.format(spot_id), 'info')
    return redirect(url_for('index'))


@app.route('/feed/<spot_id>', methods=['GET', 'POST'])
@login_required
def feed(spot_id):
    form = DateForm()
    feed = Feed.query.filter_by(spot_id=spot_id).first()
    if feed is None:
        flash('Feed not found.', 'warning')
        return redirect(url_for('index'))
    if form.is_submitted():
        if not form.start.data:
            start = feed.oldest_marker.datetime
        else:
            start = form.start.data
        if not form.end.data:
            end = feed.newest_marker.datetime
        else:
            end = form.end.data
        feed.toggle_markers_by_date(start, end)
        db.session.commit()
    markers = feed.markers.order_by(Marker.datetime.desc()).all()
    map_markers = feed.markers.filter(Marker.active == True).order_by(Marker.datetime.asc()).all()
    return render_template('feed.html',
                           title='Feed {}'.format(feed.spot_id),
                           feed=feed,
                           # start=start,
                           # end=end,
                           markers=markers,
                           map_markers=map_markers,
                           form=form)


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


@app.route('/feed/<spot_id>/route_active', methods=['POST'])
@login_required
def route_active(spot_id):
    feed = Feed.query.filter_by(spot_id=spot_id).first()
    route = feed.route_active_markers()

    return jsonify({'route id': route.id}), 202, {'Location': url_for('routestatus', route_id=route.id)}


@app.route('/feed/route_status/<route_id>')
def routestatus(route_id):
    route = bg_router.AsyncResult(route_id)

    if route.state == 'PENDING':
        response = {
            'state': route.state,
            'status': 'Pending...'
        }
    elif route.state != 'FAILURE':
        response = {
            'state': route.state,
        }
        if 'result' in route.info:
            response['result'] = route.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': route.state,
            'status': str(route.info),  # this is the exception raised
        }
    return jsonify(response)


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
