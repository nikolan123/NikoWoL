let notyf;
let warningShown = {};
let countdownInterval;

function showWarning(message) {
    if (!notyf) return console.error("Notyf not initialized yet!");
    
    notyf.open({
        type: 'warning',
        message: message,
        duration: 3000,
        background: 'orange',
        icon: false
    });
}

function sendPacket(pcid) {
    const pcElement = document.querySelector(`#pc-${pcid}`);
    const statusText = pcElement.querySelector(".status-text");

    if (statusText.textContent.trim().toLowerCase() === "online") {
        if (warningShown[pcid]) {
            console.log("Sending magic packet anyways");
        } else {
            console.log("Device is already online, showing toast and setting flag");
            showWarning("The device is already online, tap again to send magic packet anyways.");
            warningShown[pcid] = true;
            return;
        }
    } else {
        warningShown[pcid] = false;
    }

    fetch('/send_packet', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ id: pcid })
    })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(({ status, body }) => {
            if (status === 500) {
                throw new Error(status + ", " + (body.error || "Internal Server Error"));
            } else if (!status.toString().startsWith("2")) {
                throw new Error("Response code: " + status);
            }

            console.log("Sent magic packet:", body);
            notyf.success("Sent magic packet");
        })
        .catch(error => {
            console.log("Request failed: " + error.message);
            notyf.error("Request failed: " + error.message);
        });
}

function checkDeviceStatus(pcid) {
    const pcElement = document.querySelector(`#pc-${pcid}`);
    const statusText = pcElement.querySelector(".status-text");
    const statusLED = pcElement.querySelector(".status-led");
    
    fetch(`/check_status?id=${pcid}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(({ status, body }) => {
            if (!status.toString().startsWith("2")) {
                throw new Error(status + ", " + (body.error || "Unexpected Error"));
            }

            console.log("Response for " + pcid + ": " + JSON.stringify(body));
            if (body.status === "up") {
                statusText.textContent = "online";
                statusLED.className = statusLED.className.replace(/bg-\w+-500/, "bg-green-500");
            } else {
                statusText.textContent = "offline";
                statusLED.className = statusLED.className.replace(/bg-\w+-500/, "bg-red-500");
            }
        })
        .catch(error => {
            console.log("Request failed: " + error.message);
            statusText.textContent = "error";
            statusLED.className = statusLED.className.replace(/bg-\w+-500/, "bg-stone-500");
        });
}

function deleteDevice(pcid) {
    const deviceElement = document.querySelector(`#pc-${pcid}`);

    fetch(`/delete_device`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ id: pcid })
    })
    .then(response => response.json().then(data => ({ status: response.status, body: data })))
    .then(({ status, body }) => {
        if (status === 500) {
            throw new Error(status + ", " + (body.error || "Internal Server Error"));
        } else if (!status.toString().startsWith("2")) {
            throw new Error("Response code: " + status);
        }

        console.log("Deleted device:", body);
        notyf.success("Deleted device");

        // animation
        if (document.querySelectorAll("[id^='pc-']").length === 1) {
            const nodevicesfound = document.getElementById("nodevicesfound");
            nodevicesfound.style.transform = "scale(0)";
            nodevicesfound.style.transition = "transform 0.5s";
            nodevicesfound.style.display = "block";
            setTimeout(() => {
                nodevicesfound.style.transform = "scale(1)";
            }, 0);
        }
        deviceElement.style.transition = "transform 0.5s, opacity 0.5s, margin 0.5s";
        deviceElement.style.transform = "scale(0.5)";
        deviceElement.style.opacity = "0";
        deviceElement.style.margin = `0 0 -${deviceElement.offsetHeight}px 0`;

        setTimeout(() => {
            deviceElement.remove();
            checkAllDevices();
        }, 500);
    })
    .catch(error => {
        console.log("Request failed: " + error.message);
        notyf.error("Request failed: " + error.message);
    });
}

function moveDevice(pcid, direction) {
    fetch(`/move_device`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ id: pcid, direction: direction })
    })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(({ status, body }) => {
            if (status === 500 || status === 400) {
                throw new Error(status + ", " + (body.error || "Internal Server Error"));
            } else if (!status.toString().startsWith("2")) {
                throw new Error("Response code: " + status);
            }

            console.log("Moved device:", body);
            const deviceElement = document.querySelector(`#pc-${pcid}`);
            const parentElement = deviceElement.parentElement;

            if (direction === "up" && deviceElement.previousElementSibling) {
                const previousElement = deviceElement.previousElementSibling;

                const prevStyles = getComputedStyle(previousElement);
                const deviceStyles = getComputedStyle(deviceElement);
                const moveAmount =
                    previousElement.offsetHeight +
                    parseInt(prevStyles.marginBottom || 0) +
                    parseInt(deviceStyles.marginTop || 0);

                deviceElement.style.transition = "transform 0.3s";
                previousElement.style.transition = "transform 0.3s";
                deviceElement.style.transform = `translateY(-${moveAmount}px)`;
                previousElement.style.transform = `translateY(${moveAmount}px)`;

                setTimeout(() => {
                    parentElement.insertBefore(deviceElement, previousElement);
                    deviceElement.style.transition = "";
                    previousElement.style.transition = "";
                    deviceElement.style.transform = "";
                    previousElement.style.transform = "";
                }, 300);
            } else if (direction === "down" && deviceElement.nextElementSibling) {
                const nextElement = deviceElement.nextElementSibling;

                const deviceStyles = getComputedStyle(deviceElement);
                const nextStyles = getComputedStyle(nextElement);
                const moveAmount =
                    deviceElement.offsetHeight +
                    parseInt(deviceStyles.marginBottom || 0) +
                    parseInt(nextStyles.marginTop || 0);

                deviceElement.style.transition = "transform 0.3s";
                nextElement.style.transition = "transform 0.3s";
                deviceElement.style.transform = `translateY(${moveAmount}px)`;
                nextElement.style.transform = `translateY(-${moveAmount}px)`;

                setTimeout(() => {
                    parentElement.insertBefore(nextElement, deviceElement);
                    deviceElement.style.transition = "";
                    nextElement.style.transition = "";
                    deviceElement.style.transform = "";
                    nextElement.style.transform = "";
                }, 300);
            }
        })
        .catch(error => {
            console.log("Request failed: " + error.message);
            notyf.error("Request failed: " + error.message);
        });
}

function checkAllDevices() {
    const deviceElements = document.querySelectorAll("[id^='pc-']");
    if (deviceElements.length === 0) {
        const noDevicesElement = document.getElementById("nodevicesfound");
        noDevicesElement.style.display = "block";
    }
    deviceElements.forEach(device => {
        const pcid = device.id.split('-')[1];
        checkDeviceStatus(pcid);
    });
}

function startCountdown(seconds) {
    // clear previous countdown
    if (countdownInterval) {
        clearInterval(countdownInterval);
    }

    let countdownElement = document.getElementById("refresh-countdown");
    countdownElement.textContent = seconds;

    countdownInterval = setInterval(() => {
        seconds--;
        countdownElement.textContent = seconds;

        if (seconds <= 0) {
            clearInterval(countdownInterval);
            countdownInterval = null; // Set to null to indicate no active interval
        }
    }, 1000);
}

document.addEventListener("DOMContentLoaded", function () {
    notyf = new Notyf();

    /*check for url arguments*/
    const urlParams = new URLSearchParams(window.location.search);
    const added = urlParams.get('added');
    if (added) {
        notyf.success("Device added successfully");
        const addedDiv = document.getElementById(`pc-${added}`);
        if(!addedDiv) window.location.replace('/edit');
        history.replaceState(null, "", "/edit");
        /* zoom in animation */
        addedDiv.style.transform = "scale(0.5)";
        addedDiv.style.display = "flex";
        setTimeout(() => {
            addedDiv.style.transition = "transform 0.3s";
            addedDiv.style.transform = "scale(1)";
        }, 0);
    }
    const edited = urlParams.get('edited');
    if (edited) {
        notyf.success("Device edited successfully");
        const addedDiv = document.getElementById(`pc-${edited}`);
        if(!addedDiv) window.location.replace('/edit');
        history.replaceState(null, "", "/edit");
    }

    startCountdown(5);
    checkAllDevices();

    setInterval(() => {
        checkAllDevices();
        startCountdown(5);
    }, 5000);
});