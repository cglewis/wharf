from wharf import app

from flask import Markup
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug import secure_filename

from sh import git
from sh import mv

from os import listdir
from os import path
from os import remove
from os import rmdir
from os import walk

import requests
import tarfile
import time
import zipfile

ALLOWED_EXTENSIONS = set(['gz', 'zip'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

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
                    file.save(path.join(app.config['UPLOAD_FOLDER'], filename))
                    if filename.rsplit('.', 1)[1] == "zip":
                        with zipfile.ZipFile(path.join(app.config['UPLOAD_FOLDER'], filename), 'r') as service_zip:
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
                                    return render_template("forms.html", services=services, missing_files=missing_files, filename=filename, indexDesc=desc, url=url)

                            # move to services folder
                            i = 0
                            while i != -1:
                                try:
                                    if i == 0:
                                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                                     filename.rsplit('.', 1)[0],
                                                     filename.rsplit('.', 1)[0]),
                                           app.config['SERVICES_FOLDER'])
                                    elif i == 1:
                                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                                     filename.rsplit('.', 1)[0],
                                                     filename.rsplit('.', 1)[0]),
                                           path.join(app.config['UPLOAD_FOLDER'],
                                                     filename.rsplit('.', 1)[0],
                                                     (filename.rsplit('.', 1)[0])+str(i)))
                                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                                     filename.rsplit('.', 1)[0],
                                                     (filename.rsplit('.', 1)[0])+str(i)),
                                           app.config['SERVICES_FOLDER'])
                                    else:
                                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                                     filename.rsplit('.', 1)[0],
                                                     (filename.rsplit('.', 1)[0])+str(i-1)),
                                           path.join(app.config['UPLOAD_FOLDER'],
                                                     filename.rsplit('.', 1)[0],
                                                     (filename.rsplit('.', 1)[0])+str(i)))
                                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                                     filename.rsplit('.', 1)[0],
                                                     (filename.rsplit('.', 1)[0])+str(i)),
                                           app.config['SERVICES_FOLDER'])
                                    i = -1
                                except:
                                    i += 1
                            # remove leftover files in tmp
                            remove(path.join(app.config['UPLOAD_FOLDER'], filename))
                            rmdir(path.join(app.config['UPLOAD_FOLDER'], filename.rsplit('.', 1)[0]))

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
                                    return render_template("forms.html", services=services, missing_files=missing_files, filename=filename, indexDesc=desc, url=url)

                            # move to services folder
                            i = 0
                            while i != -1:
                                try:
                                    if i == 0:
                                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                                     filename.rsplit('.', 2)[0],
                                                     filename.rsplit('.', 2)[0]),
                                           app.config['SERVICES_FOLDER'])
                                    elif i == 1:
                                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                                     filename.rsplit('.', 2)[0],
                                                     filename.rsplit('.', 2)[0]),
                                           path.join(app.config['UPLOAD_FOLDER'],
                                                     filename.rsplit('.', 2)[0],
                                                     (filename.rsplit('.', 2)[0])+str(i)))
                                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                                     filename.rsplit('.', 2)[0],
                                                     (filename.rsplit('.', 2)[0])+str(i)),
                                           app.config['SERVICES_FOLDER'])
                                    else:
                                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                                     filename.rsplit('.', 2)[0],
                                                     (filename.rsplit('.', 2)[0])+str(i-1)),
                                           path.join(app.config['UPLOAD_FOLDER'],
                                                     filename.rsplit('.', 2)[0],
                                                     (filename.rsplit('.', 2)[0])+str(i)))
                                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                                     filename.rsplit('.', 2)[0],
                                                     (filename.rsplit('.', 2)[0])+str(i)),
                                           app.config['SERVICES_FOLDER'])
                                    i = -1
                                except:
                                    i += 1
                            # remove leftover files in tmp
                            remove(path.join(app.config['UPLOAD_FOLDER'], filename))
                            rmdir(path.join(app.config['UPLOAD_FOLDER'], filename.rsplit('.', 2)[0]))
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
                    # !! TODO try/except
                    if url.rsplit('.', 1)[1] == "git":
                        # !! TODO try/except - if the folder already exists
                        git.clone(url, path.join(app.config['UPLOAD_FOLDER'],
                                                 (url.rsplit('/', 1)[1]).rsplit('.', 1)[0]))

                        # check for dockerfile at root
                        if path.exists(path.join(app.config['UPLOAD_FOLDER'],
                                                 (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                 "Dockerfile")):
                            # check for existence of necessary files
                            missing_files = {}
                            for key,value in app.config['SERVICE_DICT'].items():
                                if not path.exists(path.join(app.config['UPLOAD_FOLDER'],
                                                             (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                             value)):
                                    missing_files[key] = value
                            services.append((url.rsplit('/', 1)[1]).rsplit('.', 1)[0])
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
                                                     (url.rsplit('/', 1)[1]).rsplit('.', 1)[0]),
                                           app.config['SERVICES_FOLDER'])
                                    elif i == 1:
                                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                                     (url.rsplit('/', 1)[1]).rsplit('.', 1)[0]),
                                           path.join(app.config['UPLOAD_FOLDER'],
                                                     ((url.rsplit('/', 1)[1]).rsplit('.', 1)[0])+str(i)))
                                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                                     ((url.rsplit('/', 1)[1]).rsplit('.', 1)[0])+str(i)),
                                           app.config['SERVICES_FOLDER'])
                                    else:
                                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                                     ((url.rsplit('/', 1)[1]).rsplit('.', 1)[0])+str(i-1)),
                                           path.join(app.config['UPLOAD_FOLDER'],
                                                     ((url.rsplit('/', 1)[1]).rsplit('.', 1)[0])+str(i)))
                                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                                     ((url.rsplit('/', 1)[1]).rsplit('.', 1)[0])+str(i)),
                                           app.config['SERVICES_FOLDER'])
                                    i = -1
                                except:
                                    i += 1
                            try:
                                # remove leftover files in tmp
                                rmdir(path.join(app.config['UPLOAD_FOLDER'],
                                                (url.rsplit('/', 1)[1]).rsplit('.', 1)[0]))
                            except:
                                pass
                        # check for dockerfile assuming repo is the services folder
                        elif path.exists(path.join(app.config['UPLOAD_FOLDER'],
                                                 (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                 app.config['SERVICE_DICT']['dockerfile'])):
                            # check for existence of necessary files
                            missing_files = {}
                            for key,value in app.config['SERVICE_DICT'].items():
                                if not path.exists(path.join(app.config['UPLOAD_FOLDER'],
                                                             (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                             value)):
                                    missing_files[key] = value
                            services.append((url.rsplit('/', 1)[1]).rsplit('.', 1)[0])
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
                                                     (url.rsplit('/', 1)[1]).rsplit('.', 1)[0]),
                                           app.config['SERVICES_FOLDER'])
                                    elif i == 1:
                                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                                     (url.rsplit('/', 1)[1]).rsplit('.', 1)[0]),
                                           path.join(app.config['UPLOAD_FOLDER'],
                                                     ((url.rsplit('/', 1)[1]).rsplit('.', 1)[0])+str(i)))
                                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                                     ((url.rsplit('/', 1)[1]).rsplit('.', 1)[0])+str(i)),
                                           app.config['SERVICES_FOLDER'])
                                    else:
                                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                                     ((url.rsplit('/', 1)[1]).rsplit('.', 1)[0])+str(i-1)),
                                           path.join(app.config['UPLOAD_FOLDER'],
                                                     ((url.rsplit('/', 1)[1]).rsplit('.', 1)[0])+str(i)))
                                        mv(path.join(app.config['UPLOAD_FOLDER'],
                                                     ((url.rsplit('/', 1)[1]).rsplit('.', 1)[0])+str(i)),
                                           app.config['SERVICES_FOLDER'])
                                    i = -1
                                except:
                                    i += 1
                            try:
                                # remove leftover files in tmp
                                rmdir(path.join(app.config['UPLOAD_FOLDER'],
                                                (url.rsplit('/', 1)[1]).rsplit('.', 1)[0]))
                            except:
                                pass
                        else:
                            i = 0
                            repo_dirs = []
                            for root, dirs, files in walk(path.join(app.config['UPLOAD_FOLDER'],
                                                                    (url.rsplit('/', 1)[1]).rsplit('.', 1)[0])):
                                if i == 0:
                                    repo_dirs = dirs
                                i += 1
                            if ".git" in repo_dirs:
                                repo_dirs.remove(".git")
                            services=repo_dirs
                            for service_dir in repo_dirs:
                                # check for dockerfile one folder deep
                                # could be more than one
                                if path.exists(path.join(app.config['UPLOAD_FOLDER'],
                                                         (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                         service_dir, "Dockerfile")):
                                    # check for existence of necessary files
                                    missing_files = {}
                                    for key,value in app.config['SERVICE_DICT'].items():
                                        if not path.exists(path.join(app.config['UPLOAD_FOLDER'],
                                                                     (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
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
                                                             (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                             service_dir),
                                                   app.config['SERVICES_FOLDER'])
                                            elif i == 1:
                                                mv(path.join(app.config['UPLOAD_FOLDER'],
                                                             (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                             service_dir),
                                                   path.join(app.config['UPLOAD_FOLDER'],
                                                             (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                             service_dir+str(i)))
                                                mv(path.join(app.config['UPLOAD_FOLDER'],
                                                             (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                             service_dir+str(i)),
                                                   app.config['SERVICES_FOLDER'])
                                            else:
                                                mv(path.join(app.config['UPLOAD_FOLDER'],
                                                             (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                             service_dir+str(i-1)),
                                                   path.join(app.config['UPLOAD_FOLDER'],
                                                             (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                             service_dir+str(i)))
                                                mv(path.join(app.config['UPLOAD_FOLDER'],
                                                             (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                             service_dir+str(i)),
                                                   app.config['SERVICES_FOLDER'])
                                            i = -1
                                        except:
                                            i += 1
                                # check for dockerfile in regular services folder
                                # could be more than one
                                elif path.exists(path.join(app.config['UPLOAD_FOLDER'],
                                                           (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                           service_dir, app.config['SERVICE_DICT']['dockerfile'])):
                                    print "dockerfile in services folder"
                                    # check for existence of necessary files
                                    missing_files = {}
                                    for key,value in app.config['SERVICE_DICT'].items():
                                        if not path.exists(path.join(app.config['UPLOAD_FOLDER'],
                                                                     (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
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
                                                print path.join(app.config['UPLOAD_FOLDER'],
                                                                (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                                service_dir)
                                                mv(path.join(app.config['UPLOAD_FOLDER'],
                                                             (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                             service_dir),
                                                   app.config['SERVICES_FOLDER'])
                                            elif i == 1:
                                                mv(path.join(app.config['UPLOAD_FOLDER'],
                                                             (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                             service_dir),
                                                   path.join(app.config['UPLOAD_FOLDER'],
                                                             (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                             service_dir+str(i)))
                                                mv(path.join(app.config['UPLOAD_FOLDER'],
                                                             (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                             service_dir+str(i)),
                                                   app.config['SERVICES_FOLDER'])
                                            else:
                                                mv(path.join(app.config['UPLOAD_FOLDER'],
                                                             (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                             service_dir+str(i-1)),
                                                   path.join(app.config['UPLOAD_FOLDER'],
                                                             (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                             service_dir+str(i)))
                                                mv(path.join(app.config['UPLOAD_FOLDER'],
                                                             (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                             service_dir+str(i)),
                                                   app.config['SERVICES_FOLDER'])
                                            i = -1
                                        except:
                                            i += 1
                            try:
                                rmdir(path.join(app.config['UPLOAD_FOLDER'],
                                                (url.rsplit('/', 1)[1]).rsplit('.', 1)[0]))
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
                        print url
            except:
                print "Bad URL"
        else:
            return render_template("failed.html")
        return redirect(url_for('index'))

    row = ""
    services = listdir("services")
    for service in services:
        last_modified = ""
        last_modified = time.ctime(path.getmtime("services/"+service))
        description = ""
        # !! TODO try/except
        description_path = "services/"+service+"/"+app.config['SERVICE_DICT']['description']
        with open(description_path, 'r') as content_file:
            description = content_file.read()
        row += '<tr><td class="rowlink-skip"><a href="saas/'+service+'">'+service+'</a></td><td>'+description+'</td><td><a href="saas/'+service+'">'+last_modified+'</a></td></tr>'
    row = Markup(row)
    return render_template("index.html",row=row)
