<?php
// Enable error reporting
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

// Include the database connection file
include('db.php');

// Check if the request is a POST method
if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    // Collect form data
    $firstname = $_POST['firstname'];
    $lastname = $_POST['lastname'];
    $email = $_POST['email'];
    $phone_number = $_POST['phone_number'];
    $password = $_POST['password'];
    $confirm_password = $_POST['signupConfirmPassword'];

    // Debug: print received form data
    echo "Received Data:<br>";
    echo "First Name: " . $firstname . "<br>";
    echo "Last Name: " . $lastname . "<br>";
    echo "Email: " . $email . "<br>";
    echo "Phone Number: " . $phone_number . "<br>";
    echo "Password: " . $password . "<br>";

    // Validate required fields
    if (empty($firstname) || empty($lastname) || empty($email) || empty($phone_number) || empty($password) || empty($confirm_password)) {
        echo "All fields are required.";
        exit();
    }

    // Check if passwords match
    if ($password !== $confirm_password) {
        echo "Passwords do not match.";
        exit();
    }

    // Hash the password
    $hashedPassword = password_hash($password, PASSWORD_BCRYPT);

    // Check if the email is already registered
    $checkUser = $conn->prepare("SELECT * FROM users WHERE email = ?");
    $checkUser->bind_param("s", $email);
    $checkUser->execute();
    $result = $checkUser->get_result();

    if ($result->num_rows > 0) {
        echo "User already exists.";
    } else {
        // Prepare the SQL query to insert user data
        $stmt = $conn->prepare("INSERT INTO users (firstname, lastname, email, phone_number, password) VALUES (?, ?, ?, ?, ?)");
        $stmt->bind_param("sssss", $firstname, $lastname, $email, $phone_number, $hashedPassword);

        // Execute the query and check if the insertion is successful
        if ($stmt->execute()) {
            echo "User registered successfully.";
        } else {
            echo "Error: " . $stmt->error;
        }

        $stmt->close();
    }

    $checkUser->close();
}

$conn->close();
?>
