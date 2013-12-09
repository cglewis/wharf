from wharf import app

@app.route('/robot.txt')
def robot():
    return render_template("robot.html")
