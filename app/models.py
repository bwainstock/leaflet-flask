from app import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    feeds = db.relationship('Feed', backref='user', lazy='dynamic')
    markers = db.relationship('Marker', backref='user', lazy='dynamic')

    @staticmethod
    def make_unique_nickname(nickname):
        if User.query.filter_by(nickname=nickname).first() is None:
            return nickname
        version = 2
        while True:
            new_nickname = ''.join([nickname, str(version)])
            if User.query.filter_by(nickname=new_nickname).first() is None:
                break
            version += 1
        return new_nickname

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return unicode(self.id)
        except NameError:
            return str(self.id)

    def __repr__(self):
        return '<User {}>'.format(self.nickname)


class Feed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.String(33), index=True, unique=True)
    description = db.Column(db.String(40))
    active = db.Column(db.Boolean, unique=False, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    markers = db.relationship('Marker', backref='feed', lazy='dynamic')

    def newest_marker(self):
        return self.markers.order_by(Marker.unixtime.desc()).first()

    def __repr__(self):
        return '<Feed {}>'.format(self.spot_id)


class Marker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime)
    unixtime = db.Column(db.Integer)
    model_id = db.Column(db.String(10))
    message_type = db.Column(db.String(20))
    longitude = db.Column(db.Float)
    latitude = db.Column(db.Float)
    spot_id = db.Column(db.String(33), db.ForeignKey('feed.spot_id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Marker {}/{}, {}>'.format(
            self.longitude, self.latitude, self.user)