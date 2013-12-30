from wharf import app

from docker import client
from flask import redirect
from flask.ext.login import current_user

import redis

@app.route('/kill/<container_id>/<url>')
def kill(container_id, url):
    if current_user.is_authenticated():
        try:
            c = client.Client(version="1.6", base_url='http://%s:4243' % app.config['DOCKER_HOST'])
            c.kill(container_id)

            r = redis.StrictRedis(host=app.config['REDIS_HOST'], port=int(app.config['REDIS_PORT']))
            r.delete(url)
            r.lrem(current_user.email, 1, url)
        except:
            print "unable to kill",container_id
        
        return redirect("/profile")
    else:
        return redirect("/")
