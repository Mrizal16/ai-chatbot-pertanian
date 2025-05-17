<?php
header("Access-Control-Allow-Origin: *");
header("Content-Type: application/json");
header("Access-Control-Allow-Methods: POST, GET");

$host = "localhost";
$user = "root";
$pass = "";
$dbname = "chatbot_pertanian";

$conn = new mysqli($host, $user, $pass, $dbname);
if ($conn->connect_error) {
    die(json_encode(["error" => "Koneksi database gagal"]));
}

$action = $_GET['action'] ?? '';

if ($action == 'new_session') {
    $session_name = $_POST['session_name'] ?? 'Sesi Baru';
    $stmt = $conn->prepare("INSERT INTO sessions (session_name) VALUES (?)");
    $stmt->bind_param("s", $session_name);
    $stmt->execute();
    echo json_encode(["success" => true, "session_id" => $conn->insert_id]);
} elseif ($action == 'save_message') {
    $session_id = $_POST['session_id'];
    $sender = $_POST['sender'];
    $message = $_POST['message'];
    $stmt = $conn->prepare("INSERT INTO messages (session_id, sender, message) VALUES (?, ?, ?)");
    $stmt->bind_param("iss", $session_id, $sender, $message);
    $stmt->execute();
    echo json_encode(["success" => true]);
} elseif ($action == 'get_sessions') {
    $result = $conn->query("SELECT * FROM sessions ORDER BY created_at DESC");
    $sessions = $result->fetch_all(MYSQLI_ASSOC);
    echo json_encode($sessions);
} elseif ($action == 'get_messages') {
    $session_id = $_GET['session_id'];
    $stmt = $conn->prepare("SELECT * FROM messages WHERE session_id = ? ORDER BY created_at");
    $stmt->bind_param("i", $session_id);
    $stmt->execute();
    $result = $stmt->get_result();
    $messages = $result->fetch_all(MYSQLI_ASSOC);
    echo json_encode($messages);
} // Hapus sesi dan pesan terkait
elseif ($action == 'delete_session') {
    $session_id = $_POST['session_id'] ?? null;
    if ($session_id) {
        $stmt1 = $conn->prepare("DELETE FROM messages WHERE session_id = ?");
        $stmt1->execute([$session_id]);

        $stmt2 = $conn->prepare("DELETE FROM sessions WHERE id = ?");
        $stmt2->execute([$session_id]);

        echo json_encode(["status" => "deleted"]);
    } else {
        echo json_encode(["error" => "Missing session_id"]);
    }
}

 else {
    echo json_encode(["error" => "Aksi tidak valid"]);
}
$conn->close();
?>
