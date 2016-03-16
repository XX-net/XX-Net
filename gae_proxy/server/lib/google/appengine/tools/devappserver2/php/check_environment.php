<?php
/**
 * Check if the PHP environment is acceptable for the development server. If
 * not, return non-zero and print the reason to stdout.
 */
if (!function_exists('bccomp')) {
  echo "The PHP runtime requires the \"bccomp\" function, which is not ";
  echo "defined.\n";
  echo "If you built PHP using \"configure\" then please rebuild with:\n";
  echo ' ./configure  --enable-bcmath';
  exit(1);
}

if (function_exists('memcache_add')) {
  echo 'The PHP runtime cannot be run with the "Memcache" PECL extension ' .
       'installed';
  exit(1);
}

if (class_exists('Memcached')) {
  echo 'The PHP runtime cannot be run with the "Memcached" PECL extension ' .
       'installed';
  exit(1);
}
