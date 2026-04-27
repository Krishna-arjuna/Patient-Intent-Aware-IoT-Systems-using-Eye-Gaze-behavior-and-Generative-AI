import { loginUser } from "./api.js";

async function login() {
    const username = document.getElementById("username").value;

    const res = await fetch("/api/login", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            username: username,
            role: selectedRole   // 🔥 FIXED
        })
    });

    const data = await res.json();

    console.log("LOGIN RESPONSE:", data);

    if (data.success) {
        if (data.role === "admin") {
            window.location.href = "/admin";
        } else {
            window.location.href = "/dashboard";
        }
    } else {
        alert("Login failed");
    }

    logout=() => {
        localStorage.removeItem("token");
        window.location.href = "/login";
    }
}