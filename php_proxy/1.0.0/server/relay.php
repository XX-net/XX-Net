<?php

$__relay__ = 'http://goagent.app.com/index.php';
$__hosts__ = array('goagent.app.com');
$__timeout__ = 16;


function php_getallheaders() {
    $headers = array();
    foreach ($_SERVER as $name => $value) {
        if (substr($name, 0, 5) == 'HTTP_')  {
            $name = join('-', array_map('ucfirst', explode('_', strtolower(substr($name, 5)))));
            $headers[$name] = $value;
        } else if ($name == "CONTENT_TYPE") {
            $headers["Content-Type"] = $value;
        } else if ($name == "CONTENT_LENGTH") {
            $headers["Content-Length"] = $value;
        }
    }
    return $headers;
}


function header_function($ch, $header) {
    if (stripos($header, 'Transfer-Encoding:') === false) {
        header($header, false);
    }
    return strlen($header);
}


function write_function($ch, $content) {
    echo $content;
    return strlen($content);
}


function main() {
    $timeout = $GLOBALS['__timeout__'];
    $method = $_SERVER['REQUEST_METHOD'] ;
    $url = $GLOBALS['__relay__'];
    $host = $GLOBALS['__hosts__'][array_rand($GLOBALS['__hosts__'])];
    $headers = php_getallheaders();
    $body = isset($GLOBALS['HTTP_RAW_POST_DATA']) ? $GLOBALS['HTTP_RAW_POST_DATA'] : '';

    $urlparts = parse_url($url);

    if ($body && !isset($headers['Content-Length'])) {
        $headers['Content-Length'] = strval(strlen($body));
    }
    if (isset($headers['Connection'])) {
        $headers['Connection'] = 'close';
    }
    $headers['Host'] = $urlparts['host'];

    $header_array = array();
    foreach ($headers as $key => $value) {
        $header_array[] = "$key: $value";
    }

    $curl_opt = array();

    switch (strtoupper($method)) {
        case 'HEAD':
            $curl_opt[CURLOPT_NOBODY] = true;
            break;
        case 'GET':
            break;
        case 'POST':
            $curl_opt[CURLOPT_POST] = true;
            $curl_opt[CURLOPT_POSTFIELDS] = $body;
            break;
        default:
            $curl_opt[CURLOPT_CUSTOMREQUEST] = $method;
            $curl_opt[CURLOPT_POSTFIELDS] = $body;
            break;
    }

    $curl_opt[CURLOPT_HTTPHEADER] = $header_array;
    $curl_opt[CURLOPT_RETURNTRANSFER] = true;
    $curl_opt[CURLOPT_BINARYTRANSFER] = true;

    $curl_opt[CURLOPT_HEADER]         = false;
    $curl_opt[CURLOPT_HEADERFUNCTION] = 'header_function';
    $curl_opt[CURLOPT_WRITEFUNCTION]  = 'write_function';

    $curl_opt[CURLOPT_FAILONERROR]    = false;
    $curl_opt[CURLOPT_FOLLOWLOCATION] = false;

    $curl_opt[CURLOPT_CONNECTTIMEOUT] = $timeout;
    $curl_opt[CURLOPT_TIMEOUT]        = $timeout;

    $curl_opt[CURLOPT_SSL_VERIFYPEER] = false;
    $curl_opt[CURLOPT_SSL_VERIFYHOST] = false;

    $new_url = preg_replace('@//[^/]+@', "//$host", $url);
    if ($_SERVER['QUERY_STRING']) {
        $new_url .= '?' . $_SERVER['QUERY_STRING'];
    }

    //var_dump(array('new_url' => $new_url, 'headers' => $headers, 'curl_opt' => $curl_opt));
    //exit(0);

    $ch = curl_init($new_url);
    curl_setopt_array($ch, $curl_opt);
    $ret = curl_exec($ch);
    $errno = curl_errno($ch);

    if ($errno) {
        if (!headers_sent()) {
            header('HTTP/1.1 502 Gateway Error');
            header('Content-Type: text/plain');
        }
        echo "502 Urlfetch Error\r\nPHP Urlfetch Error: curl($errno)\r\n"  . curl_error($ch);
    }
    curl_close($ch);
}

main();
