from wharf import app

from flask import Markup
from flask import redirect
from flask import render_template
from flask.ext.login import current_user

import datetime
import humanize
import redis
import time

@app.route('/profile')
def profile():
    if current_user.is_authenticated():
        # redis list of ids
        # redis hash of running containers with ids that match lists
        # hash should have a 'owned_by' - this will allow sharing in the future

        r = redis.StrictRedis(host=app.config['REDIS_HOST'], port=int(app.config['REDIS_PORT']))

        row = ""
        for container in r.lrange(current_user.email, 0, -1):
            print "foo:",container
            container_dict = r.hgetall(container)
            row += '<tr><td class="rowlink-skip"><a href="http://'+container+'">'+container+'</a></td><td>'+container_dict['service']+'</td><td>'+container_dict['container_id']+'</td><td>'+container_dict['owned_by']+'</td><td>'+humanize.naturaltime(datetime.timedelta(0, time.time()-float(container_dict['timestamp'])))+'</td><td><a href="/kill/'+container_dict['container_id']+'/'+container_dict['url']+'">Click to Terminate</a></td></tr>'
        row = Markup(row)

        return render_template("profile.html", row=row)
    else:
        return redirect("/")
