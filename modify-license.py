#!/bin/python

#
# Copyright 2014 Gedare Bloom (gedare@rtems.org)
#
# This file's license is 2-clause BSD.

##
## Replace license terms in C source and header files
##

import getopt
import os
import re
import string
import subprocess
import sys

def usage():
    print "\
Usage: modify-license.py -[hm]\n\
  -h --help         print this help\n\
  -m --modify       modify license of identified files\n\
"

# Utilities

def pattern_in_string(pattern, string):
    return re.match(".*"+pattern+".*", string)

def grep(filename, pattern):
    result = [];
    file = open(filename,'r')
    for line in file.readlines():
      if pattern_in_string(pattern, line):
        result.append(string.strip(line))
    file.close()
    return result

# Assume 4 numbers is a year.
def string_contains_year(string):
    return pattern_in_string("[0-9]{4}", string)

def get_name_from_copyright_line(line):
    tokenized = line.strip('.').split(" ")
    for i in range(len(tokenized)):
        token = tokenized[i]
        if string_contains_year(token):
            return (token, ' '.join(tokenized[i+1:]))

def get_copyright_holders_from_file(filename):
    holders = []
    copyright_lines = grep(filename, "Copyright")
    copyright_lines.extend(grep(filename, "COPYRIGHT"))
    for line in copyright_lines:
        holders.append(get_name_from_copyright_line(line))
    return holders

def find_files_with_authors_and_copyrights(root, files, authors, copyright_holders):
    result = []
    for file in files:
        f = os.path.join(root, file)
        # only worry about files with the RTEMS license
        if not grep(f, "The license and distribution"):
            continue
        # Check that all of f's authors are in the authors list
        p = subprocess.Popen(
                "git log --pretty=format:\"%an %ae\" " + f + " | sort -u",
                shell = True,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE
        )
        (out, error) = p.communicate()

        for line in string.split(str(out), "\n"):
            if line and not line in authors:
                print "Did not find author: " + line
                break
        else:
            # Now check that all copyright holders are in copyright_holders
            file_copyright_holders = get_copyright_holders_from_file(f)
            for copyright_tuple in file_copyright_holders:
                if copyright_tuple and not copyright_tuple[1] in copyright_holders:
                    print "Did not find copyright holder: " + copyright_tuple[1]
                    break
            else:
                # Success
                print "file ", f
                print "authors ", out
                print "Copyrights ", file_copyright_holders
                result.append(f)
    return result

# the main event
def modify_license(filename):
    new_license_line = "This file's license is 2-clause BSD as in this distribution's LICENSE.2 file.\n"

    # Read the file into an array, replace first line of existing boilerplate
    # with a new boilerplate, remove other lines that reference the license,
    # and write the array back out to the file.
    f = open(filename, 'r')
    lines = f.readlines()
    f.close()
    for i in range(len(lines)):
        if pattern_in_string("The license and distribution", lines[i]):
            lead_text = lines[i][0:string.find(lines[i], "The")]

            lines[i] = lead_text + new_license_line
            i = i + 1
            while pattern_in_string("LICENSE", lines[i]):
                lines[i] = ""
                i = i + 1
            break
    f = open(filename, 'w')
    for line in lines:
        f.write(line)

# argument processing
def validate_arguments(filename):
    assert os.path.exists(filename), "Invalid path to file: " + filename

def main():
    # default args
    modify = False
    authors = [
            "Gedare Bloom gedare@rtems.org",
            ]
    copyright_holders = [
            "Gedare Bloom",
            "Eugen Leontie",
            ]

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hm",
                ["help", "modify"])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-m", "--modify"):
            modify = True
        else:
            assert False, "unhandled option " + opt

    targets = []
    for root, dirs, files in os.walk(os.getcwd()):
        targets.extend(find_files_with_authors_and_copyrights(
            root, files, authors, copyright_holders))

    print targets
    if modify:
        for f in targets:
            modify_license(f)



# script entry point
if __name__ == "__main__":
  main()
