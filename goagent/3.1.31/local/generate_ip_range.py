#!/usr/bin/env python
# -*- coding: utf-8 -*-
from goagent.local.google_ip import ip_utils

__author__ = 'moonshawdo@gamil.com'

# read ip range string
# order it
# merge over lapped
# Then reproduce good format file
# check it.

import re

ip_str_list = '''
218.189.25.166-218.189.25.187|121.78.74.80-121.78.74.88|178.45.251.84-178.45.251.123|210.61.221.148-210.61.221.187
61.219.131.84-61.219.131.251|202.39.143.84-202.39.143.123|203.66.124.148-203.66.124.251|203.211.0.20-203.211.0.59
60.199.175.18-60.199.175.187|218.176.242.20-218.176.242.251|203.116.165.148-203.116.165.251|203.117.34.148-203.117.34.187
210.153.73.20-210.153.73.123|106.162.192.148-106.162.192.187|106.162.198.84-106.162.198.123|106.162.216.20-106.162.216.123
210.139.253.20-210.139.253.251|111.168.255.20-111.168.255.187|203.165.13.210-203.165.13.251
61.19.1.30-61.19.1.109|74.125.31.33-74.125.31.60|210.242.125.20-210.242.125.59|203.165.14.210-203.165.14.251
216.239.32.0/19
64.233.160.0/19
66.249.80.0/20
72.14.192.0/18
209.85.128.0/17
66.102.0.0/20
74.125.0.0-74.125.31.255
74.125.32.0-74.125.63.255
74.125.64.0-74.125.95.255
74.125.96.0-74.125.127.255
74.125.128.0-74.125.159.255
74.125.160.0-74.125.191.255
74.125.192.0-74.125.223.255
74.125.224.0-74.125.255.255
64.18.0.0/20
207.126.144.0/20
173.194.0.0-173.194.31.255
173.194.32.0-173.194.63.255
173.194.64.0-173.194.95.255
173.194.96.0-173.194.127.255
173.194.128.0-173.194.159.255
173.194.160.0-173.194.191.255
173.194.192.0-173.194.223.255
173.194.224.0-173.194.255.255
1.179.248.0-255
106.162.192.148-187
118.174.24.0-255
118.174.25.0-255
118.174.26.0-255
118.174.27.0-255
121.78.74.68-123
123.205.250.0-255
123.205.251.68-123
178.60.128.1-63
193.120.166.64-127
193.92.133.0-63
194.78.99.0-255
195.249.20.192-255
202.39.143.1-123
203.66.124.129-251
208.117.224.0-208.117.229.255
208.117.230.0-208.117.239.55
208.117.240.0-208.117.255.255
209.85.228.0-255
210.242.125.20-59
212.188.15.0-255
213.186.229.0-63
213.240.44.0-31
218.176.242.0-255
24.156.131.0-255
41.206.96.0-255
62.116.207.0-63
62.197.198.193-251
64.15.112.0-64.15.117.255
64.15.119.0-64.15.126.255
64.233.160.0-255
64.233.168.0-255
64.233.171.0-255
80.228.65.128-191
81.175.29.128-191
84.235.77.0-255
85.182.250.0-255
86.127.118.128-191
93.183.211.192-255
93.94.217.0-31
93.94.218.0-31
94.200.103.64-71
94.40.70.0-63
'''

def PRINT(strlog):
    print (strlog)

def merge_ip_range():
    ip_range_list = []

    ip_lines_list = re.split("\r|\n", ip_str_list)
    for iplines in ip_lines_list:
        if len(iplines) == 0 or iplines[0] == '#':
            #print "non:", iplines
            continue

        ips = re.split(",|\|", iplines)
        for line in ips:
            if len(line) == 0 or line[0] == '#':
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

    # merge range
    ip_range_list_2 = []
    range_num = len(ip_range_list)

    last_begin = ip_range_list[0][0]
    last_end = ip_range_list[0][1]
    for i in range(1,range_num - 1):
        ip_range = ip_range_list[i]

        begin = ip_range[0]
        end = ip_range[1]

        #print "now:",ip_utils.ip_num_to_string(begin), ip_utils.ip_num_to_string(end)

        if begin > last_end + 2:
            #print "add:",ip_utils.ip_num_to_string(begin), ip_utils.ip_num_to_string(end)
            ip_range_list_2.append([last_begin, last_end])
            last_begin = begin
            last_end = end
        else:
            print "merge:", ip_utils.ip_num_to_string(last_begin), ip_utils.ip_num_to_string(last_end), ip_utils.ip_num_to_string(begin), ip_utils.ip_num_to_string(end)
            if end > last_end:
                last_end = end

    ip_range_list_2.append([last_begin, last_end])


    for ip_range in ip_range_list_2:
        begin = ip_range[0]
        end = ip_range[1]
        print ip_utils.ip_num_to_string(begin), ip_utils.ip_num_to_string(end)

    # write out
    fd = open("ip_range.txt", "w")
    for ip_range in ip_range_list_2:
        begin = ip_range[0]
        end = ip_range[1]
        #print ip_utils.ip_num_to_string(begin), ip_utils.ip_num_to_string(end)
        fd.write(ip_utils.ip_num_to_string(begin)+ "-" + ip_utils.ip_num_to_string(end)+"\n")

    fd.close()

merge_ip_range()

def test_load():

    fd = open("ip_range.txt", "r")
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
    print "amount:", amount

#
test_load()








