#!/usr/bin/env node

var __version__  = '3.2.0';
var __password__ = '123456';
var __hostsdeny__ = []; // var __hostsdeny__ = ['.youtube.com', '.youku.com'];
var __content_type__ = 'image/gif';
var __content__ = '';
var __timeout__ = 20;

var zlib = require('zlib');
var http = require('http');
var https = require('https');
var url = require('url');

var ipaddr = '';
var port = process.env.PORT || 8080;


function message_html(title, banner, detail) {
    var message = "\
<html><head>\
<meta http-equiv='content-type' content='text/html;charset=utf-8'>\
<title>$title</title>\
<style><!--\
body {font-family: arial,sans-serif}\
div.nav {margin-top: 1ex}\
div.nav A {font-size: 10pt; font-family: arial,sans-serif}\
span.nav {font-size: 10pt; font-family: arial,sans-serif; font-weight: bold}\
div.nav A,span.big {font-size: 12pt; color: #0000cc}\
div.nav A {font-size: 10pt; color: black}\
A.l:link {color: #6f6f6f}\
A.u:link {color: green}\
//--></style>\
</head>\
<body text=#000000 bgcolor=#ffffff>\
<table border=0 cellpadding=2 cellspacing=0 width=100%>\
<tr><td bgcolor=#3366cc><font face=arial,sans-serif color=#ffffff><b>Message</b></td></tr>\
<tr><td>&nbsp;</td></tr></table>\
<blockquote>\
<H1>$banner</H1>\
$detail\
<p>\
</blockquote>\
<table width=100% cellpadding=0 cellspacing=0><tr><td bgcolor=#3366cc><img alt='' width=1 height=4></td></tr></table>\
</body></html>";
    return message.replace('$title', title).replace('$banner', banner).replace('$detail', detail);
}


function decode_request(data, callback) {
    var headers_length = (data[0] << 8) + data[1];

    request = Object();
    request.headers = {};
    request.kwargs = {};
    request.body = data.slice(2+headers_length);

    zlib.inflateRaw(data.slice(2, 2+headers_length), function(error, buff) {
        var lines = buff.toString().split("\r\n");
        var request_line_items = lines.shift().split(" ");
        request.method = request_line_items[0];
        request.url = request_line_items[1];
        for (var i = 0; i < lines.length; i++) {
            var line = lines[i];
            var pos = line.indexOf(':');
            if (pos > 0) {
                var key = line.substring(0, pos);
                var value = line.substring(pos+1).trim();
                if (key.toLowerCase().indexOf('x-urlfetch-') == 0) {
                    request.kwargs[key.substring(11).toLowerCase()] = value;
                } else {
                    key = key.replace(/\w[^\-]*/g, function(w){return w.charAt(0).toUpperCase() + w.substr(1).toLowerCase();})
                    request.headers[key] = value;
                }
            }
        }
        if (request.headers.hasOwnProperty('Content-Encoding')
            && request.headers['Content-Encoding'] == 'deflate') {
            zlib.inflateRaw(request.body, function(error, buff) {
                request.body = buff;
                request.headers['Content-Length'] = request.body.length.toString();
                delete request.headers['Content-Encoding'];
                callback(request);
            });
        } else {
            callback(request);
        }
    });
}

function buffer_xorbit(buff, bit) {
    var data = new Buffer(buff.length);
    for (var i = 0; i < data.length; i++) {
        data.writeUInt8(buff[i] ^ bit, i);
    }
    return data;
}


function application(req, res) {
    console.log('INFO - [' + new Date().toLocaleString('en', {hour12: false}).replace(/\s*GMT\+.+$/, '') + '] ' + req.connection.remoteAddress + ':' + req.connection.remotePort + ' "' + req.method + ' ' + req.url + ' ' + req.httpVersion +'" - -')

    var content_length = parseInt(req.headers['content-length']);

    if (!(content_length > 0)) {
        res.writeHead(302, {'Location': 'http://www.google.com/'});
        res.end();
        return;
    }

    var buffers = [];

    req.on('data', function(chunk) {
        buffers.push(chunk);
    });

    req.on('end', function() {
        var data = Buffer.concat(buffers);
        var bit = __password__.charCodeAt(0);
        decode_request(data, function(request) {
            console.log('INFO - [' + new Date().toLocaleString('en', {hour12: false}).replace(/\s*GMT\+.+$/, '') + '] ' + req.connection.remoteAddress + ':' + req.connection.remotePort + ' "' + request.method + ' ' + request.url + ' HTTP/1.1" - -')

            // console.log(request);
            if (!request.kwargs.hasOwnProperty('password') || __password__ != request.kwargs['password']) {
                if (!res.headersSent) {
                    res.writeHead(403, {'Content-Type': __content_type__});
                }
                res.write('HTTP/1.0 403\r\n\r\n' + message_html('403 Forbidden', 'Wrong Password', 'please edit proxy.ini'));
                res.end();
                return;
            }

            var option = url.parse(request.url);

            if (__hostsdeny__.length) {
                var hostname = option.hostname;
                if (__hostsdeny__.filter(function(i) {return i==hostname.substring(hostname.length-i.length);}).length) {
                    var content = 'HTTP/1.0 403\r\n\r\n' + message_html('403 Forbidden', 'hostsdeny matched(' + hostname + ')',  request.url)
                    if (!res.headersSent) {
                        res.writeHead(200, {'Content-Type': __content_type__});
                    }
                    res.write(buffer_xorbit(new Buffer(content), bit));
                    res.end();
                    return;
                }
            }

            var httplib = option.protocol == 'https:' ? https : http;
            option.path = option.path ? option.path : option.pathname+(option.search ? option.search : '');
            option.method = request.method;
            option.headers = request.headers;
            var http_request = httplib.request(option, function(response) {
                if (!res.headersSent) {
                    res.writeHead(200, {'Content-Type': __content_type__});
                }
                var content = 'HTTP/1.1 ' + response.statusCode + '\r\n';
                for (var key in response.headers) {
                    value = response.headers[key];
                    key = key.replace(/\w+/g, function(w){return w.charAt(0).toUpperCase() + w.substr(1).toLowerCase();});
                    if (key == "Transfer-Encoding") {
                        continue;
                    }
                    if (key == 'Set-Cookie') {
                        value = value.toString().replace(/,([^ =]+(?:=|$))/g, '\r\nSet-Cookie: $1');
                    }
                    content += key + ': ' + value + '\r\n';
                }
                content += '\r\n';
                // console.log('header content=\r\n[' + content + ']');
                res.write(buffer_xorbit(new Buffer(content), bit));
                response.on('data',function(chunk){
                        res.write(buffer_xorbit(chunk, bit));
                    });
                response.on('end',function(){
                        res.end();
                    });
                }).on('error', function(error) {
                    if (!res.headersSent) {
                        res.writeHead(200, {'Content-Type': __content_type__});
                    }
                    content = "HTTP/1.0 502\r\n\r\n" + message_html('502 Urlfetch Error', 'http.request error: ' + error,  request.url)
                    res.write(buffer_xorbit(new Buffer(content), bit));
                    res.end();
                });
                http_request.setTimeout(__timeout__ * 1000, function() {
                    http_request.abort();
                    if (!res.headersSent) {
                        res.writeHead(200, {'Content-Type': __content_type__});
                    }
                    content = "HTTP/1.0 502\r\n\r\n" + message_html('502 Urlfetch Error', 'http.request timeout',  request.url)
                    res.write(buffer_xorbit(new Buffer(content), bit));
                    res.end();
                });
                http_request.on('error', function(error) {
                    if (!res.headersSent) {
                        res.writeHead(200, {'Content-Type': __content_type__});
                    }
                    content = "HTTP/1.0 502\r\n\r\n" + message_html('502 Urlfetch Error', 'http.request ' + error,  request.url)
                    res.write(buffer_xorbit(new Buffer(content), bit));
                    res.end();
                });
                if (request.body.length) {
                    // console.log('body: [' + request.body.toString() + ']');
                    http_request.write(request.body);
                }
                http_request.end();
            });
    });
}

console.log('local node application serving at ' + ipaddr + ':' + port);
http.createServer(application).listen(port, ipaddr);
