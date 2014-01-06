from wharf import app

from flask import render_template

@app.route('/edit/<service>')
def edit(service):
    about = ""
    body = ""
    link = ""
    link_name = ""
    # !! TODO try/except
    about_path = "services/"+service+"/"+app.config['SERVICE_DICT']['about']
    with open(about_path, 'r') as content_file:
        about = content_file.read()
    body_path = "services/"+service+"/"+app.config['SERVICE_DICT']['body']
    with open(body_path, 'r') as content_file:
        body = content_file.read()
    link_path = "services/"+service+"/"+app.config['SERVICE_DICT']['link']
    with open(link_path, 'r') as content_file:
        link = content_file.read()
    link_a = link.split(" ", 1)
    link = link_a[0]
    link_name = link_a[1]
    return render_template("edit.html",service=service,about=about,body=body,link=link,link_name=link_name)
