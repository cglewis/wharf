from wharf import app

from flask import render_template

@app.route('/robot.txt')
def robot():
    return render_template("robot.html")
