from wharf import app

from flask import Markup
from flask import render_template
from flask.ext.login import current_user

import redis

REDIS_HOST="localhost"
REDIS_PORT=6379

@app.route('/profile')
def profile():
    # redis list of ids
    # redis hash of running containers with ids that match lists
    # hash should have a 'owned_by' - this will allow sharing in the future

    r = redis.StrictRedis(host=REDIS_HOST, port=int(REDIS_PORT))
    row = ""
    for container in r.lrange(current_user.email, 0, -1):
        container_dict = r.hgetall(container)
        row += '<tr><td class="rowlink-skip"><a href="http://'+container+'">'+container+'</a></td><td>'+container_dict['service']+'</td><td>'+container_dict['owned_by']+'</td><td>'+container_dict['timestamp']+'</td></tr>'
    row = Markup(row)

    return render_template("profile.html", row=row)
