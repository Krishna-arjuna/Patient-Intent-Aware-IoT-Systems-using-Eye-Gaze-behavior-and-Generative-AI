import { getState } from "./api.js";

async function updateDashboard() {
    try {
        const data = await getState();

        console.log("STATE:", data);

        // Example UI update
        const grid = document.getElementById("patients-grid");
        if (!grid) return;

        grid.innerHTML = `
            <div style="color:#00d4ff;font-family:monospace">
                Gaze: ${data.latest.gaze} <br>
                Blink Count: ${data.latest.blink_count} <br>
                Blink Rate: ${data.latest.blink_rate}
            </div>
        `;
    } catch (e) {
        console.error("Dashboard error:", e);
    }
}

function logout() {
    window.location.href = "/login";
}
window.logout = logout;

setInterval(updateDashboard, 2000);
updateDashboard();

const activePatient = localStorage.getItem("activePatient");

console.log("ACTIVE PATIENT:", activePatient);