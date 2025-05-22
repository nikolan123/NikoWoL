let notyf;

function addDevice(pcid) {
    // get 3 fields
    const prettyName = document.querySelector(`#pretty_name`).value.trim();
    const deviceIP = document.querySelector(`#device_ip`).value.trim();
    const macAddress = document.querySelector(`#mac_address`).value.trim();
    // send request
    fetch('/add_device', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ prettyName: prettyName, deviceIP: deviceIP, macAddress: macAddress })
    })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(({ status, body }) => {
            if (status === 200) {
                window.location = '/edit?added=' + body.id;
            } else if (status === 500 || status === 400) {
                throw new Error(status + ", " + (body.error || "Internal Server Error"));
            } else if (!status.toString().startsWith("2")) {
                throw new Error("Response code: " + status);
            }
        })
        .catch(error => {
            console.log("Request failed: " + error.message);
            notyf.error("Request failed: " + error.message);
        });
}

function updateDevice(pcid) {
    // get 3 fields
    const prettyName = document.querySelector(`#pretty_name`).value.trim();
    const deviceIP = document.querySelector(`#device_ip`).value.trim();
    const macAddress = document.querySelector(`#mac_address`).value.trim();
    // send request
    fetch(`/edit/${pcid}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ prettyName: prettyName, deviceIP: deviceIP, macAddress: macAddress })
    })
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(({ status, body }) => {
            if (status === 200) {
                window.location = '/edit?edited=' + pcid;
            } else if (status === 500 || status === 400) {
                throw new Error(status + ", " + (body.error || "Internal Server Error"));
            } else if (!status.toString().startsWith("2")) {
                throw new Error("Response code: " + status);
            }
        })
        .catch(error => {
            console.log("Request failed: " + error.message);
            notyf.error("Request failed: " + error.message);
        });
}

document.addEventListener("DOMContentLoaded", function () {
    notyf = new Notyf();
    const inputs = document.querySelectorAll("input");

    document.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
            event.preventDefault();
            // If window.pcid is defined, we're on the edit page
            if (typeof window.pcid !== "undefined") {
                updateDevice(window.pcid);
            } else {
                addDevice();
            }
        }
    });
});
