<?php
// Database connection configuration
$servername = "localhost"; // Assuming you're using localhost
$username = "root";        // Your MySQL username
$password = "";            // Your MySQL password (leave blank if none)
$dbname = "user_database"; // The name of the database you created

// Create connection
$conn = new mysqli($servername, $username, $password, $dbname);

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}
?>
