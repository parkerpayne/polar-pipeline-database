import sys
sys.path.append('/usr/src/app/polarpipeline')
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import psycopg2
import yaml
import time
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

cached_pipeline_state = []
cached_merged_state = []
cached_data_state = []

@app.route('/guys')
def guys():
    global cached_pipeline_state
    global cached_merged_state
    global cached_data_state
    with open('/usr/src/app/polardb/paths.yaml', 'r') as yaml_file:
        data = yaml.load(yaml_file, Loader=yaml.FullLoader)
    output_directories = data['pipeline_paths']
    merged_fastq_directories = data['merged_paths']
    data_folder_directories = data['data_paths']
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

        cursor.execute("SELECT folder_uid, folder_path FROM data_folders")
        stored_folders = cursor.fetchall()
        # print(stored_runs)
        for data_folder in stored_folders:
            if not os.path.isdir(data_folder[1]):
                cursor.execute("DELETE FROM data_folders WHERE folder_uid = %s", (data_folder[0],))
        
        cursor.execute("""
            SELECT g.uid, g.initials 
            FROM guys g 
            LEFT JOIN runs r ON g.uid = r.guy_uid 
            LEFT JOIN fastqs f ON g.uid = f.guy_uid 
            LEFT JOIN data_folders df ON g.uid = df.guy_uid 
            WHERE r.guy_uid IS NULL AND f.guy_uid IS NULL AND df.guy_uid IS NULL
        """)
        empty_guys = cursor.fetchall()

        for guy in empty_guys:
            cursor.execute("DELETE FROM guys WHERE uid = %s", (guy[0],))

        pattern = r'[A-Za-z]{2,3}_\d{7}'
        datepattern = r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}'
        seq_datepattern = r'\d{4}-\d{2}-\d{2}'
        
        current_pipeline_state = []
        for output_directory in output_directories:
            current_pipeline_state.append(os.listdir(output_directory))
        
        current_merged_state = []
        for merged_fastq_directory in merged_fastq_directories:
            for root, dirs, files in os.walk(merged_fastq_directory):
                current_merged_state.append(files)
        
        current_data_state = []
        for data_folder_directory in data_folder_directories:
            current_data_state.append(os.listdir(data_folder_directory))

        if current_pipeline_state != cached_pipeline_state:
            cached_pipeline_state = current_pipeline_state
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
    

        if current_merged_state != cached_merged_state:
            cached_merged_state = current_merged_state
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

        if current_data_state != cached_data_state:
            cached_data_state = current_data_state
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
    

def report_finder(start_dir):
    report_array = []
    for item in os.listdir(start_dir):
        if os.path.isdir(os.path.join(start_dir, item)):
            if 'pass' not in item.lower() and 'fail' not in item.lower():
                report_array = report_array + report_finder(os.path.join(start_dir, item))
    for item in os.listdir(start_dir):
        if os.path.isfile(os.path.join(start_dir, item)) and 'report' in item.lower() and item.endswith('html'):
            return [(item.replace('.html', ''), os.path.join(start_dir, item))]
    return report_array

def sort_by_basename(item):
    return os.path.basename(item[1])

@app.route('/guys/<uid>')
def info(uid):
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    fastq_pattern = r'MERGED_.*'
    try:
        cursor.execute("SELECT uid, initials, id FROM guys WHERE uid = %s", (uid,))
        fetched = cursor.fetchone()
        # print(fetched)
        uid, initials, id = [result for result in fetched]

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
                if matches[0].split('_T2T')[0].split('_sorted')[0] in fetched_fastq[0]:
                    matched_fastqs.append(fetched_fastq[1])
            other_run_name = ''
            if not matched_fastqs:
                moved_id_pattern = r'MERGED_[A-Za-z]{2,3}_\d{7}'
                date_pattern = r'_\d{4}-\d{2}-\d{2}'
                moved_name_matches = re.findall(moved_id_pattern, result[0])
                if moved_name_matches:
                    id_to_move = moved_name_matches[0].replace('MERGED', '')
                    work_in_progress = result[0].replace(id_to_move, '')
                    dates_in_name = re.findall(date_pattern, work_in_progress)
                    if dates_in_name:
                        last_date = dates_in_name[-1]
                        other_run_name = work_in_progress.replace(last_date, last_date+id_to_move)
            if other_run_name:
                matched_fastqs = []
                matches = re.findall(fastq_pattern, other_run_name)
                for fetched_fastq in fetched_fastqs:
                    if matches[0].split('_T2T')[0].split('_sorted')[0] in fetched_fastq[0]:
                        matched_fastqs.append(fetched_fastq[1])
            run.append(matched_fastqs)
            runs.append(run)
        # print(runs)
            
        fastqs=[]
        for result in fetched_fastqs:
            fastq = []
            fastq.append(result[0])
            fastq.append(result[1])
            fastq_stats = os.stat(result[1])
            fastq.append(str(round(fastq_stats.st_size/(1024*1024*1024), 2)))
            fastqs.append(fastq)

        cursor.execute("SELECT folder_name, folder_path FROM data_folders WHERE guy_uid = %s", (uid,))
        fetched = cursor.fetchall()
        data_folders=[]
        for result in fetched:
            data_folder = []
            data_folder.append(result[0])
            data_folder.append(result[1])
            reports = report_finder(result[1])
            data_folder.append(reports)
            data_folders.append(data_folder)

        # print(data_folders)        

    except Exception as e:
        return f"Error: {e}"
    return render_template('info.html', initials=initials, id=id, runs=runs, fastqs=sorted(fastqs, key=sort_by_basename), data_folders=sorted(data_folders, key=sort_by_basename), uid=uid)

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

@app.route('/<path:filepath>')
def open_html(filepath):
    if 'report' in filepath and filepath.endswith('.html'):
        return send_file('/'+filepath, mimetype='text/html', as_attachment=False)
    else:
        return 'Error: file not found or invalid'

@app.route('/config')
def config():
    with open('/usr/src/app/polardb/paths.yaml', 'r') as yaml_file:
        data = yaml.load(yaml_file, Loader=yaml.FullLoader)
    pipeline_paths = data['pipeline_paths']
    merged_paths = data['merged_paths']
    data_paths = data['data_paths']
    return render_template('config.html', pipeline_paths=pipeline_paths, merged_paths=merged_paths, data_paths=data_paths)

@app.route('/update_paths', methods=['POST'])
def update_paths():
    path_type = request.json.get("path_type")
    path_list = request.json.get("path_list")
    # print(path_type)
    # print(path_list)
    invalid_paths = [path for path in path_list if not os.path.isdir(path) and not path=='']
    if invalid_paths:
        error_message = f'Invalid path(s): {", ".join(invalid_paths)}'
        return jsonify({'error': error_message}), 400

    with open('/usr/src/app/polardb/paths.yaml', 'r') as yaml_file:
        data = yaml.load(yaml_file, Loader=yaml.FullLoader)
    pipeline_paths = data['pipeline_paths']
    merged_paths = data['merged_paths']
    data_paths = data['data_paths']

    match path_type:
        case 'Path':
            pipeline_paths = path_list
        case 'Merged':
            merged_paths = path_list
        case 'Data':
            data_paths = path_list
    
    with open('/usr/src/app/polardb/paths.yaml', 'w') as yaml_file:
        yaml.dump({'pipeline_paths': pipeline_paths, 'merged_paths': merged_paths, 'data_paths': data_paths}, yaml_file)

    return 'success'

@app.route('/export', methods=['POST'])
def export():
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    guy_dict = {}
    to_export = request.json
    placeholders = ','.join(['%s'] * len(to_export))
    sql = f"SELECT * FROM guys WHERE uid IN ({placeholders})"
    cursor.execute(sql, to_export)
    guys = cursor.fetchall()
    sorted_guys = []
    for uid in to_export:
        for guy in guys:
            if int(uid) == int(guy[0]):
                sorted_guys.append(guy)
                break
    # print(sorted_guys)
    for guy in sorted_guys:
        # print(guy)
        guy_info = guy[1]+'_'+guy[2]
        cursor.execute('SELECT * FROM runs WHERE guy_uid=%s', (guy[0],))
        runs = cursor.fetchall()
        runs_results = []
        for run in runs:
            # run_result = []
            # run_result.append(run[3])
            # runs_results.append(run_result)
            runs_results.append(run[3])
        cursor.execute('SELECT * FROM fastqs WHERE guy_uid=%s', (guy[0],))
        fastqs = cursor.fetchall()
        fastq_results = []
        for fastq in fastqs:
            fastq_results.append(fastq[3])
        cursor.execute('SELECT * FROM data_folders WHERE guy_uid=%s', (guy[0],))
        data_folders = cursor.fetchall()
        data_results = []
        for data in data_folders:
            data_results.append(data[3])
        # print(guy_info)
        # print(runs_results)
        # print(fastq_results)
        # print(data_results)
        lengths = [len(runs_results), len(fastq_results), len(data_results)]
        array_height = max(lengths)
        # print(guy_info, lengths, array_height)

        guy_array = []
        for h in range(array_height):
            row = []
            for col in [[guy_info], runs_results, fastq_results, data_results]:
                if h < len(col):
                    row.append(col[h])
                elif col == [guy_info]:
                    row.append(guy_info)
                else:
                    row.append('')
            guy_array.append(row)
        
        guy_dict[guy_info] = guy_array

    if not os.path.isdir('/usr/src/temp'):
        os.mkdir('/usr/src/temp')
    with open('/usr/src/temp/guysexport.tsv', 'w') as opened:
        opened.write('Guy ID\tRuns\tMERGED Fastqs\tData Folders\n')
        for guy in guy_dict:
            for row in guy_dict[guy]:
                opened.write('\t'.join(row)+'\n')

    return send_file('/usr/src/temp/guysexport.tsv', as_attachment=True)

class toDoListGuy:
    def __init__(self, identifier, needs_merged=True, needs_pipeline=True,
                 needs_t2t_pipeline=True, needs_fastqs_zipped=True, needs_data_to_syn=True,
                 needs_zipped_merge_to_syn=True):
        self.identifier = identifier
        self.needs_merged = needs_merged
        self.needs_pipeline = needs_pipeline
        self.needs_t2t_pipeline = needs_t2t_pipeline
        self.needs_fastqs_zipped = needs_fastqs_zipped
        self.needs_data_to_syn = needs_data_to_syn
        self.needs_zipped_merge_to_syn = needs_zipped_merge_to_syn
    
    def ready_to_delete(self):
        if self.needs_merged:
            return False
        if self.needs_pipeline:
            return False
        if self.needs_t2t_pipeline:
            return False
        if self.needs_fastqs_zipped:
            return False
        if self.needs_data_to_syn:
            return False
        if self.needs_zipped_merge_to_syn:
            return False
        return True
    
    def priority(self):
        priority = 0
        if self.needs_merged:
            priority += 1
        if self.needs_pipeline:
            priority += 1
        if self.needs_t2t_pipeline:
            priority += 1
        if self.needs_fastqs_zipped:
            priority += 1
        if self.needs_data_to_syn:
            priority += 1
        if self.needs_zipped_merge_to_syn:
            priority += 1
        return priority

    def print(self):
        print('identifier=',self.identifier,end=' ')
        print('needs_merged=',self.needs_merged,end=' ')
        print('needs_pipeline=',self.needs_pipeline,end=' ')
        print('needs t2t_pipeline=',self.needs_t2t_pipeline,end=' ')
        print('needs_fastqs_zipped=',self.needs_fastqs_zipped,end=' ')
        print('needs_data_to_syn=',self.needs_data_to_syn,end=' ')
        print('needs_zipped_merge_to_syn=',self.needs_zipped_merge_to_syn,end='\n')

def izipped(path):
    zipped = False
    for item in os.listdir(path):
        if os.path.isdir(os.path.join(path, item)) and 'report' not in item.lower() and 'pod5' not in item.lower():
            return izipped(os.path.join(path, item))
        elif os.path.isfile(os.path.join(path, item)):
            if 'fastq' in item:
                if item.endswith('.gz'):
                    return True
                else:
                    return False
    return zipped

def sort_by_priority(item):
    return item.priority()

@app.route('/prom')
def prom():
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    gentlemen = {}
    pattern = r'[A-Za-z]{2,3}_\d{7}'
    try:
        for thing in os.listdir('/mnt/prom'):
            if not os.path.isdir(os.path.join('/mnt/prom',thing)): continue
            matches = re.findall(pattern, thing)
            if matches and 'bad' not in thing.lower() and 'incomplete' not in thing.lower() and 'copy' not in thing.lower():
                # print('guy found:', matches[0], flush=True)
                initials, _id = matches[0].split('_')
                cursor.execute("SELECT COUNT(r.*) FROM runs r JOIN guys g ON r.guy_uid = g.uid WHERE g.initials = %s AND g.id = %s AND r.run_type = %s", (initials, _id, 'GRCh38'))
                runs = cursor.fetchone()
                cursor.execute("SELECT COUNT(r.*) FROM runs r JOIN guys g ON r.guy_uid = g.uid WHERE g.initials = %s AND g.id = %s AND r.run_type = %s", (initials, _id, 'T2T'))
                t2t_runs = cursor.fetchone()
                cursor.execute("SELECT COUNT(f.*) FROM fastqs f JOIN guys g ON f.guy_uid = g.uid WHERE g.initials = %s AND g.id = %s", (initials, _id))
                fastqs = cursor.fetchone()
                cursor.execute("SELECT COUNT(d.*) FROM data_folders d JOIN guys g ON d.guy_uid = g.uid WHERE g.initials = %s AND g.id = %s", (initials, _id))
                datas = cursor.fetchone()
                # print('queries done for', matches[0])
                gentlemen[matches[0]] = toDoListGuy(matches[0], needs_zipped_merge_to_syn=not bool(int(fastqs[0])), needs_pipeline=not bool(int(runs[0])), needs_t2t_pipeline=not bool(int(t2t_runs[0])), needs_data_to_syn=not bool(int(datas[0])), needs_fastqs_zipped=not izipped(os.path.join('/mnt/prom', thing)))
                # gentlemen[matches[0]] = toDoListGuy(matches[0], needs_zipped_merge_to_syn=bool(int(fastqs[0])), needs_pipeline=bool(int(runs[0])), needs_data_to_syn=bool(int(datas[0])))
                # print('created class for', matches[0])

    except Exception as e:
        conn.rollback()
        print(e)

    for file in os.listdir('/mnt/prom/1.4.MERGED_fastq'):
        matches = re.findall(pattern, file)
        if matches:
            identification = matches[0]
            if identification in gentlemen:
                gentlemen[identification].needs_merged = False

    gentlemen_list = []
    delete_list = []
    for item in gentlemen:
        if not gentlemen[item].ready_to_delete():
            gentlemen_list.append(gentlemen[item])
        else:
            delete_list.append(gentlemen[item])


    # print(os.listdir('/mnt/prom'))
    return render_template('prom.html', gentlemen_list=sorted(gentlemen_list, key=sort_by_priority)[::-1], delete_list=delete_list)

def count_t2t_lines(path):
    count = 0
    for line in open(path, 'r'):
        if line.strip().startswith('#'):
            continue
        count += 1
    return count

def sort_by_date(item):
    return item[3]

@app.route('/t2t')
@app.route('/t2t/')
def t2t():
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("SELECT run_path, guy_uid FROM runs WHERE run_type = %s", ('T2T',))
    results = cursor.fetchall()
    guys = []
    for result in results:
        row = []
        path, uid = result
        cursor.execute("SELECT initials, id, seq_date FROM guys WHERE uid = %s", (uid,))
        guy_info = cursor.fetchone()
        initials, id, seq_date = guy_info
        linecounts = {}
        intersect_path = ''
        for item in os.listdir(path):
            if item.endswith('intersect'):
                intersect_path = os.path.join(path, item)
        if intersect_path:
            for file in os.listdir(intersect_path):
                if file.endswith('.vcf'):
                    if 'del_assay_MORE.vcf' in file:
                        linecounts['del_assay_MORE'] = count_t2t_lines(os.path.join(intersect_path, file))
                    elif 'AZFabc_protein.vcf' in file:
                        linecounts['AZFabc_protein'] = count_t2t_lines(os.path.join(intersect_path, file))
                    elif 'AZFabc.vcf' in file:
                        linecounts['AZFabc'] = count_t2t_lines(os.path.join(intersect_path, file))
        row.append(uid)
        row.append(initials)
        row.append(id)
        row.append(seq_date)
        row.append(linecounts)
        present = False
        for item in guys:
            if row[0] == item[0]:
                present = True
        if present == False and linecounts:
            guys.append(row)

    
    
    return render_template('t2t.html', guys=sorted(guys, key=sort_by_date)[::-1])

@app.route('/t2t/<uid>')
def t2t_info(uid):
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute('SELECT run_path FROM runs WHERE guy_uid = %s AND run_type = %s', (uid, 'T2T',))
    result = cursor.fetchone()[0]
    del_assay = []
    del_assay_header = ''
    azfabc_prot = []
    azfabc_prot_header = ''
    for guy_path in os.listdir(result):
        if 'intersect' in guy_path and os.path.isdir(os.path.join(result, guy_path)):
            intersect_path = os.path.join(result, guy_path)
            for file in os.listdir(intersect_path):
                if file.endswith('del_assay_MORE.vcf'):
                    for line in open(os.path.join(intersect_path, file)):
                        if not line.startswith("##"):
                            if line.startswith("#CHROM"):
                                del_assay_header = line
                            else:
                                del_assay.append(line.strip().split('\t'))
                elif file.endswith('AZFabc_protein.vcf'):
                    for line in open(os.path.join(intersect_path, file)):
                        if not line.startswith("##"):
                            if line.startswith("#CHROM"):
                                azfabc_prot_header = line
                            else:
                                azfabc_prot.append(line.strip().split('\t'))
    # print(del_assay)
    # print(azfabc_prot)
    return render_template('t2t_info.html', del_assay=(del_assay_header, del_assay), azfabc_prot=(azfabc_prot_header, azfabc_prot))