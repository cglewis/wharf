from wharf import app

from flask import Markup
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from os import listdir
from os import path
from os import remove
from os import rmdir
from os import walk
from sh import git
from sh import mv
from werkzeug import secure_filename

import requests
import tarfile
import time
import zipfile

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in set(['gz', 'zip'])

def move_services(filename, num_ext):
    # move to services folder

    file_path = filename.rsplit('.', num_ext)[0]
    src_path = path.join(app.config['UPLOAD_FOLDER'], file_path, file_path)
    dest_path = app.config['SERVICES_FOLDER']

    i = 0
    while i != -1:
        try:
            src_path_i = path.join(app.config['UPLOAD_FOLDER'], file_path, file_path+str(i))
            src_path_ii = path.join(app.config['UPLOAD_FOLDER'], file_path, file_path+str(i-1))
            if i == 0:
                mv(src_path, dest_path)
            elif i == 1:
                mv(src_path, dest_path_i)
                mv(dest_path_i, dest_path)
            else:
                mv(dest_path_ii, dest_path_i)
                mv(dest_path_i, dest_path)
            i = -1
        except:
            i += 1

    # remove leftover files in tmp
    remove(path.join(app.config['UPLOAD_FOLDER'], filename))
    rmtree(path.join(app.config['UPLOAD_FOLDER'], file_path))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = ""
        file = ""
        desc = ""
        services = []
        try:
            url = request.form['wharf_url']
        except:
            url = ""
        try:
            file = request.files['file']
        except:
            file = ""
        if file != "":
            try:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    if filename.rsplit('.', 1)[1] == "zip":
                        with zipfile.ZipFile(file_path, 'r') as service_zip:
                            service_zip.extractall(path.join(app.config['UPLOAD_FOLDER'],
                                                             filename.rsplit('.', 1)[0]))
                            # !! TODO
                            #    allow exception for dockerfile, check at root as well
                            # check for existence of necessary files
                            missing_files = {}
                            for key,value in app.config['SERVICE_DICT'].items():
                                if not path.exists(path.join(app.config['UPLOAD_FOLDER'],
                                                             filename.rsplit('.', 1)[0],
                                                             filename.rsplit('.', 1)[0],
                                                             value)):
                                    missing_files[key] = value
                            services.append(filename.rsplit('.', 1)[0])
                            if missing_files:
                                if "dockerfile" in missing_files:
                                    return render_template("failed.html")
                                else:
                                    return render_template("forms.html",
                                                           services=services,
                                                           missing_files=missing_files,
                                                           filename=filename,
                                                           indexDesc=desc,
                                                           url=url)
                            move_services(filename, 1)

                    elif filename.rsplit('.', 1)[1] == "gz":
                        with tarfile.open(path.join(app.config['UPLOAD_FOLDER'], filename)) as service_gz:
                            service_gz.extractall(path.join(app.config['UPLOAD_FOLDER'],
                                                            filename.rsplit('.', 2)[0]))
                            # !! TODO
                            #    allow exception for dockerfile, check at root as well
                            # check for existence of necessary files
                            missing_files = {}
                            for key,value in app.config['SERVICE_DICT'].items():
                                if not path.exists(path.join(app.config['UPLOAD_FOLDER'],
                                                             filename.rsplit('.', 2)[0],
                                                             filename.rsplit('.', 2)[0],
                                                             value)):
                                    missing_files[key] = value
                            services.append(filename.rsplit('.', 2)[0])
                            if missing_files:
                                if "dockerfile" in missing_files:
                                    return render_template("failed.html")
                                else:
                                    return render_template("forms.html",
                                                           services=services,
                                                           missing_files=missing_files,
                                                           filename=filename,
                                                           indexDesc=desc,
                                                           url=url)
                            move_services(filename, 2)
                    else:
                        return render_template("failed.html")
                    # !! TODO
                    #    some post-processing once the file is uploaded
                else:
                    return render_template("failed.html")
            except:
                print "No file selected"
        elif url != "":
            try:
                if url:
                    url_path = (url.rsplit('/', 1)[1]).rsplit('.', 1)[0]
                    # !! TODO try/except
                    if url.rsplit('.', 1)[1] == "git":
                        # !! TODO try/except - if the folder already exists
                        git.clone(url, path.join(app.config['UPLOAD_FOLDER'],
                                                 url_path))

                        # check for dockerfile at root
                        # check for dockerfile assuming repo is the services folder
                        if path.exists(path.join(app.config['UPLOAD_FOLDER'],
                                                 url_path,
                                                 "Dockerfile")) or path.exists(path.join(app.config['UPLOAD_FOLDER'],
                                                 url_path,
                                                 app.config['SERVICE_DICT']['dockerfile'])):
                            # check for existence of necessary files
                            missing_files = {}
                            for key,value in app.config['SERVICE_DICT'].items():
                                if not path.exists(path.join(app.config['UPLOAD_FOLDER'],
                                                             url_path,
                                                             value)):
                                    missing_files[key] = value
                            services.append(url_path)
                            if "dockerfile" in missing_files:
                                del missing_files['dockerfile']
                            if missing_files:
                                return render_template("forms.html",
                                                       services=services,
                                                       missing_files=missing_files,
                                                       filename=file,
                                                       indexDesc=desc,
                                                       url=url)
                            # move to services folder
                            i = 0
                            while i != -1:
                                try:
                                    if i == 0:
                                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                                     url_path),
                                           app.config['SERVICES_FOLDER'])
                                    elif i == 1:
                                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                                     url_path),
                                           path.join(app.config['UPLOAD_FOLDER'],
                                                     url_path+str(i)))
                                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                                     url_path+str(i)),
                                           app.config['SERVICES_FOLDER'])
                                    else:
                                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                                     url_path+str(i-1)),
                                           path.join(app.config['UPLOAD_FOLDER'],
                                                     url_path+str(i)))
                                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                                     url_path+str(i)),
                                           app.config['SERVICES_FOLDER'])
                                    i = -1
                                except:
                                    i += 1
                            try:
                                # remove leftover files in tmp
                                rmdir(path.join(app.config['UPLOAD_FOLDER'],
                                                url_path))
                            except:
                                pass
                        else:
                            i = 0
                            repo_dirs = []
                            for root, dirs, files in walk(path.join(app.config['UPLOAD_FOLDER'],
                                                                    url_path)):
                                if i == 0:
                                    repo_dirs = dirs
                                i += 1
                            if ".git" in repo_dirs:
                                repo_dirs.remove(".git")
                            services=repo_dirs
                            for service_dir in repo_dirs:
                                # check for dockerfile one folder deep
                                # check for dockerfile in regular services folder
                                # could be more than one
                                if path.exists(path.join(app.config['UPLOAD_FOLDER'],
                                                         url_path,
                                                         service_dir, "Dockerfile")) or path.exists(path.join(app.config['UPLOAD_FOLDER'],
                                                           url_path,
                                                           service_dir, app.config['SERVICE_DICT']['dockerfile'])):
                                    # check for existence of necessary files
                                    missing_files = {}
                                    for key,value in app.config['SERVICE_DICT'].items():
                                        if not path.exists(path.join(app.config['UPLOAD_FOLDER'],
                                                                     url_path,
                                                                     service_dir,
                                                                     value)):
                                            missing_files[key] = value

                                    if "dockerfile" in missing_files:
                                        del missing_files['dockerfile']
                                    if missing_files:
                                        # !! TODO TODO TODO
                                        #    this needs to be re-worked for times 
                                        #    when there is more than one service_dir
                                        return render_template("forms.html",
                                                               services=services,
                                                               missing_files=missing_files,
                                                               filename=file,
                                                               indexDesc=desc,
                                                               url=url)
                                    # move to services folder
                                    i = 0
                                    while i != -1:
                                        try:
                                            if i == 0:
                                                mv(path.join(app.config['UPLOAD_FOLDER'],
                                                             url_path,
                                                             service_dir),
                                                   app.config['SERVICES_FOLDER'])
                                            elif i == 1:
                                                mv(path.join(app.config['UPLOAD_FOLDER'],
                                                             url_path,
                                                             service_dir),
                                                   path.join(app.config['UPLOAD_FOLDER'],
                                                             url_path,
                                                             service_dir+str(i)))
                                                mv(path.join(app.config['UPLOAD_FOLDER'],
                                                             url_path,
                                                             service_dir+str(i)),
                                                   app.config['SERVICES_FOLDER'])
                                            else:
                                                mv(path.join(app.config['UPLOAD_FOLDER'],
                                                             url_path,
                                                             service_dir+str(i-1)),
                                                   path.join(app.config['UPLOAD_FOLDER'],
                                                             url_path,
                                                             service_dir+str(i)))
                                                mv(path.join(app.config['UPLOAD_FOLDER'],
                                                             url_path,
                                                             service_dir+str(i)),
                                                   app.config['SERVICES_FOLDER'])
                                            i = -1
                                        except:
                                            i += 1
                            try:
                                rmdir(path.join(app.config['UPLOAD_FOLDER'],
                                                url_path))
                            except:
                                pass
                    else:
                        # !! TODO
                        #    should point to docker index url, expects a <meta name="description"
                        #    won't have a dockerfile in the service folder
                        #    note the naming scheme will mess with directory structure of service name
                        #    needs to be handled as a special case
                        repo = ""
                        desc = ""
                        try:
                            index_repo = (requests.get(url).content).split('<meta name="description" content="')
                            index_repo = index_repo[1].split("\" />")
                            # !! TODO try, if fails, there is no description.
                            try:
                                repo, desc = index_repo[0].split(": ", 1)
                                desc = desc.replace("\n", " ")
                                print repo, desc
                            except:
                                repo = index_repo[0]
                                print repo
                        except:
                            return render_template("failed.html")
                        if repo == "":
                            return render_template("failed.html")
                        missing_files = {}
                        for key,value in app.config['SERVICE_DICT'].items():
                            missing_files[key] = value
                        del missing_files["dockerfile"]
                        if desc != "":
                            del missing_files["description"]
                        services.append(repo)

                        return render_template("forms.html",
                                               services=services,
                                               missing_files=missing_files,
                                               filename=file,
                                               indexDesc=desc,
                                               url=url)
            except:
                print "Bad URL"
        else:
            return render_template("failed.html")
        return redirect(url_for('index'))

    row = ""
    services = [name for name in listdir("services") if path.isdir(path.join("services", name))]
    for service in services:
        last_modified = ""
        last_modified = time.ctime(path.getmtime("services/"+service))
        description = ""
        row += '<tr><td class="rowlink-skip"><a href="saas/'+service+'">'+service+'</a></td><td>'
        try:
            description_path = "services/"+service+"/"+app.config['SERVICE_DICT']['description']
            with open(description_path, 'r') as content_file:
                description = content_file.read()
            row += description
        except:
            row += "no description"
        row += '</td><td><a href="saas/'+service+'">'+last_modified+'</a></td><td><a href="edit/'+service+'">Edit</a></td></tr>'
    row = Markup(row)
    return render_template("index.html",row=row)
