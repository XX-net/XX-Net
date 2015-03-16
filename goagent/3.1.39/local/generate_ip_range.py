#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ip_utils

__author__ = 'moonshawdo@gamil.com'

# read ip range string
# order it
# merge over lapped
# Then reproduce good format file
# check it.

import re

ip_str_list = '''
1.179.248.0-1.179.248.255
4.3.2.0/24
8.6.48.0-8.6.55.255
8.8.4.0/24
8.8.8.0/24
8.22.56.0-8.22.63.255
8.34.208.0-8.34.223.255
8.35.192.0-8.35.207.255
12.216.80.0-12.216.80.255
24.156.131.0-24.156.131.255
41.206.96.0-41.206.96.255
60.199.175.18-60.199.175.187
61.19.1.30-61.19.1.109
61.219.131.84-61.219.131.251
62.116.207.0-62.116.207.63
62.197.198.193-62.197.198.251
63.211.200.72-63.211.200.79
64.15.112.0-64.15.117.255
64.15.119.0-64.15.126.255
64.18.0.0-64.18.15.255
64.41.221.192-64.41.221.207
64.68.64.64-64.68.64.127
64.68.80.0-64.68.95.255
64.154.178.208-64.154.178.223
64.233.160.0-64.233.191.255
66.102.0.0-66.102.15.255
66.249.64.0-66.249.95.255
70.32.128.0-70.32.159.255
70.90.219.48-70.90.219.55
70.90.219.72-70.90.219.79
72.14.192.0-72.14.255.255
74.125.0.0-74.125.255.255
78.37.100.0/24
80.64.175.0/24
80.228.65.128-80.228.65.191
81.175.29.128-81.175.29.191
84.235.77.0-84.235.77.255
85.182.250.0-85.182.250.255
86.127.118.128-86.127.118.191
93.94.217.0-93.94.217.31
93.94.218.0-93.94.218.31
93.183.211.192-93.183.211.255
94.40.70.0-94.40.70.63
94.200.103.64-94.200.103.71
95.54.196.0/24
106.162.192.148-106.162.192.187
106.162.198.84-106.162.198.123
106.162.216.20-106.162.216.123
108.59.80.0-108.59.95.255
108.170.192.0-108.170.255.255
108.177.0.0-108.177.127.255
111.168.255.20-111.168.255.187
113.197.105.0-113.197.105.255
114.4.41.0/24
118.174.24.0-118.174.27.255
121.78.74.68-121.78.74.123
123.205.250.0-123.205.250.255
123.205.251.68-123.205.251.123
139.175.107.88/24
142.250.0.0-142.251.255.255
162.216.148.0-162.216.151.255
166.90.148.64-166.90.148.79
172.217.0.0-172.217.255.255
172.253.0.0-172.253.255.255
173.194.0.0-173.194.255.255
178.45.251.84-178.45.251.123
178.60.128.1-178.60.128.
192.158.28.0-192.158.31.255
192.178.0.0-192.179.255.255
193.92.133.0-193.92.133.63
193.120.166.64-193.120.166.127
194.78.99.0-194.78.99.255
194.221.68.0-194.221.68.255
195.249.20.192-195.249.20.255
198.108.100.192-198.108.100.207
199.87.241.32-199.87.241.63
199.192.112.0-199.192.115.255
199.223.232.0-199.223.239.255
202.39.143.1-202.39.143.123
202.169.193.0/24
203.66.124.129-203.66.124.251
203.116.165.148-203.116.165.251
203.117.34.148-203.117.34.187
203.165.13.210-203.165.13.251
203.165.14.210-203.165.14.251
203.208.32.0-203.208.63.255
203.211.0.20-203.211.0.59
207.126.144.0-207.126.159.255
207.223.160.0-207.223.175.255
208.21.209.0-208.21.209.15
208.117.224.0-208.117.239.55
208.117.233.0/24
208.117.240.0-208.117.255.255
209.85.128.0-209.85.255.255
209.185.108.128-209.185.108.255
209.245.184.136-209.245.184.143
209.247.159.144-209.247.159.159
210.61.221.148-210.61.221.187
210.139.253.20-210.139.253.251
210.153.73.20-210.153.73.123
213.158.11.0/24
210.158.146.0/24
210.242.125.20-210.242.125.59
210.245.14.0/24
212.188.15.0-212.188.15.255
213.186.229.0-213.186.229.63
213.240.44.0-213.240.44.31
216.33.229.0/24
216.58.208.0/20
216.109.75.80-216.109.75.95
216.239.32.0-216.239.63.255
218.176.242.0-218.176.242.255
218.253.0.0/24
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








