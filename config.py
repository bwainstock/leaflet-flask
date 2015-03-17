import os
basedir = os.path.abspath(os.path.dirname(__file__))

WTF_CSRF_ENABLED = True
SECRET_KEY = 'thebigsupersecretpassword'

OPENID_PROVIDERS = [
    {'name': 'Google', 'url': 'https://www.google.com/accounts/o8/id'},
    {'name': 'Flickr', 'url': 'http://www.flickr.com/<username>'}]

SQLALCHEMY_DATABASE_URI = ''.join(['sqlite:///', os.path.join(basedir, 'app.db')])
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

POSTS_PER_PAGE = 3
