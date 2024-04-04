# Polar Pipeline Database
a viewer for locating and identifying locations of various sequencing related files.

# Introduction
The Polar Pipeline Database is a Flask-based web application designed to provide the user with a quick way to identify patients, as well as the number and location of various intermediate files. It has been packaged into a docker container to provide the simplest user experience.

# Features
- Search patients by initials or ID
- Order results by the number of pipeline outputs, the number of fastq files, the number of data folders (from a nanopore sequencer), first associated date, or by alphabet
- Limit results by the presence or absence of T2T and GRCh38 pipeline outputs
- View specific pages for patients, as well as a brief summary for each identified run, fastq, and data folders
- Point web application to specific folders in which to search for all relevant files

# Installation
1. Install Docker on the host machine.
2. Download the repository to the host machine.
3. Inside the /mnt/ directory, create new directories for all locations you want accessible to the web application. Use either symlinks or use NFS to mount these directories to the location of your files.
4. Build the web application by running ```sudo docker compose up -d``` inside the 'polar-pipeline-database/ directory.
5. Add the directories for various filetypes in the config page.
6. Done! Upon returning to the patients page, the database will be populated with all relevant info, and will only update when changes in the defined directories are detected.