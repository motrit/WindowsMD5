__author__ = 'noway'

import hashlib
import os
import shelve
import time
import sys


#byte size
CHUNK_SIZE = 4096


def md5(file_name):
#Compute md5 of file CONTENTS
#   file_name - path to file (ex. /Users/123/Desktop/file.txt)
#Result:
#   128-bit hex string = md5 hash

    hash_md5 = hashlib.md5()
    with open(file_name) as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), ''):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def update_hash_names(path):
#Produce SHELVE-database with dictionary [HASH:PATH]
#   path - path to the dictionary where all files and subdir should be hashed
#Result:
#   Database named 'names_db'
    names_db = shelve.open('names_db')
    for root, dirs, files in os.walk(path):
        for name in files:
            file = root + "\\" + name
            hash_name = hashlib.md5(file).hexdigest()
            if not names_db.has_key(hash_name):
                names_db[hash_name] = file
    names_db.close()


def compute_dir_hash(path, progress_bar=False, dbname="hash_database"):
#Produce SHELVE-database with dictionary [HASH1:HASH2]
#Where HASH1 is hash of path to file, HASH2 is hash of file contents
#   path - path to the directory to be hashed
#   (optional)progress_bar - set True if you want to see
#       approximate progress (MAY USE ADDITIONAL TIME)
#Result:
#   Database named [path to directory]_db
    print "Updating hash:path table... ",
    update_hash_names(path)
    print "Done"
    counter = 0
    counter_saved = 0
    if progress_bar:
        print "Computing all files in directory " + path + " and subdir..."
        for root, dirs, files in os.walk(path):
            for name in files:
                counter += 1
        print "There are " + str(counter) + " files to be aggregated"
        counter_saved = counter
        counter = 0

    print "Hashing directory " + path + " and all subdir contents"
    dir_db = shelve.open(dbname)

    for root, dirs, files in os.walk(path):
        for name in files:
            if progress_bar:
                counter += 1
                print "\r{0} of {1} completed".format(counter, counter_saved),

            #file_path = root + "/" + name        #MAC OS
            file_path = root + "\\" + name      #WIN

            hash_name = hashlib.md5(file_path).hexdigest()

            try:
                hash_value = md5(file_path)
            except IOError:
                print "Permission Denied to compute md5 hash of " + file_path
            else:
                if not hash_name in dir_db:
                    dir_db[hash_name] = hash_value
    dir_db.close()


def get_path(hash):
    names_db = shelve.open('names_db')
    if hash in names_db:
        ret = names_db[hash]
    else:
        ret = "MISS FILE PATH"
    names_db.close()
    return ret


#Return True if should be excluded
#Return False if should be printed
def verify(path):
    if "Windows\ServiceProfiles\LocalService\AppData\Local\Temp" in path or \
    "Windows\System32\config\systemprofile\AppData\Local\Microsoft\Windows\Temporary Internet Files" in path or \
    "Windows\winsxs\Temp" in path or \
    "Windows\System32\LogFiles" in path or \
    "Windows\System32\WDI\LogFiles" in path or \
    "Windows\System32\winevt\Logs" in path or \
    "Windows\SoftwareDistribution\DataStore\Logs" in path or \
    "Windows\System32\wfp" in path or \
    "Windows\ServiceProfiles" in path or \
    "Windows\winsxs\FileMaps" in path or \
    ".chk" in path.lower() or \
    ".etl" in path.lower() or \
    ".regtrans-ms" in path.lower() or \
    ".crmlog" in path.lower() or \
    "tm.blf" in path.lower() or \
    ".log" in path.lower():
        return True
    else:
        return False


def check_backup(path):
    if "C:\Windows\winsxs\Backup" in path:
        return True
    else:
        return False


def diff_db(old_db_name, new_db_name, log_path, use_mask=False):
    f = open(log_path, 'w')
    old_db = shelve.open(old_db_name)
    new_db = shelve.open(new_db_name)
    backup_data = ""
    if cmp(old_db, new_db) == 0:
        print "\nNo changes in the directory"
    else:
        print "\nThere are some changes in the directory"
        for key in old_db.keys():
            path = get_path(key)
            if use_mask and verify(path):
                new_db[key] = 0
                continue
            if not key in new_db:
                result = "The file " + path + " was removed\n"
                if check_backup(path):
                    backup_data += result
                else:
                    print result
                    f.write(result)
            elif old_db[key] != new_db[key]:
                result = "The file " + path + " was updated\n"
                if check_backup(path):
                    backup_data += result
                else:
                    print result
                    f.write(result)
                new_db[key] = 0
            else:
                new_db[key] = 0
                continue

        for key in new_db.keys():
            path = get_path(key)
            if (use_mask) and (verify(path)):
                new_db[key] = 0
                continue
            if not (new_db[key] == 0):
                result = "The file " + path + " was created\n"
                if check_backup(path):
                    backup_data += result
                else:
                    print result
                    f.write(result)
                new_db[key] = 0
        f.write("\nChanges in backup folder:\n" + backup_data)


def speed_test(path):
    timer = time.time()
    for root, dirs, files in os.walk(path):
        for name in files:
            file_path = root + "\\" + name
            hash_value = md5(file_path)
    print str(time.time() - timer)

def display_usage():
        print "Usage: {0} <command> <options> <arguments>\nRun {0} --help to view available commands".format(sys.argv[0])
        exit(1)
        pass
#compute_dir_hash('C:\Windows', progress_bar=True)
#compute_dir_hash('/Users/pontifik/Desktop/Work', progress_bar=True)
#diff_db('CWindowsold_db', 'CWindows_db', 'log.txt', use_mask=True)
#speed_test('C:\Python27')
#print "DONE"

if __name__ == "__main__":

    if(len(sys.argv) < 2):
        display_usage()

    #sample.py --help
    if (sys.argv[1] == "--help"):
        print "Available commands:" \
              "\n\t--compute <options> <path_to_directory> <output_db_name>(optional)" \
              "\n\t--diff <options> <path_to_db1> <path_to_db2>" \
              "\nAvailable options:" \
              "\n\t--progressbar - to enable progress bar during directory " \
              "\n\t\thash computing, does nothing while diffing" \
              "\n\t--usemask - to exclude unnescessary directories and file " \
              "\n\t\tformats during diff, does nothing while " \
              "computing directory hash"\
              "\nExample:" \
              "\n{0} --compute --progressbar ./ example_db" \
            .format(sys.argv[0])
        exit(1)
        pass

    if (len(sys.argv) < 3):
        display_usage()

    if (sys.argv[1] == "--compute"):
        if sys.argv[2] == "--progressbar":
            if (len(sys.argv) < 4):
                display_usage()
            if (os.path.exists(sys.argv[3]) == False):
                print "No such file or directory to compute hash of... Exiting"
                exit(1)
                pass
            if (len(sys.argv) < 5):
                compute_dir_hash(sys.argv[3], progress_bar=True)
            else:
                compute_dir_hash(sys.argv[3], progress_bar=True, dbname=sys.argv[4])
            exit(1)
            pass
        if (os.path.exists(sys.argv[2]) == False):
            print "No such file or directory to compute hash of... Exiting"
            exit(1)
            pass
        if (len(sys.argv) < 4):
            compute_dir_hash(sys.argv[2])
        else:
            compute_dir_hash(sys.argv[2], dbname=sys.argv[3])
        exit(1)
        pass

    if (sys.argv[1] == "--diff"):
        if sys.argv[2] == "--usemask":
            if (len(sys.argv) < 5):
                display_usage()
            else:
                if ((os.path.exists(sys.argv[3]) == False) or (os.path.exists(sys.argv[4]) == False) ):
                    print "No such database... Exiting"
                    exit(1)
                    pass
                diff_db(sys.argv[3], sys.argv[4], 'log.txt', use_mask=True)
                exit(1)
                pass

        if (len(sys.argv) < 4):
            display_usage()
        if ((os.path.exists(sys.argv[2]) == False) or (os.path.exists(sys.argv[3]) == False) ):
            print "No such database... Exiting"
            exit(1)
            pass
        diff_db(sys.argv[2], sys.argv[3], 'log.txt')
