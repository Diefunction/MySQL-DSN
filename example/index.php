<?php
session_start();

$validUser = $_SESSION['login'] === true;
if ($validUser)
{
    header("location: success.php");
    exit();
}

$err = "";

if (isset($_GET['login']))
{
    $user = $_GET['username'];
    $pass = md5($_GET['password']);
    $db = $_GET['db'];
    $dsn = "mysql:host=127.0.0.1;dbname=" . $db;
    $username = "usertest";
    $password = "passtest";
    if (empty($user) || empty($pass))
    {
        $err = "Fields can't be empty!";
    }
    else
    {

        try
        {
            $conn = new PDO($dsn, $username, $password);
        }
        catch(PDOException $e)
        {
            echo "PDOException code: " . $e->getCode();
            exit();
        }
        $sql = "SELECT username, password FROM users WHERE username=? AND password=? ";
        $query = $conn->prepare($sql);
        $query->execute(array(
            $user,
            $pass
        ));

        if ($query->rowCount() >= 1)
        {
            $_SESSION['login'] = true;
            header("location: success.php");
        }
        else
        {
            $err = "Nope.";
        }
    }
}

?>

