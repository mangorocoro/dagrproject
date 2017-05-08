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
            script.write('''size="$(stat -c '%s' "${filename}")"\n''')
            script.write('''output=${owner}"^^"${lastaccess}"^^"${lastmod}"^^"${laststatuschange}"^^"${size}\n''')
            script.write('echo ${output}\n')

    # if file lister script doesn't already exist make it
    if not os.path.exists('files.sh'):
        with open('files.sh', 'w') as script:
            script.write('#!/bin/bash\n')
            script.write('currdir=$1\n')
            script.write('''filesonly="$(find "${currdir}" -maxdepth 1 -not -path '*/\.*' -type f \( ! -iname ".*" \))"\n''')
            script.write('echo $filesonly\n')

    # if directory lister script doesn't already exist make it
    if not os.path.exists('directories.sh'):
        with open('directories.sh', 'w') as script:
            script.write('#!/bin/bash\n')
            script.write('currdir=$1\n')
            script.write('''directories="$(find "${currdir}" -maxdepth 1 -not -path '*/\.*' -type d \( ! -iname ".*" \))"\n''')
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


        # extract all relevant metadata from current file
        guid, localpath, lastmod, owner, extract_size = extractLocalMetadata(filename, size, local_homedir)



        # get the directory of the file selected for bulk load preparation
        directory = localpath[:-len(filename)]


        # extract all files from current directory and insert into db
        bulkfiles(directory)

        # travel into any subdirectories and bulk load files there
        bulkdirectory(directory)


        return HttpResponseRedirect(reverse('success'))

    return HttpResponse("Failed")



def bulkfiles(directory):
    # run file script to get all the files in the current directory
    proc = subprocess.Popen(["bash", "files.sh", directory], stdout=subprocess.PIPE)

    file_list_str = ""
    # extract all the paths pathfinder returns you
    for row in proc.stdout:
        file_list_str += row.decode("utf-8").rstrip()


    indices = [m.start() for m in re.finditer("/home/", file_list_str)]

    start, end = tee(indices)

    end.__next__()

    separated_list = [file_list_str[i:j] for i, j in zip_longest(start, end)]

    cleaned_files = []
    for ele in separated_list:
        cleaned_files.append(ele.rstrip())


    # insert each of the files into the db
    for f in cleaned_files:
        # extract all relevant metadata from file
        guid, localpath, lastmod, owner, current_file_size = extractWithPath(f)


        # process current filename (get rid of path, just take filename itself)
        current_filename = {localpath.replace(directory, '').replace('/', '') for x in localpath}


        # insert the file's metadata as a DAGR
        insertIntoDB(guid, current_filename, localpath, current_file_size, lastmod, owner, '')


def bulkdirectory(directory):
    # get list of any sub-directories that may exist in current directory
    # run directory searcher script to get any sub-directories that may exist in current directory
    proc = subprocess.Popen(["bash", "directories.sh", directory], stdout=subprocess.PIPE)
    print("proc = {}".format(proc))

    directory_list_str = ""
    # extract all the paths pathfinder returns you
    for row in proc.stdout:
        directory_list_str += row.decode("utf-8").rstrip()
        print("row.decode = {}".format(row.decode("utf-8")))

    print("directory_list_str= {}".format(directory_list_str))

    indices = [m.start() for m in re.finditer("/home/", directory_list_str)]

    print("indices = {}".format(indices))
    start, end = tee(indices)

    end.__next__()

    separated_list = [directory_list_str[i:j] for i, j in zip_longest(start, end)]

    cleaned_directories = []
    for ele in separated_list:
        cleaned_directories.append(ele.rstrip())

    print("cleaned ={}".format(cleaned_directories))

    # directories script returns all directories including the current directory.
    # get rid of the current directory (we don't need it)
    cleaned_directories = cleaned_directories[1:]

    # for each subdirectory, insert files
    for d in cleaned_directories:
        print("d = {}".format(d))
        bulkfiles(d)


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
        dagr_list[row[0]] = row[1]

    # submit query for getting all Categories
    y = conn.cursor()
    y.execute("""SELECT * FROM Categories""")

    # create dictionary of Categories
    category_list = {}

    for row in y:
        category_list[row[0]] = row[1]

    conn.close()


    return render(request, 'categorize.html', {'dagr_list': dagr_list, 'category_list': category_list})

def categorizeSubmission(request):
    if request.method == 'POST':
        category = request.POST.get('category-selection')
        dagrid = request.POST.get('dagr-selection', None)

        print("selected category was = {}".format(category))
        print("selected dagr id was = {}".format(dagrid))

        # assign the category to the dagr in Category table
        assignCategory(category, dagrid)


        return HttpResponseRedirect(reverse('success'))

    return HttpResponse("Failed")

def keywordSubmission(request):
    if request.method == 'POST':
        keyword = request.POST.get('keyword-selection')
        dagrid = request.POST.get('dagr-selection', None)

        # make sure the dagr with the guid doesn't already have the keyword associated with it
        if not isKeywordDuplicate(dagrid, keyword):
            insertKeywords(dagrid, keyword)

        return HttpResponseRedirect(reverse('success'))

    return HttpResponse("Failed")



def assignCategory(category, dagrid):
    # make connection to database
    conn = MySQLdb.connect(host="localhost",
                           user="root",
                           passwd="password",
                           db="Documents")
    x = conn.cursor()

    x.execute("""SELECT * FROM Categories""")

    dagrwithcat_exists = False
    for row in x:
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




class DeletePageView(TemplateView):
    template_name = 'delete.html'

class FindOrphansPageView(TemplateView):
    template_name = 'findorphans.html'

class HtmlParserPageView(TemplateView):
    template_name = 'htmlparser.html'

class InsertPageView(TemplateView):
    template_name = 'insert.html'

def insert(request):
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

    conn.close()

    return render(request, 'insert.html', {'dagr_list': dagr_list})


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
        dagrid = request.POST.get('dagr-selection')
        keywords = request.POST.get('keywords').lower()     # convert everything to lowercase

        keyword_list = keywords.split(',')
        keyword_list = [x.strip() for x in keyword_list]    # strip out leading and trailing whitespace

        # extract all relevant metadata from file
        guid, localpath, lastmod, owner, extract_size = extractLocalMetadata(filename, size, local_homedir)


        # make sure this file is not already a DAGR. If it ISN'T then allow upload

        # if the file is a duplicate, find it's GUID
        if isDAGRDuplicate(filename, localpath):
            guid = findGUID(filename, localpath)
        else:   # if the file is NOT a duplicate, insert it into the DB
            insertIntoDB(guid, filename, localpath, size, lastmod, owner, dagrid)

        # insert each keyword for this dagr
        for k in keyword_list:
            # make sure the dagr with the guid doesn't already have the keyword associated with it
            if not isKeywordDuplicate(guid, k):
                insertKeywords(guid, k)

        return HttpResponseRedirect(reverse('success'))

    return HttpResponse("Failed")


def findGUID(filename, localpath):
    # make connection to database
    conn = MySQLdb.connect(host="localhost",
                           user="root",
                           passwd="password",
                           db="Documents")
    x = conn.cursor()
    # submit query for getting all DAGRs
    x.execute("""SELECT * FROM DAGR""")

    # go through rows of DAGR table to find guid for the filename
    for row in x:
        # filename in this row
        curr_fname = row[1]
        # localpath in this row
        curr_localpath = row[2]
        if filename == curr_fname and localpath == curr_localpath:
            return row[0]


def isKeywordDuplicate(guid, keyword):
    # make connection to database
    conn = MySQLdb.connect(host="localhost",
                           user="root",
                           passwd="password",
                           db="Documents")
    x = conn.cursor()

    # submit query for getting all DAGRs
    x.execute("""SELECT * FROM keywords""")

    for row in x:
        # guid in this row
        curr_guid = row[1]
        # curr keyword
        curr_keyword = row[0]

        if guid == curr_guid and keyword == curr_keyword:
            return True

    return False

def isDAGRDuplicate(filename, localpath):
    # make connection to database
    conn = MySQLdb.connect(host="localhost",
                           user="root",
                           passwd="password",
                           db="Documents")
    x = conn.cursor()

    # submit query for getting all DAGRs
    x.execute("""SELECT * FROM DAGR""")

    # check to see if the DAGR already exists
    for row in x:
        # filename in this row
        curr_fname = row[1]
        # localpath in this row
        curr_localpath = row[2]
        if filename == curr_fname and localpath == curr_localpath:
            return True

    return False



def keywordPage(request):
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

    # submit query for getting all Keywords
    y = conn.cursor()
    y.execute("""SELECT DISTINCT * FROM keywords""")

    # create dictionary of keywords
    keyword_list = {}

    for row in y:
        print("row = {}".format(row))
        keyword_list[row[0]] = row[1]

    conn.close()

    return render(request, 'keywordPage.html', {'dagr_list': dagr_list, 'keyword_list': keyword_list})


def insertKeywords(guid, keyword):
    guid = str(guid)
    conn = MySQLdb.connect(host="localhost",
                           user="root",
                           passwd="password",
                           db="Documents")
    x = conn.cursor()

    x.execute(""" INSERT INTO keywords VALUES (%s, %s) """, (keyword, guid))
    conn.commit()

    x.execute("""SELECT * FROM keywords""")
    for row in x:
        print(row)
    conn.close()
    print("keywords saved for this dagr!")



def extractLocalMetadata(filename, size, local_homedir):

    size_c = str(size) + "c"

    # clean the filename up
    filename_proc = subprocess.Popen(["bash", "filenamecleanup.sh", filename], stdout=subprocess.PIPE)
    cleaned_filename = ""
    for row in filename_proc.stdout:
        cleaned_filename = row.decode("utf-8").rstrip()


    # run pathfinder script to get the paths
    proc = subprocess.Popen(["bash", "pathfinder.sh", cleaned_filename, size_c, local_homedir], stdout=subprocess.PIPE)


    path_list = []
    # extract all the paths pathfinder returns you
    for row in proc.stdout:
        path_list.append(row.decode("utf-8").rstrip())


    # if there is more than one path in path list, choose the first one
    if len(path_list) != 1:
        localpath = path_list[0]
    elif len(path_list) == 0:
        raise Exception('Why is there no path?')
    else:
        localpath = path_list[0]

    return extractWithPath(localpath)


def extractWithPath(localpath):
    # grab metadata using metadataextractor script
    extractor_output = subprocess.Popen(["bash", "metadataextractor.sh", localpath], stdout=subprocess.PIPE)


    for row in extractor_output.stdout:
        extractor_output_combined = row.decode("utf-8")

    extractor_split = extractor_output_combined.split("^^")

    owner = extractor_split[0]
    lastaccess = extractor_split[1].split('.')[0]
    lastmod = extractor_split[2].split('.')[0]
    laststatuschange = extractor_split[3].split('.')[0]
    size = extractor_split[4].split('.')[0]
    filename = extractor_split[5].split('.')[0]

    guid = uuid.uuid4()

    return guid, localpath, lastmod, owner, size



def insertIntoDB(guid, filename, localpath, size, lastmod, owner, parent):

    guid = str(guid)
    conn = MySQLdb.connect(host="localhost",
                           user="root",
                           passwd="password",
                           db="Documents")
    x = conn.cursor()

    x.execute(""" INSERT INTO DAGR VALUES (%s, %s, %s, %s, %s, %s, %s) """,
              (guid, filename, localpath, size, lastmod, owner, parent))
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
        guid = str(request.POST.get('guid'))

        name = str(request.POST.get('name'))
        category = str(request.POST.get('category'))
        path = str(request.POST.get('path'))
        size = str(request.POST.get('size'))
        creationtime = str(request.POST.get('creationtime'))
        creator = str(request.POST.get('creator'))
        modtime = str(request.POST.get('modtime'))
        date = str(request.POST.get('date'))


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