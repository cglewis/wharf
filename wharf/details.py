from wharf import app

from flask import render_template

@app.route('/details/<service>/<url>')
def details(url, service):
    # !! TODO try/except
    client = ""
    test = ""
    link = ""
    link_name = ""
    link_path = "services/"+service+"/"+app.config['SERVICE_DICT']['link']
    with open(link_path, 'r') as content_file:
        link = content_file.read()
    link_a = link.split(" ", 1)
    link = link_a[0]
    link_name = link_a[1]
    client_path = "services/"+service+"/"+app.config['SERVICE_DICT']['client']
    with open(client_path, 'r') as content_file:
        client = content_file.read()
    client_a = client.split("\n")
    client = client_a[0]
    test_path = "services/"+service+"/client/"+client_a[1]
    with open(test_path, 'r') as content_file:
        test = content_file.read()
    return render_template("details.html",
                           url=url,
                           service=service,
                           client=client,
                           test=test,
                           link=link,
                           link_name=link_name)
