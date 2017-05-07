# home/views.py
from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse, reverse_lazy
from .forms import DocumentForm
import os, time, sys
from stat import * # ST_SIZE etc
import MySQLdb
import uuid
from subprocess import call
import subprocess
import metadata_parser
from bs4 import BeautifulSoup
import urllib
import re
from itertools import tee, zip_longest
import shlex


def createShellScript():

    # if filenamecleanup script doesn't already exist, make it
    if not os.path.exists('filenamecleanup.sh'):
        with open('filenamecleanup.sh', 'w') as script:
            script.write('#!/bin/bash\n')
            script.write('filename=$1\n')
            script.write('''newword=""\n''')
            script.write('loopcounter=1\n')
            script.write('for word in $filename; do\n')
            script.write('if [ $loopcounter = 1 ]; then\n')
            script.write('newword=$word\n')
            script.write('loopcounter=$(($loopcounter + 1))\n')
            script.write('else\n')
            script.write('''newword="$newword\ $word"\n''')
            script.write('fi\n')
            script.write('done\n')
            script.write('echo $newword\n')

    # if pathfinder script doesn't already exist, make it
    if not os.path.exists('pathfinder.sh'):
        with open('pathfinder.sh', 'w') as script:
            script.write('#!/bin/bash\n')
            script.write('cleanfilename=$1\n')
            script.write('size=$2\n')
            script.write('homedir=$3\n')
            script.write('find $homedir -type f -size $size -name "$cleanfilename" 2>/dev/null\n')

    # new pathfinder
    if not os.path.exists('newpathfinder.sh'):
        with open('newpathfinder.sh', 'w') as script:
            script.write('#!/bin/bash\n')
            script.write('numargs=$#\n')
            script.write('concatrange=$(($numargs - 2))\n')
            script.write('count=2\n')
            script.write('newname=$1\n')
            script.write('for i in ${@:2}; do\n')
            script.write('''if [ "$count" -le "$concatrange" ]; then\n''')
            script.write('''newname="$newname\\ ${i}"\n''')
            script.write('count=$(($count+1))\n')
            script.write('fi\n')
            script.write('done\n')
            script.write('size=${@: -2:1}\n')
            script.write('homedir=${@: -1:1}\n')
            script.write('find $homedir -type f -size $size -name $newname 2>/dev/null\n')

    # if metadata extractor script doesn't already exist make it
    if not os.path.exists('metadataextractor.sh'):
        with open('metadataextractor.sh', 'w') as script:
            script.write('#!/bin/bash\n')
            script.write('filename=$1\n')
            script.write('''owner="$(stat -c '%U' "${filename}")"\n''')
            script.write('''lastaccess="$(stat -c '%x' "${filename}")"\n''')
            script.write('''lastmod="$(stat -c '%y' "${filename}")"\n''')
            script.write('''laststatuschange="$(stat -c '%z' "${filename}")"\n''')
            script.write('''output=${owner}"^^"${lastaccess}"^^"${lastmod}"^^"${laststatuschange}\n''')
            script.write('echo ${output}\n')

    # if file lister script doesn't already exist make it
    if not os.path.exists('files.sh'):
        with open('files.sh', 'w') as script:
            script.write('#!/bin/bash\n')
            script.write('currdir=$1\n')
            script.write('''filesonly="$(find ${currdir} -maxdepth 1 -not -path '*/\.*' -type f \( ! -iname ".*" \))"\n''')
            script.write('echo $filesonly\n')

    # if directory lister script doesn't already exist make it
    if not os.path.exists('directories.sh'):
        with open('directories.sh', 'w') as script:
            script.write('#!/bin/bash\n')
            script.write('currdir=$1\n')
            script.write('''directories="$(find ${currdir} -maxdepth 1 -not -path '*/\.*' -type d \( ! -iname ".*" \))"\n''')
            script.write('echo $directories\n')


class HomePageView(TemplateView):
    '''
    def get(self, request, **kwargs):
        return render(request, 'index.html', context=None)
    '''
    # let's create a shell script on the local computer!
    # for preparation of local file metadata extraction
    createShellScript()

    template_name = 'index.html'

class AboutPageView(TemplateView):
    template_name = 'about.html'

class BulkEntryPageView(TemplateView):
    template_name = 'bulkentry.html'


def bulk(request):
    if request.method == 'POST':

        # let's create a shell script on the local computer!
        # for preparation of local file metadata extraction
        createShellScript()

        # extract file, filename, size, and local directory
        file = request.FILES['file']
        filename = str(file)
        size = request.POST['size']
        local_homedir = request.META['HOME']

        print("file = {}".format(file))
        print("filename = {}".format(filename))
        print("size = {}".format(size))
        print("local home directory = {}".format(local_homedir))

        # extract all relevant metadata from current file
        guid, localpath, lastmod, owner = extractLocalMetadata(filename, size, local_homedir)

        print("localpath = {}".format(localpath))
        print("filename = {}".format(filename))


        # get the directory of the file selected for bulk load preparation
        directory = localpath[:-len(filename)]

        print("directory of file is = {}".format(directory))


        # run file script to get all the files in the current directory
        proc = subprocess.Popen(["bash", "files.sh", directory], stdout=subprocess.PIPE)
        print("proc = {}".format(proc))

        file_list_str = ""
        # extract all the paths pathfinder returns you
        for row in proc.stdout:
            file_list_str += row.decode("utf-8").rstrip()
            print("row.decode = {}".format(row.decode("utf-8")))

        print("file_list_str= {}".format(file_list_str))

        indices = [m.start() for m in re.finditer("/home/", file_list_str)]

        print("indices = {}".format(indices))
        start, end = tee(indices)

        end.__next__()

        separated_list = [file_list_str[i:j] for i, j in zip_longest(start, end)]

        cleaned = []
        for ele in separated_list:
            cleaned.append(ele.rstrip())

        print("cleaned ={}".format(cleaned))

        return HttpResponseRedirect(reverse('success'))

    return HttpResponse("Failed")








class CategorizePageView(TemplateView):
    template_name = 'categorize.html'


def categorize(request):
    # make connection to database
    conn = MySQLdb.connect(host="localhost",
                           user="root",
                           passwd="password",
                           db="Documents")
    x = conn.cursor()

    # submit query for getting all DAGRs
    x.execute("""SELECT * FROM DAGR""")

    # create dictionary of DAGRs
    dagr_list = {}
    for row in x:
        print("row = {}".format(row))
        dagr_list[row[0]] = row[1]


    print("dagr_list = {}".format(dagr_list))

    # submit query for getting all Categories
    y = conn.cursor()
    y.execute("""SELECT * FROM Categories""")

    # create dictionary of Categories
    category_list = {}

    for row in y:
        print("row = {}".format(row))
        category_list[row[0]] = row[1]


    conn.close()


    return render(request, 'categorize.html', {'dagr_list': dagr_list, 'category_list': category_list})

def categorizeSubmission(request):
    if request.method == 'POST':
        category = request.POST.get('category-selection')
        dagrid = request.POST.get('dagr-selection', None)

        print("selected category was = {}".format(category))
        print("selected dagr id was = {}".format(dagrid))

        # make connection to database
        conn = MySQLdb.connect(host="localhost",
                               user="root",
                               passwd="password",
                               db="Documents")
        x = conn.cursor()

        x.execute("""SELECT * FROM Categories""")


        print("---category table---")
        dagrwithcat_exists = False
        for row in x:
            print("current category = {}".format(row[0]))
            print("current dagrid = {}".format(row[1]))

            if row[0] == category and row[1] == dagrid:
                print("this combo already exists! Breaking out of loop!")
                dagrwithcat_exists = True
                break
            print("row = {}".format(row))

        if not dagrwithcat_exists:
            x.execute(""" INSERT INTO Categories VALUES (%s, %s) """, (category, dagrid))
            conn.commit()
            print("new entry inserted into Category table!")

        conn.close()

        return HttpResponseRedirect(reverse('success'))

    return HttpResponse("Failed")





class DeletePageView(TemplateView):
    template_name = 'delete.html'

class FindOrphansPageView(TemplateView):
    template_name = 'findorphans.html'

class HtmlParserPageView(TemplateView):
    template_name = 'htmlparser.html'

class InsertPageView(TemplateView):
    template_name = 'insert.html'

def upload(request):
    if request.method == 'POST':

        # let's create a shell script on the local computer!
        # for preparation of local file metadata extraction
        createShellScript()

        # extract file, filename, size, and local directory
        file = request.FILES['file']
        filename = str(file)
        size = request.POST['size']
        local_homedir = request.META['HOME']


        print("file = {}".format(file))

        # extract all relevant metadata from file
        guid, localpath, lastmod, owner = extractLocalMetadata(filename, size, local_homedir)

        insertIntoDB(guid, filename, localpath, size, lastmod, owner)

        return HttpResponseRedirect(reverse('success'))

    return HttpResponse("Failed")


def escape(filename):
    special_chars = ['!', '#', '$', '%', '&', "'", '*', '+', '-', '.', '^', '_', '`', '|', '~', ':', ' ']
    for char in filename:
        if char in special_chars:
            print('blah')




def extractLocalMetadata(filename, size, local_homedir):

    size_c = str(size) + "c"
    print("size_c = {}".format(size_c))

    print("filename is = {}".format(filename))

    # clean the filename up
    filename_proc = subprocess.Popen(["bash", "filenamecleanup.sh", filename], stdout=subprocess.PIPE)
    cleaned_filename = ""
    for row in filename_proc.stdout:
        cleaned_filename = row.decode("utf-8").rstrip()
    print("cleaned_filename = {}".format(cleaned_filename))


    # run pathfinder script to get the paths
    proc = subprocess.Popen(["bash", "pathfinder.sh", cleaned_filename, size_c, local_homedir], stdout=subprocess.PIPE)


    path_list = []
    # extract all the paths pathfinder returns you
    for row in proc.stdout:
        print("row of proc.stdout = {}".format(row))
        path_list.append(row.decode("utf-8").rstrip())
        print("row.decode = {}".format(row.decode("utf-8")))

    print("path_list = {}".format(path_list))

    # if there is more than one path in path list, choose the first one
    if len(path_list) != 1:
        localpath = path_list[0]
    elif len(path_list) == 0:
        raise Exception('Why is there no path?')
    else:
        localpath = path_list[0]

    print("local path extracted = {}".format(localpath))

    ##############################################
    # Still some issues with filenames with spaces
    ##############################################

    # grab metadata using metadataextractor script
    extractor_output = subprocess.Popen(["bash", "metadataextractor.sh", localpath], stdout=subprocess.PIPE)

    print("extractor output = {}".format(extractor_output))

    for row in extractor_output.stdout:
        print("row.decode = {}".format(row.decode("utf-8").rstrip()))
        extractor_output_combined = row.decode("utf-8")
        print(extractor_output_combined)

    extractor_split = extractor_output_combined.split("^^")
    print("split array = {}".format(extractor_split))

    owner = extractor_split[0]
    lastaccess = extractor_split[1].split('.')[0]
    lastmod = extractor_split[2].split('.')[0]
    laststatuschange = extractor_split[3].split('.')[0]

    print("owner = {}\nlastaccess = {}\nlastmod = {}\nlaststatuschange = {}".format(owner, lastaccess, lastmod, laststatuschange))

    guid = uuid.uuid4()

    return guid, localpath, lastmod, owner




def insertIntoDB(guid, filename, localpath, size, lastmod, owner):

    guid = str(guid)
    conn = MySQLdb.connect(host="localhost",
                           user="root",
                           passwd="password",
                           db="Documents")
    x = conn.cursor()

    x.execute(""" INSERT INTO DAGR VALUES (%s, %s, %s, %s, %s, %s, %s) """,
              (guid, filename, localpath, size, lastmod, owner, ' '))
    conn.commit()
    x.execute("""SELECT * FROM DAGR""")
    for row in x:
        print(row)
    conn.close()
    print("dagr created from metadata!")






def urlParser(request):
    if request.method == "GET":
        url = request.GET.get('url')
        # if first 7 or 8 chars are not http:// or https:// append it
        http = "http://"
        https = "https://"
        if not url.startswith(http) or not url.startswith(https):
            url = http + url

        print("url = {}".format(url))
        page = metadata_parser.MetadataParser(url=url, search_head_only=False)
        print("page = {}".format(page.metadata))


        title = page.get_metadata('title')

        description = page.get_metadata('description')

        id = uuid.uuid4()

        date = page.get_metadata('pubdate')

        date = date[:10] + " " + date[11:len(date) - 1]

        last_modified = page.get_metadata('lastmod')

        last_modified = date[:10] + " " + date[11:len(date) - 1]

    return HttpResponseRedirect(reverse('success'))




def metadataqueryresults(request):
    if request.method == "POST":
        # get the search terms, None if nothing entered
        print("IM A POST LIKE IM SUPPOSED TO BE")
        print("request.POST = {}".format(request.POST))

        guid = str(request.POST.get('guid'))

        name = str(request.POST.get('name'))
        category = str(request.POST.get('category'))
        path = str(request.POST.get('path'))
        size = str(request.POST.get('size'))
        creationtime = str(request.POST.get('creationtime'))
        creator = str(request.POST.get('creator'))
        modtime = str(request.POST.get('modtime'))
        date = str(request.POST.get('date'))

        print("guid = {}".format(guid))
        print("name = {}".format(name))
        print("category = {}".format(category))
        print("path = {}".format(path))
        print("size = {}".format(size))
        print("creationtime = {}".format(creationtime))
        print("creator = {}".format(creator))
        print("modtime = {}".format(modtime))
        print("date = {}".format(date))

        conn = MySQLdb.connect(host="localhost",
                               user="root",
                               passwd="password",
                               db="Documents")
        x = conn.cursor()

        x.execute("""SELECT * FROM DAGR""")
        for row in x:
            print(row)
        conn.close()



        return HttpResponseRedirect(reverse('success'))
    return HttpResponse("Failed")


class SuccessView(TemplateView):
    template_name = 'success.html'

class MetadataQueryPageView(TemplateView):
    template_name = 'metadataquery.html'


class ModifyPageView(TemplateView):
    template_name = 'modify.html'

class ReachPageView(TemplateView):
    template_name = 'reach.html'

class TimeRangePageView(TemplateView):
    template_name = 'timerange.html'