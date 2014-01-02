from wharf import app

from ast import literal_eval
from flask import jsonify
from flask import render_template
from flask import request
from os import mkdir
from os import path
from os import remove
from os import rmdir
from sh import mv
from shutil import rmtree

def move_services(filename, j, num_ext):
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
            j = i
            i = -1
        except:
            i += 1

    # remove leftover files in tmp
    remove(path.join(app.config['UPLOAD_FOLDER'], filename))
    rmtree(path.join(app.config['UPLOAD_FOLDER'], file_path))
    return j

def add_metadata(meta, filename, j, num_ext):
    meta_path = app.config['SERVICES_FOLDER']+filename.rsplit('.', num_ext)[0]+str(j)
    if not path.exists(meta_path+"/html"):
        mkdir(meta_path+"/html")
    with open(meta_path+"/"+app.config['SERVICE_DICT'][metadata], 'w') as f:
        f.write(meta)

def missing_metadata(j, filename, metadata):
    meta = ""
    try:
        meta = request.json[metadata]
    except:
        pass
    if j == 0:
        j = ""
    if filename.rsplit('.', 1)[1] == "zip":
        add_metadata(meta, filename, j, 1)
    elif filename.rsplit('.', 1)[1] == "gz":
        add_metadata(meta, filename, j, 2)

@app.route('/forms', methods=['POST'])
def forms():
    try:
        filename = request.json['filename']
        url = request.json['url']
        services = request.json['services']
        i = 0
        j = 0
        if filename:
            if filename.rsplit('.', 1)[1] == "zip":
                j = move_services(filename, j, 1)
            elif filename.rsplit('.', 1)[1] == "gz":
                j = move_services(filename, j, 2)

            missing_files = request.json['missing_files']
            if "description" in missing_files:
                description = ""
                try:
                    description = request.json['description']
                except:
                    pass
                if j == 0:
                    j = ""
                if filename.rsplit('.', 1)[1] == "zip":
                    with open(app.config['SERVICES_FOLDER']+filename.rsplit('.', 1)[0]+str(j)+"/"+app.config['SERVICE_DICT']['description'], 'w') as f:
                        f.write(description)
                elif filename.rsplit('.', 1)[1] == "gz":
                    with open(app.config['SERVICES_FOLDER']+filename.rsplit('.', 2)[0]+str(j)+"/"+app.config['SERVICE_DICT']['description'], 'w') as f:
                        f.write(description)
            if "client" in missing_files:
                client = ""
                clientLanguage = ""
                clientFilename = "dummy.txt"
                try:
                    client = request.json['client']
                    clientLanguage = request.json['clientLanguage']
                    clientFilename = request.json['clientFilename']
                except:
                    pass
                if j == 0:
                    j = ""
                if filename.rsplit('.', 1)[1] == "zip":
                    meta_path = app.config['SERVICES_FOLDER']+filename.rsplit('.', 1)[0]+str(j)
                    if not path.exists(meta_path+"/client"):
                        mkdir(meta_path+"/client")
                    with open(meta_path+"/"+app.config['SERVICE_DICT']['client'], 'w') as f:
                        f.write(clientLanguage+"\n")
                        f.write(clientFilename)
                    with open(meta_path+"/client/"+clientFilename, 'w') as f:
                        f.write(client)
                elif filename.rsplit('.', 1)[1] == "gz":
                    meta_path = app.config['SERVICES_FOLDER']+filename.rsplit('.', 2)[0]+str(j)
                    if not path.exists(meta_path+"/client"):
                        mkdir(meta_path+"/client")
                    with open(meta_path+"/"+app.config['SERVICE_DICT']['client'], 'w') as f:
                        f.write(clientLanguage+"\n")
                        f.write(clientFilename)
                    with open(meta_path+"/client/"+clientFilename, 'w') as f:
                        f.write(client)
            if "about" in missing_files:
                missing_metadata(j, filename, "about")
            if "body" in missing_files:
                missing_metadata(j, filename, "body")
            if "link" in missing_files:
                link = "#"
                linkName = "None"
                try:
                    link = request.json['link']
                    linkName = request.json['linkName']
                except:
                    pass
                if j == 0:
                    j = ""
                if filename.rsplit('.', 1)[1] == "zip":
                    if not path.exists(app.config['SERVICES_FOLDER']+filename.rsplit('.', 1)[0]+str(j)+"/html"):
                        mkdir(app.config['SERVICES_FOLDER']+filename.rsplit('.', 1)[0]+str(j)+"/html")
                    with open(app.config['SERVICES_FOLDER']+filename.rsplit('.', 1)[0]+str(j)+"/"+app.config['SERVICE_DICT']['link'], 'w') as f:
                        f.write(link+" "+linkName)
                elif filename.rsplit('.', 1)[1] == "gz":
                    if not path.exists(app.config['SERVICES_FOLDER']+filename.rsplit('.', 2)[0]+str(j)+"/html"):
                        mkdir(app.config['SERVICES_FOLDER']+filename.rsplit('.', 2)[0]+str(j)+"/html")
                    with open(app.config['SERVICES_FOLDER']+filename.rsplit('.', 2)[0]+str(j)+"/"+app.config['SERVICE_DICT']['link'], 'w') as f:
                        f.write(link+" "+linkName)
        elif url:
            j_array = []
            if not "." in url or not "git" in url:
                # docker index
                j = 0
                j_array.append(j)
            elif url.rsplit('.', 1)[1] == "git":
                # move to services folder
                i = 0
                # keeps track of the number of the service (if there is more than one)
                j = 0
                try:
                    services = services.replace('&#39;', "'")
                    services = [ item.encode('ascii') for item in literal_eval(services) ]
                except:
                    pass
                if not services:
                    return render_template("failed.html")
                elif len(services) == 1:
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
                            j = i
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
                    for service in services:
                        i = 0
                        while i != -1:
                            try:
                                if i == 0:
                                    mv(path.join(app.config['UPLOAD_FOLDER'],
                                                 (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                 service),
                                       app.config['SERVICES_FOLDER'])
                                elif i == 1:
                                    mv(path.join(app.config['UPLOAD_FOLDER'],
                                                 (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                 service),
                                       path.join(app.config['UPLOAD_FOLDER'],
                                                 (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                 (service)+str(i)))
                                    mv(path.join(app.config['UPLOAD_FOLDER'],
                                                 (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                 (service)+str(i)),
                                       app.config['SERVICES_FOLDER'])
                                else:
                                    mv(path.join(app.config['UPLOAD_FOLDER'],
                                                 (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                 (service)+str(i-1)),
                                       path.join(app.config['UPLOAD_FOLDER'],
                                                 (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                 (service)+str(i)))
                                    mv(path.join(app.config['UPLOAD_FOLDER'],
                                                 (url.rsplit('/', 1)[1]).rsplit('.', 1)[0],
                                                 (service)+str(i)),
                                       app.config['SERVICES_FOLDER'])
                                j = i
                                i = -1
                            except:
                                i += 1
                        j_array.append(j)
                    try:
                        # remove leftover files in tmp
                        rmtree(path.join(app.config['UPLOAD_FOLDER'],
                                        (url.rsplit('/', 1)[1]).rsplit('.', 1)[0]))
                    except:
                        pass

                # !! TODO
                # array of services
                # return array of missing files, empty slots for ones that don't need replacing
                # eventually allow this for file upload as well
                # something different is git repo versus docker index
                # can all git repos be handled the same, or are there ones that might be different?

            try:
                services = services.replace('&#39;', "'")
                services = [ item.encode('ascii') for item in literal_eval(services) ]
            except:
                pass
            if len(services) > 1:
                print services
                counter = 0
                for service in services:
                    # update missing_files for array of them,
                    # similarly with description, client, about, body, link, etc.
                    missing_files = request.json['missing_files']
                    description = ""
                    if "description" in missing_files:
                        try:
                            description = request.json['description'+str(counter)]
                        except:
                            pass
                        if j_array[counter] == 0:
                            j_array[counter] = ""
                        # if url is docker index
                        if not "." in url or not "git" in url:
                            if description == "":
                                description = request.json['indexDesc']
                            index_service = service.replace("/", "-")
                            if not path.exists(app.config['SERVICES_FOLDER']+index_service+str(j_array[counter])):
                                mkdir(app.config['SERVICES_FOLDER']+index_service+str(j_array[counter]))
                            with open(app.config['SERVICES_FOLDER']+index_service+str(j_array[counter])+"/"+app.config['SERVICE_DICT']['description'], 'w') as f:
                                f.write(description)
                        elif url.rsplit('.', 1)[1] == "git":
                            with open(app.config['SERVICES_FOLDER']+service+str(j_array[counter])+"/"+app.config['SERVICE_DICT']['description'], 'w') as f:
                                f.write(description)
                    else:
                        if j_array[counter] == 0:
                            j_array[counter] = ""
                        # if url is docker index
                        if not "." in url or not "git" in url:
                            if description == "":
                                description = request.json['indexDesc']
                            index_service = service.replace("/", "-")
                            if not path.exists(app.config['SERVICES_FOLDER']+index_service+str(j_array[counter])):
                                mkdir(app.config['SERVICES_FOLDER']+index_service+str(j_array[counter]))
                            with open(app.config['SERVICES_FOLDER']+index_service+str(j_array[counter])+"/"+app.config['SERVICE_DICT']['description'], 'w') as f:
                                f.write(description)

                    if "client" in missing_files:
                        client = ""
                        clientLanguage = ""
                        clientFilename = "dummy.txt"
                        try:
                            client = request.json['client'+str(counter)]
                            clientLanguage = request.json['clientLanguage'+str(counter)]
                            clientFilename = request.json['clientFilename'+str(counter)]
                        except:
                            pass
                        if j_array[counter] == 0:
                            j_array[counter] = ""
                        # if url is docker index
                        if not "." in url or not "git" in url:
                            index_service = service.replace("/", "-")
                            if not path.exists(app.config['SERVICES_FOLDER']+index_service+str(j_array[counter])):
                                mkdir(app.config['SERVICES_FOLDER']+index_service+str(j_array[counter]))
                            if not path.exists(app.config['SERVICES_FOLDER']+index_service+str(j_array[counter])+"/client"):
                                mkdir(app.config['SERVICES_FOLDER']+index_service+str(j_array[counter])+"/client")
                            with open(app.config['SERVICES_FOLDER']+index_service+str(j_array[counter])+"/"+app.config['SERVICE_DICT']['client'], 'w') as f:
                                f.write(clientLanguage+"\n")
                                f.write(clientFilename)
                            with open(app.config['SERVICES_FOLDER']+index_service+str(j_array[counter])+"/client/"+clientFilename, 'w') as f:
                                f.write(client)
                        elif url.rsplit('.', 1)[1] == "git":
                            if not path.exists(app.config['SERVICES_FOLDER']+service+str(j_array[counter])+"/client"):
                                mkdir(app.config['SERVICES_FOLDER']+service+str(j_array[counter])+"/client")
                            with open(app.config['SERVICES_FOLDER']+service+str(j_array[counter])+"/"+app.config['SERVICE_DICT']['client'], 'w') as f:
                                f.write(clientLanguage+"\n")
                                f.write(clientFilename)
                            with open(app.config['SERVICES_FOLDER']+service+str(j_array[counter])+"/client/"+clientFilename, 'w') as f:
                                f.write(client)
                    if "about" in missing_files:
                        about = ""
                        try:
                            about = request.json['about'+str(counter)]
                        except:
                            pass
                        if j_array[counter] == 0:
                            j_array[counter] = ""
                        # if url is docker index
                        if not "." in url or not "git" in url:
                            index_service = service.replace("/", "-")
                            if not path.exists(app.config['SERVICES_FOLDER']+index_service+str(j_array[counter])):
                                mkdir(app.config['SERVICES_FOLDER']+index_service+str(j_array[counter]))
                            if not path.exists(app.config['SERVICES_FOLDER']+index_service+str(j_array[counter])+"/html"):
                                mkdir(app.config['SERVICES_FOLDER']+index_service+str(j_array[counter])+"/html")
                            with open(app.config['SERVICES_FOLDER']+index_service+str(j_array[counter])+"/"+app.config['SERVICE_DICT']['about'], 'w') as f:
                                f.write(about)
                        elif url.rsplit('.', 1)[1] == "git":
                            if not path.exists(app.config['SERVICES_FOLDER']+service+str(j_array[counter])+"/html"):
                                mkdir(app.config['SERVICES_FOLDER']+service+str(j_array[counter])+"/html")
                            with open(app.config['SERVICES_FOLDER']+service+str(j_array[counter])+"/"+app.config['SERVICE_DICT']['about'], 'w') as f:
                                f.write(about)
                    if "body" in missing_files:
                        body = ""
                        try:
                            body = request.json['body'+str(counter)]
                        except:
                            pass
                        if j_array[counter] == 0:
                            j_array[counter] = ""
                        # if url is docker index
                        if not "." in url or not "git" in url:
                            index_service = service.replace("/", "-")
                            if not path.exists(app.config['SERVICES_FOLDER']+index_service+str(j_array[counter])):
                                mkdir(app.config['SERVICES_FOLDER']+index_service+str(j_array[counter]))
                            if not path.exists(app.config['SERVICES_FOLDER']+index_service+str(j_array[counter])+"/html"):
                                mkdir(app.config['SERVICES_FOLDER']+index_service+str(j_array[counter])+"/html")
                            with open(app.config['SERVICES_FOLDER']+index_service+str(j_array[counter])+"/"+app.config['SERVICE_DICT']['body'], 'w') as f:
                                f.write(body)
                        elif url.rsplit('.', 1)[1] == "git":
                            if not path.exists(app.config['SERVICES_FOLDER']+service+str(j_array[counter])+"/html"):
                                mkdir(app.config['SERVICES_FOLDER']+service+str(j_array[counter])+"/html")
                            with open(app.config['SERVICES_FOLDER']+service+str(j_array[counter])+"/"+app.config['SERVICE_DICT']['body'], 'w') as f:
                                f.write(body)
                    if "link" in missing_files:
                        link = "#"
                        linkName = "None"
                        try:
                            link = request.json['link'+str(counter)]
                            linkName = request.json['linkName'+str(counter)]
                        except:
                            pass
                        if j_array[counter] == 0:
                            j_array[counter] = ""
                        # if url is docker index
                        if not "." in url or not "git" in url:
                            index_service = service.replace("/", "-")
                            if not path.exists(app.config['SERVICES_FOLDER']+index_service+str(j_array[counter])):
                                mkdir(app.config['SERVICES_FOLDER']+index_service+str(j_array[counter]))
                            if not path.exists(app.config['SERVICES_FOLDER']+index_service+str(j_array[counter])+"/html"):
                                mkdir(app.config['SERVICES_FOLDER']+index_service+str(j_array[counter])+"/html")
                            with open(app.config['SERVICES_FOLDER']+index_service+str(j_array[counter])+"/"+app.config['SERVICE_DICT']['link'], 'w') as f:
                                f.write(link+" "+linkName)
                        elif url.rsplit('.', 1)[1] == "git":
                            if not path.exists(app.config['SERVICES_FOLDER']+service+str(j_array[counter])+"/html"):
                                mkdir(app.config['SERVICES_FOLDER']+service+str(j_array[counter])+"/html")
                            with open(app.config['SERVICES_FOLDER']+service+str(j_array[counter])+"/"+app.config['SERVICE_DICT']['link'], 'w') as f:
                                f.write(link+" "+linkName)
                    counter += 1
            else:
                missing_files = request.json['missing_files']
                description = ""
                if "description" in missing_files:
                    try:
                        description = request.json['description']
                    except:
                        pass
                    if j == 0:
                        j = ""
                    # if url is docker index
                    if not "." in url or not "git" in url:
                        if description == "":
                            description = request.json['indexDesc']
                        index_service = services[0].replace("/", "-")
                        if not path.exists(app.config['SERVICES_FOLDER']+index_service+str(j)):
                            mkdir(app.config['SERVICES_FOLDER']+index_service+str(j))
                        with open(app.config['SERVICES_FOLDER']+index_service+str(j)+"/"+app.config['SERVICE_DICT']['description'], 'w') as f:
                            f.write(description)
                    elif url.rsplit('.', 1)[1] == "git":
                        with open(app.config['SERVICES_FOLDER']+(url.rsplit('/', 1)[1]).rsplit('.', 1)[0]+str(j)+"/"+app.config['SERVICE_DICT']['description'], 'w') as f:
                            f.write(description)
                else:
                    if j == 0:
                        j = ""
                    # if url is docker index
                    if not "." in url or not "git" in url:
                        if description == "":
                            description = request.json['indexDesc']
                        index_service = services[0].replace("/", "-")
                        if not path.exists(app.config['SERVICES_FOLDER']+index_service+str(j)):
                            mkdir(app.config['SERVICES_FOLDER']+index_service+str(j))
                        with open(app.config['SERVICES_FOLDER']+index_service+str(j)+"/"+app.config['SERVICE_DICT']['description'], 'w') as f:
                            f.write(description)
                if "client" in missing_files:
                    client = ""
                    clientLanguage = ""
                    clientFilename = "dummy.txt"
                    try:
                        client = request.json['client']
                        clientLanguage = request.json['clientLanguage']
                        clientFilename = request.json['clientFilename']
                    except:
                        pass
                    if j == 0:
                        j = ""
                    # if url is docker index
                    if not "." in url or not "git" in url:
                        index_service = services[0].replace("/", "-")
                        if not path.exists(app.config['SERVICES_FOLDER']+index_service+str(j)):
                            mkdir(app.config['SERVICES_FOLDER']+index_service+str(j))
                        if not path.exists(app.config['SERVICES_FOLDER']+index_service+str(j)+"/client"):
                            mkdir(app.config['SERVICES_FOLDER']+index_service+str(j)+"/client")
                        with open(app.config['SERVICES_FOLDER']+index_service+str(j)+"/"+app.config['SERVICE_DICT']['client'], 'w') as f:
                            f.write(clientLanguage+"\n")
                            f.write(clientFilename)
                        with open(app.config['SERVICES_FOLDER']+index_service+str(j)+"/client/"+clientFilename, 'w') as f:
                            f.write(client)
                    elif url.rsplit('.', 1)[1] == "git":
                        if not path.exists(app.config['SERVICES_FOLDER']+(url.rsplit('/', 1)[1]).rsplit('.', 1)[0]+str(j)+"/client"):
                            mkdir(app.config['SERVICES_FOLDER']+(url.rsplit('/', 1)[1]).rsplit('.', 1)[0]+str(j)+"/client")
                        with open(app.config['SERVICES_FOLDER']+(url.rsplit('/', 1)[1]).rsplit('.', 1)[0]+str(j)+"/"+app.config['SERVICE_DICT']['client'], 'w') as f:
                            f.write(clientLanguage+"\n")
                            f.write(clientFilename)
                        with open(app.config['SERVICES_FOLDER']+(url.rsplit('/', 1)[1]).rsplit('.', 1)[0]+str(j)+"/client/"+clientFilename, 'w') as f:
                            f.write(client)
                if "about" in missing_files:
                    about = ""
                    try:
                        about = request.json['about']
                    except:
                        pass
                    if j == 0:
                        j = ""
                    # if url is docker index
                    if not "." in url or not "git" in url:
                        index_service = services[0].replace("/", "-")
                        if not path.exists(app.config['SERVICES_FOLDER']+index_service+str(j)):
                            mkdir(app.config['SERVICES_FOLDER']+index_service+str(j))
                        if not path.exists(app.config['SERVICES_FOLDER']+index_service+str(j)+"/html"):
                            mkdir(app.config['SERVICES_FOLDER']+index_service+str(j)+"/html")
                        with open(app.config['SERVICES_FOLDER']+index_service+str(j)+"/"+app.config['SERVICE_DICT']['about'], 'w') as f:
                            f.write(about)
                    elif url.rsplit('.', 1)[1] == "git":
                        if not path.exists(app.config['SERVICES_FOLDER']+(url.rsplit('/', 1)[1]).rsplit('.', 1)[0]+str(j)+"/html"):
                            mkdir(app.config['SERVICES_FOLDER']+(url.rsplit('/', 1)[1]).rsplit('.', 1)[0]+str(j)+"/html")
                        with open(app.config['SERVICES_FOLDER']+(url.rsplit('/', 1)[1]).rsplit('.', 1)[0]+str(j)+"/"+app.config['SERVICE_DICT']['about'], 'w') as f:
                            f.write(about)
                if "body" in missing_files:
                    body = ""
                    try:
                        body = request.json['body']
                    except:
                        pass
                    if j == 0:
                        j = ""
                    # if url is docker index
                    if not "." in url or not "git" in url:
                        index_service = services[0].replace("/", "-")
                        if not path.exists(app.config['SERVICES_FOLDER']+index_service+str(j)):
                            mkdir(app.config['SERVICES_FOLDER']+index_service+str(j))
                        if not path.exists(app.config['SERVICES_FOLDER']+index_service+str(j)+"/html"):
                            mkdir(app.config['SERVICES_FOLDER']+index_service+str(j)+"/html")
                        with open(app.config['SERVICES_FOLDER']+index_service+str(j)+"/"+app.config['SERVICE_DICT']['body'], 'w') as f:
                            f.write(body)
                    elif url.rsplit('.', 1)[1] == "git":
                        if not path.exists(app.config['SERVICES_FOLDER']+(url.rsplit('/', 1)[1]).rsplit('.', 1)[0]+str(j)+"/html"):
                            mkdir(app.config['SERVICES_FOLDER']+(url.rsplit('/', 1)[1]).rsplit('.', 1)[0]+str(j)+"/html")
                        with open(app.config['SERVICES_FOLDER']+(url.rsplit('/', 1)[1]).rsplit('.', 1)[0]+str(j)+"/"+app.config['SERVICE_DICT']['body'], 'w') as f:
                            f.write(body)
                if "link" in missing_files:
                    link = "#"
                    linkName = "None"
                    try:
                        link = request.json['link']
                        linkName = request.json['linkName']
                    except:
                        pass
                    if j == 0:
                        j = ""
                    # if url is docker index
                    if not "." in url or not "git" in url:
                        index_service = services[0].replace("/", "-")
                        if not path.exists(app.config['SERVICES_FOLDER']+index_service+str(j)):
                            mkdir(app.config['SERVICES_FOLDER']+index_service+str(j))
                        if not path.exists(app.config['SERVICES_FOLDER']+index_service+str(j)+"/html"):
                            mkdir(app.config['SERVICES_FOLDER']+index_service+str(j)+"/html")
                        with open(app.config['SERVICES_FOLDER']+index_service+str(j)+"/"+app.config['SERVICE_DICT']['link'], 'w') as f:
                            f.write(link+" "+linkName)
                    elif url.rsplit('.', 1)[1] == "git":
                        if not path.exists(app.config['SERVICES_FOLDER']+(url.rsplit('/', 1)[1]).rsplit('.', 1)[0]+str(j)+"/html"):
                            mkdir(app.config['SERVICES_FOLDER']+(url.rsplit('/', 1)[1]).rsplit('.', 1)[0]+str(j)+"/html")
                        with open(app.config['SERVICES_FOLDER']+(url.rsplit('/', 1)[1]).rsplit('.', 1)[0]+str(j)+"/"+app.config['SERVICE_DICT']['link'], 'w') as f:
                            f.write(link+" "+linkName)
    except:
        pass
    return jsonify(url=app.config['DOMAIN'])
