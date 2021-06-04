<?php
session_start();
$err = "";
if (isset($_SESSION['login'])) {
    echo "Success \n";
    session_destroy();
} else {
    header("location: index.php");
    die();
}
?>