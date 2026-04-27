const BASE = "http://127.0.0.1:5000";

export async function getState() {
    const res = await fetch(`${BASE}/api/state`);
    return await res.json();
}

export async function loginUser(data) {
    const res = await fetch(`${BASE}/api/login`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data)
    });
    return await res.json();
}