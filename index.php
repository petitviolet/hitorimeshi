<?php
header('Access-Control-Allow-Origin:*');
header("Content-Type: text/xml");

echo('<?xml version="1.0" encoding="UTF-8" ?>');
echo('<test><title>ぼっちーむapi</title><result>');
if(isset($_GET['input']) && is_numeric($_GET['input'])){
  printf("%d", $_GET['input'] * 5);
}else{
  printf("Error. input data is 'null', or not Numeric.");
}
echo('</result></test>');
// echo('<page><name>Google</name><url>http://google.co.jp</url></page></test>');
?>
