from app import db
from app.models import User, Feed, Marker

from datetime import datetime
import requests
from time import sleep


SPOT_URL = 'https://api.findmespot.com/spot-main-web/consumer/rest-api/2.0/public/feed/{}/message.json'


def get_spot_json(spot_url):
    response = requests.get(spot_url)
    if 'feedMessageResponse' in response.json()['response']:
        return response.json()['response']['feedMessageResponse']['messages']['message']
    return False


def db_write(data, feed):
    latest_marker = feed.newest_marker()
    if latest_marker:
        maxtime = latest_marker.unixtime
    else:
        maxtime = 0
    for point in data:
        dateinfo = datetime.strptime(point['dateTime'], '%Y-%m-%dT%H:%M:%S%z')
        unixtime = point['unixTime']
        model_id = point['modelId']
        message_type = point['messageType']
        longitude = point['longitude']
        latitude = point['latitude']
        spot_id = feed.spot_id
        user_id = feed.user_id

        if unixtime > maxtime:
            marker = Marker(datetime=dateinfo,
                            unixtime=unixtime,
                            model_id=model_id,
                            message_type=message_type,
                            longitude=longitude,
                            latitude=latitude,
                            spot_id=spot_id,
                            user_id=user_id)
            db.session.add(marker)
            print(marker)

    db.session.commit()

def main():
    feeds = Feed.query.all()
    for feed in feeds:
        data = get_spot_json(SPOT_URL.format(feed.spot_id))
        print(data)
        if data:
            db_write(data, feed)
        sleep(2)

if __name__ == '__main__':
    main()
