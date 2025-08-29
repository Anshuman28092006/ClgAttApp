function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(showPosition, showError);
    } else {
        document.getElementById("geo-status").innerHTML = "Geolocation not supported.";
    }
}

function showPosition(position) {
    // Simulate geofence check (real: compare to classroom coords)
    document.getElementById("geo-status").innerHTML = "Location: " + position.coords.latitude + ", " + position.coords.longitude + " (Valid geofence!)";
}

function showError(error) {
    document.getElementById("geo-status").innerHTML = "Geofence error: " + error.message;
}