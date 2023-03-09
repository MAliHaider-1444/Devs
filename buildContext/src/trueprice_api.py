from ingestors.ingestor import Ingestion

import trueprice_database as tpdb

import os
import sys
from flask import Flask, flash, request, redirect, url_for, flash, render_template
from werkzeug.utils import secure_filename
import zipfile

app = Flask(__name__)

UPLOAD_FOLDER = './flask_file_upload' # need to decide on best way to deal with this, s3 and/or local?
ALLOWED_EXTENSIONS = {'csv'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ingestor = Ingestion()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# figure out how to get with curl as well
@app.route('/upload', methods=['GET','POST'])
def upload():
    print(f"/upload called", file=sys.stderr)
    if request.method == 'POST':
        print(f"POST: {request}", file=sys.stderr)
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            print(f"Uploading", file=sys.stderr)
            filename = secure_filename(file.filename)
            location = os.path.join(app.config['UPLOAD_FOLDER'], filename) 
            file.save(location)
            ingestor.call_ingestor(location) # deal with result
            #return redirect(url_for('download_file', name=filename)) # fix retrieval link
            return redirect(url_for('upload'))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''

@app.route('/', methods=['GET'])
def hello_world():
    df = None
    #df = tpdb.get_all_data()
    #print(df)
    return f"<p>The new TRUEPrice API, see /upload or /zip</p>{df}"

UPLOAD_FOLDER = os.path.dirname(os.path.realpath(__file__))
ALLOWED_EXTENSIONS = set(['zip','csv'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/zip', methods=['GET','POST'])
def upload_zip():    
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            zip_ref = zipfile.ZipFile(os.path.join(UPLOAD_FOLDER, filename), 'r')
            zip_ref.extractall(UPLOAD_FOLDER + "/unzipped/")
            zip_ref.close()
            # todo - ingestion 
            return redirect(url_for('upload_zip'))
    return render_template('index.html')

if __name__ == "__main__":
    print("Starting")
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(port=5555)