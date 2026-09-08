function showDetails(marker) {

    const location = marker.dataset.location;
    const risk = marker.dataset.risk;

    let message = "";

    if (risk === "high") {
        message = "Immediate attention required. Avoid this area.";
    } 
    else if (risk === "medium") {
        message = "Moderate landslide possibility. Stay alert.";
    } 
    else {
        message = "Low landslide risk. Normal precautions advised.";
    }

    document.getElementById("details").innerHTML = `
        <h2>📍 ${location}</h2>

        <p>
            <strong>Risk Level:</strong>
            ${risk.toUpperCase()}
        </p>

        <p>
            <strong>Status:</strong>
            ${message}
        </p>

        <p>
            <strong>Monitoring:</strong>
            Active
        </p>

        <p>
            <strong>Last Updated:</strong>
            ${new Date().toLocaleString()}
        </p>
    `;
}


function findLocation() {

    const search = document
        .getElementById("searchBox")
        .value
        .toLowerCase();

    const markers = document.querySelectorAll(".landslide-marker");

    let found = false;

    markers.forEach(marker => {

        const location =
            marker.dataset.location.toLowerCase();

        if (location.includes(search) && search !== "") {

            marker.style.transform = "scale(1.5)";
            marker.style.border = "4px solid yellow";

            showDetails(marker);

            found = true;

        } else {

            marker.style.transform = "";
            marker.style.border = "3px solid white";

        }
    });

    if (!found && search !== "") {
        alert("Location not found!");
    }
}


/* Risk filter */

document
    .getElementById("riskFilter")
    .addEventListener("change", function () {

        const selectedRisk = this.value;

        const markers =
            document.querySelectorAll(".landslide-marker");

        markers.forEach(marker => {

            if (
                selectedRisk === "all" ||
                marker.dataset.risk === selectedRisk
            ) {
                marker.style.display = "flex";
            } else {
                marker.style.display = "none";
            }

        });
    });
