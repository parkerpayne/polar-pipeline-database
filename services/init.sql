CREATE TABLE guys (
    uid SERIAL PRIMARY KEY,
    initials  TEXT NOT NULL,
    id      TEXT NOT NULL,
    seq_date DATE NOT NULL
);

CREATE TABLE runs (
    run_uid SERIAL PRIMARY KEY,
    guy_uid INTEGER REFERENCES guys(uid),
    run_name TEXT NOT NULL,
    run_path TEXT NOT NULL,
    run_type TEXT NOT NULL,
    run_time TIMESTAMP NOT NULL
);

CREATE TABLE fastqs (
    fastq_uid SERIAL PRIMARY KEY,
    guy_uid INTEGER REFERENCES guys(uid),
    fastq_name TEXT NOT NULL,
    fastq_path TEXT NOT NULL
);

CREATE TABLE data_folders (
    folder_uid SERIAL PRIMARY KEY,
    guy_uid INTEGER REFERENCES guys(uid),
    folder_name TEXT NOT NULL,
    folder_path TEXT NOT NULL
);

CREATE TABLE lines_t2t (
    file_id SERIAL PRIMARY KEY,
    guy_uid INTEGER REFERENCES guys(uid),
    intersection TEXT NOT NULL,
    lines INTEGER NOT NULL
);

-- INSERT INTO guys(
--         uid, initials, id
--     ) values (
--         '3a8bec201c', 'PP', '4280049'
--     );

-- INSERT INTO guys(
--         uid, initials, id
--     ) values (
--         '498bec201c', 'RP', '3819945'
--     );