import sys
sys.path.append('/usr/src/app/polarpipeline')

from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from wtforms import StringField, SubmitField
from flask_wtf import FlaskForm
from datetime import datetime
import urllib.parse
import configparser
import pandas as pd
import subprocess
import psycopg2
import hashlib
import time
import yaml
import svg
import ast
import os
import re


app = Flask(__name__)
app.config.from_object("polardb.config.Config")
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    active = db.Column(db.Boolean(), default=True, nullable=False)

    def __init__(self, email):
        self.email = email

db_config = {
    'dbname': 'polardbDB',
    'user': 'polardbPL',
    'password': 'polardbpswd',
    'host': 'db',
    'port': '5432',
}


@app.route('/')
def index():
    return redirect(url_for('guys'))
    return render_template('index.html')

    
@app.route('/guys')
def guys():
    output_directories = ['/mnt/synology3/polar_pipeline', '/mnt/synology4/polar_pipeline']
    merged_fastq_directories = ['/mnt/synology3/MERGED_fastq.gz_files', '/mnt/synology4/MERGED_fastq.gz_files']
    data_folder_directories = ['/mnt/synology3/data.P24', '/mnt/synology4/data.P24']
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        cursor.execute("SELECT run_uid, run_path FROM runs")
        stored_runs = cursor.fetchall()
        # print(stored_runs)
        for run in stored_runs:
            if not os.path.isdir(run[1]):
                cursor.execute("DELETE FROM runs WHERE run_uid = %s", (run[0],))

        cursor.execute("SELECT fastq_uid, fastq_path FROM fastqs")
        stored_fastqs = cursor.fetchall()
        # print(stored_runs)
        for fastq in stored_fastqs:
            if not os.path.isfile(fastq[1]):
                cursor.execute("DELETE FROM fastqs WHERE fastq_uid = %s", (fastq[0],))
        
        # cursor.execute("SELECT g.uid, g.initials FROM guys g LEFT JOIN runs r ON g.uid = r.guy_uid WHERE r.run_uid IS NULL")
        # empty_guys = cursor.fetchall()
        # for guy in empty_guys:
        #     cursor.execute("DELETE FROM guys WHERE uid = %s", (guy[0],))

        pattern = r'[A-Za-z]{2,3}_\d{7}'
        datepattern = r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}'
        seq_datepattern = r'\d{4}-\d{2}-\d{2}'
        
        for output_directory in output_directories:
            for item in os.listdir(output_directory):
                matches = re.findall(pattern, item)
                if matches:
                    initials, id = matches[0].split('_')
                    # print(initials, id)
                    t2t = 'GRCh38'
                    if 't2t' in item.lower():
                        t2t = 'T2T'
                    datematches = re.findall(datepattern, item)
                    seq_dates = re.findall(seq_datepattern, item)
                    # print(seq_dates, min(seq_dates))
                    seq_date = datetime.strptime(min(seq_dates), '%Y-%m-%d')

                    pipe_tmstmp = datematches[0]
                    date_obj = datetime.strptime(pipe_tmstmp, '%Y-%m-%d_%H-%M-%S')

                    # Check if uid already exists in the database
                    cursor.execute("SELECT uid FROM guys WHERE initials = %s AND id = %s", (initials, id))
                    existing_uid = cursor.fetchone()
                    
                    if not existing_uid:
                        seq_dates = re.findall(seq_datepattern, item)
                        # print(seq_dates, min(seq_dates))
                        seq_date = datetime.strptime(min(seq_dates), '%Y-%m-%d')
                        # If uid not in guys, insert into the database
                        cursor.execute("INSERT INTO guys (initials, id, seq_date) VALUES (%s, %s, %s) RETURNING uid", (initials, id, seq_date))
                        existing_uid = cursor.fetchone()

                    cursor.execute("SELECT run_uid FROM runs WHERE guy_uid = %s AND run_name = %s AND run_path = %s AND run_type = %s AND run_time = %s", (existing_uid, item, os.path.join(output_directory, item), t2t, date_obj))
                    existing_run_uid = cursor.fetchone()

                    if not existing_run_uid:
                        cursor.execute("INSERT INTO runs (guy_uid, run_name, run_path, run_type, run_time) VALUES (%s, %s, %s, %s, %s)", (existing_uid, item, os.path.join(output_directory, item), t2t, date_obj))

        for merged_fastq_directory in merged_fastq_directories:
            for root, dirs, files in os.walk(merged_fastq_directory):
                for file in files:
                    matches = re.findall(pattern, file)
                    if matches:
                        path = os.path.join(root, file)
                        initials, id = matches[0].split('_')

                        cursor.execute("SELECT uid FROM guys WHERE initials = %s AND id = %s", (initials, id))
                        existing_uid = cursor.fetchone()

                        if not existing_uid:
                            seq_dates = re.findall(seq_datepattern, item)
                            # If uid not in guys, insert into the database
                            cursor.execute("INSERT INTO guys (initials, id, seq_date) VALUES (%s, %s, %s) RETURNING uid", (initials, id, seq_date))
                            existing_uid = cursor.fetchone()
                        
                        cursor.execute("SELECT fastq_uid FROM fastqs WHERE guy_uid = %s AND fastq_name = %s AND fastq_path = %s", (existing_uid, file, path))
                        existing_fastq_uid = cursor.fetchone()

                        if not existing_fastq_uid:
                            cursor.execute("INSERT INTO fastqs (guy_uid, fastq_name, fastq_path) VALUES (%s, %s, %s)", (existing_uid, file, path))

        for data_folder in data_folder_directories:
            for dir in os.listdir(data_folder):
                matches = re.findall(pattern, dir)
                if matches:
                    path = os.path.join(data_folder, dir)
                    initials, id = matches[0].split('_')

                    cursor.execute("SELECT uid FROM guys WHERE initials = %s AND id = %s", (initials, id))
                    existing_uid = cursor.fetchone()    

                    if not existing_uid:
                        seq_dates = re.findall(seq_datepattern, item)
                        # If uid not in guys, insert into the database
                        cursor.execute("INSERT INTO guys (initials, id, seq_date) VALUES (%s, %s, %s) RETURNING uid", (initials, id, seq_date))
                        existing_uid = cursor.fetchone()
                    
                    cursor.execute("SELECT folder_uid FROM data_folders WHERE guy_uid = %s AND folder_name = %s AND folder_path = %s", (existing_uid, dir, path))
                    existing_fastq_uid = cursor.fetchone()

                    if not existing_fastq_uid:
                        cursor.execute("INSERT INTO data_folders (guy_uid, folder_name, folder_path) VALUES (%s, %s, %s)", (existing_uid, dir, path))


        # Commit the changes to the database
        conn.commit()
        
        # Retrieve all entries from the database
        cursor.execute("SELECT * FROM guys ORDER BY initials")
        select = cursor.fetchall()
        entries = []
        for line in select:

            try:
                cursor.execute("SELECT DISTINCT run_type FROM runs WHERE guy_uid = %s", (line[0],))
                all_run_types = cursor.fetchall()
                all_run_types_flat = [run_type[0] for run_type in all_run_types]
                cursor.execute("SELECT COUNT(*) FROM runs WHERE guy_uid = %s;", (line[0],))
                num_runs_for_guy = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM fastqs WHERE guy_uid = %s;", (line[0],))
                num_fastqs_for_guy = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM data_folders WHERE guy_uid = %s;", (line[0],))
                num_data_folders_for_guy = cursor.fetchone()[0]
                # print(all_run_types_flat)
            except Exception as e:
                return f"Error: {e}"
            entry = []
            entry.append(line[0])
            entry.append(line[1])
            entry.append(line[2])
            entry.append(num_runs_for_guy)
            if 'GRCh38' in all_run_types_flat:
                entry.append('checked')
            else:
                entry.append('')
            if 'T2T' in all_run_types_flat:
                entry.append('checked')
            else:
                entry.append('')
            entry.append(num_fastqs_for_guy)
            entry.append(line[3].strftime('%Y-%m-%d'))
            entry.append(num_data_folders_for_guy)
            entries.append(entry)

        # print(entries)
        cursor.close()
        conn.close()

        guylen = len(entries)

        return render_template('guys.html', entries=entries, guylen=guylen)
    except Exception as e:
        return f"Error: {e}"

@app.route('/guys/<uid>')
def info(uid):
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    fastq_pattern = r'MERGED_.*'
    try:
        cursor.execute("SELECT initials, id FROM guys WHERE uid = %s", (uid,))
        fetched = cursor.fetchone()
        # print(fetched)
        initials, id = [result for result in fetched]

        runs = []
        cursor.execute("SELECT run_name, run_type, run_time, run_path FROM runs WHERE guy_uid = %s ORDER BY run_time", (uid,))
        fetched = cursor.fetchall()
        cursor.execute("SELECT fastq_name, fastq_path FROM fastqs WHERE guy_uid = %s", (uid,))
        fetched_fastqs = cursor.fetchall()
        # print(fetched)
        for result in fetched:
            run = []
            run.append(result[0])
            run.append(result[1])
            run.append(result[2].strftime('%Y-%m-%d %H:%M:%S'))
            run.append(result[3])
            matched_fastqs = []
            matches = re.findall(fastq_pattern, result[0])
            for fetched_fastq in fetched_fastqs:
                if matches[0].replace('_T2T', '').replace('_sorted', '') in fetched_fastq[0]:
                    matched_fastqs.append(fetched_fastq[1])
            run.append(matched_fastqs)
            runs.append(run)
        # print(runs)
            
        fastqs=[]
        for result in fetched_fastqs:
            fastq = []
            fastq.append(result[0])
            fastq.append(result[1])
            fastqs.append(fastq)

        cursor.execute("SELECT folder_name, folder_path FROM data_folders WHERE guy_uid = %s", (uid,))
        fetched = cursor.fetchall()
        data_folders=[]
        for result in fetched:
            data_folder = []
            data_folder.append(result[0])
            data_folder.append(result[1])
            data_folders.append(data_folder)

    except Exception as e:
        return f"Error: {e}"
    return render_template('info.html', initials=initials, id=id, runs=runs, fastqs=fastqs, data_folders=data_folders)

@app.route('/runsummary', methods=['POST'])
def runsummary():
    run_path = request.form['value']
    print(run_path)
    summary = []
    try:
        for line in open(os.path.join(run_path, '0_nextflow/run_summary.txt')):
            summary.append(line.strip().split('\t'))
        # print(summary)
        return summary
    except Exception as e:
        error_message = 'An error occurred: ' + str(e)
        return jsonify({'error': error_message}), 500

@app.route('/config')
def config():
    with open('/usr/src/app/polardb/paths.yaml', 'r') as yaml_file:
        data = yaml.load(yaml_file, Loader=yaml.FullLoader)
    pipeline_paths = data['pipeline_paths']
    merged_paths = data['merged_paths']
    data_paths = data['data_paths']
    return render_template('config.html', pipeline_paths=pipeline_paths, merged_paths=merged_paths, data_paths=data_paths)