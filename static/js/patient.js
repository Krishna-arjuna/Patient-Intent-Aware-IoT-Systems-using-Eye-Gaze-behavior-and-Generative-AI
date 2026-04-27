import { getState } from "./api.js";

async function updatePatient() {
    try {
        const data = await getState();

        document.getElementById("blink-count").innerText =
            data.latest.blink_count;

        document.getElementById("gaze-lbl").innerText =
            data.latest.gaze;

    } catch (e) {
        console.error(e);
    }
}

setInterval(updatePatient, 2000);
updatePatient();