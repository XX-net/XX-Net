#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'moonshawdo@gamil.com'


import re
import os
import subprocess
import sys
import urllib2
import math


current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath( os.path.join(current_path, os.pardir, os.pardir))
data_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir, 'data'))
data_gae_proxy_path = os.path.join(data_path, 'gae_proxy')
python_path = os.path.abspath( os.path.join(root_path, 'python27', '1.0'))

noarch_lib = os.path.abspath( os.path.join(python_path, 'lib', 'noarch'))
sys.path.append(noarch_lib)


from config import config
import ip_utils

# This code functions:
# read ip range string in code
# merge over lapped range
# filter out bad ip range

# Then reproduce good format file


# Support format:
# # Comment (#）
#
# range seperater:
# range can seperate by (,) or(|) or new line
#
# Single rang format: ：
# "xxx.xxx.xxx-xxx.xxx-xxx"
# "xxx.xxx.xxx."
# "xxx.xxx.xxx.xxx/xx"
# "xxx.xxx.xxx.xxx"



def PRINT(strlog):
    print (strlog)

def print_range_list(ip_range_list):
    for ip_range in ip_range_list:
        begin = ip_range[0]
        end = ip_range[1]
        print ip_utils.ip_num_to_string(begin), ip_utils.ip_num_to_string(end)


def parse_range_string(input_lines):
    ip_range_list = []

    ip_lines_list = re.split("\r|\n", input_lines)
    for raw_line in ip_lines_list:
        raw_s = raw_line.split("#")
        context_line = raw_s[0]

        context_line = context_line.replace(' ', '')

        ips = re.split(",|\|", context_line)
        for line in ips:
            if len(line) == 0:
                #print "non line:", line
                continue
            begin, end = ip_utils.split_ip(line)
            if ip_utils.check_ip_valid(begin) == 0 or ip_utils.check_ip_valid(end) == 0:
                PRINT("ip format is error,line:%s, begin: %s,end: %s" % (line, begin, end))
                continue
            nbegin = ip_utils.ip_string_to_num(begin)
            nend = ip_utils.ip_string_to_num(end)
            ip_range_list.append([nbegin,nend])
            #print begin, end

    ip_range_list.sort()

    return ip_range_list

def merge_range(input_ip_range_list):
    output_ip_range_list = []
    range_num = len(input_ip_range_list)

    last_begin = input_ip_range_list[0][0]
    last_end = input_ip_range_list[0][1]
    for i in range(1,range_num):
        ip_range = input_ip_range_list[i]
        begin = ip_range[0]
        end = ip_range[1]

        #print "now:",ip_utils.ip_num_to_string(begin), ip_utils.ip_num_to_string(end)

        if begin > last_end + 2:
            #print "add:",ip_utils.ip_num_to_string(begin), ip_utils.ip_num_to_string(end)
            output_ip_range_list.append([last_begin, last_end])
            last_begin = begin
            last_end = end
        else:
            print "merge:", ip_utils.ip_num_to_string(last_begin), ip_utils.ip_num_to_string(last_end), ip_utils.ip_num_to_string(begin), ip_utils.ip_num_to_string(end)
            if end > last_end:
                last_end = end

    output_ip_range_list.append([last_begin, last_end])

    return output_ip_range_list

def filter_ip_range(good_range, bad_range):
    out_good_range = []
    bad_i = 0

    bad_begin, bad_end = bad_range[bad_i]

    for good_begin, good_end in good_range:
        while True:
            if good_begin > good_end:
                PRINT("bad good ip range when filter:%s-%s"  % (ip_utils.ip_num_to_string(good_begin), ip_utils.ip_num_to_string(good_end)))
                assert(good_begin < good_end)
            if good_end < bad_begin:
                # case:
                #     [  good  ]
                #                   [  bad  ]
                out_good_range.append([good_begin, good_end])
                break
            elif bad_end < good_begin:
                # case:
                #                   [  good  ]
                #     [   bad   ]
                bad_i += 1
                bad_begin, bad_end = bad_range[bad_i]
                continue
            elif good_begin <= bad_begin and good_end <= bad_end:
                # case:
                #     [   good    ]
                #           [   bad   ]
                PRINT("cut bad ip case 1:%s - %s" % (ip_utils.ip_num_to_string(bad_begin), ip_utils.ip_num_to_string(good_end)))
                if bad_begin - 1 > good_begin:
                    out_good_range.append([good_begin, bad_begin - 1])
                break
            elif good_begin >= bad_begin and good_end == bad_end:
                # case:
                #           [   good   ]
                #     [      bad       ]
                PRINT("cut bad ip case 2:%s - %s" % (ip_utils.ip_num_to_string(good_begin), ip_utils.ip_num_to_string(bad_end)))

                bad_i += 1
                bad_begin, bad_end = bad_range[bad_i]
                break
            elif good_begin >= bad_begin and good_end > bad_end:
                # case:
                #           [   good   ]
                #     [    bad  ]
                PRINT("cut bad ip case 3:%s - %s" % (ip_utils.ip_num_to_string(good_begin), ip_utils.ip_num_to_string(bad_end)))
                good_begin = bad_end + 1
                bad_i += 1
                bad_begin, bad_end = bad_range[bad_i]
                continue
            elif good_begin <= bad_begin and good_end >= bad_end:
                # case:
                #     [     good     ]
                #         [  bad  ]
                out_good_range.append([good_begin, bad_begin - 1])
                PRINT("cut bad ip case 4:%s - %s" % (ip_utils.ip_num_to_string(bad_begin), ip_utils.ip_num_to_string(bad_end)))
                good_begin = bad_end + 1
                bad_i += 1
                bad_begin, bad_end = bad_range[bad_i]
                continue
            elif good_begin >= bad_begin and good_end <= bad_end:
                # case:
                #          [good]
                #      [    bad    ]
                PRINT("cut bad ip case 5:%s - %s" % (ip_utils.ip_num_to_string(good_begin), ip_utils.ip_num_to_string(good_end)))
                break
            else:
                PRINT("any case? good:%s-%s bad:%s-%s" % (ip_utils.ip_num_to_string(good_begin), ip_utils.ip_num_to_string(good_end),
                    ip_utils.ip_num_to_string(bad_begin), ip_utils.ip_num_to_string(bad_end)))
                assert( False )

    return out_good_range

def download_apic(filename):
    url = 'http://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest'
    try:
        data = subprocess.check_output(['wget', url, '-O-'])
    except (OSError, AttributeError):
        print >> sys.stderr, "Fetching data from apnic.net, "\
                             "it might take a few minutes, please wait..."
        data = urllib2.urlopen(url).read()

    with open(filename, "w") as f:
        f.write(data)
    return data


def generage_range_from_apnic(input):

    cnregex = re.compile(r'^apnic\|(?:cn)\|ipv4\|[\d\.]+\|\d+\|\d+\|a\w*$',
                         re.I | re.M )
    cndata = cnregex.findall(input)

    results = []

    for item in cndata:
        unit_items = item.split('|')
        starting_ip = unit_items[3]
        num_ip = int(unit_items[4])

        cidr = 32 - int(math.log(num_ip, 2))

        results.append("%s/%s" % (starting_ip, cidr))

    return "\n".join(results)

def load_bad_ip_range():
    file_name = "delegated-apnic-latest.txt"
    apnic_file = os.path.join(config.DATA_PATH, file_name)
    if not os.path.isfile(apnic_file):
        download_apic(apnic_file)

    with open(apnic_file, "r") as inf:
        apnic_lines = inf.read()

    bad_ip_range_lines = generage_range_from_apnic(apnic_lines)

    sepcial_bad_ip_range_lines  = """
    130.211.0.0/16          #Empty ip range, no route to it.
    255.255.255.255/32      #for algorithm
    """
    return bad_ip_range_lines + sepcial_bad_ip_range_lines


def generate_ip_range():
    # load input good ip range
    file_name = "ip_range.txt"
    input_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_name)
    with open(input_file, "r") as inf:
        input_good_range_lines = inf.read()

    ip_range_list = parse_range_string(input_good_range_lines)
    ip_range_list = merge_range(ip_range_list)
    PRINT("Good ip range:\n")
    print_range_list(ip_range_list)

    if False:
        input_bad_ip_range_lines = load_bad_ip_range()
        bad_range_list = parse_range_string(input_bad_ip_range_lines)
        bad_range_list = merge_range(bad_range_list)
        PRINT("Bad ip range:\n")
        print_range_list(ip_range_list)

        ip_range_list = filter_ip_range(ip_range_list, bad_range_list)
        PRINT("Output ip range:\n")
        print_range_list(ip_range_list)

    # write out
    output_file = os.path.join(config.DATA_PATH, file_name)
    fd = open(output_file, "w")
    for ip_range in ip_range_list:
        begin = ip_range[0]
        end = ip_range[1]
        #print ip_utils.ip_num_to_string(begin), ip_utils.ip_num_to_string(end)
        fd.write(ip_utils.ip_num_to_string(begin)+ "-" + ip_utils.ip_num_to_string(end)+"\n")

    fd.close()


def test_load():
    print("Begin test load ip_range.txt\n")
    file_name = os.path.join(config.DATA_PATH, "ip_range.txt")
    fd = open(file_name, "r")
    if not fd:
        print "open ip_range.txt fail."
        exit()

    amount = 0
    for line in fd.readlines():
        if len(line) == 0 or line[0] == '#':
            continue
        begin, end = ip_utils.split_ip(line)

        nbegin = ip_utils.ip_string_to_num(begin)
        nend = ip_utils.ip_string_to_num(end)

        num = nend - nbegin
        amount += num
        print ip_utils.ip_num_to_string(nbegin), ip_utils.ip_num_to_string(nend), num

    fd.close()
    print "amount ip:", amount


def main():
    generate_ip_range()
    test_load()


if __name__ == "__main__":
    main()
