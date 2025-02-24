const btn = document.getElementById("summarise");
const output = document.getElementById("output");

// Create loader dynamically & place it inside the body
const loader = document.createElement("div");
loader.style.border = "6px solid #f3f3f3";
loader.style.borderTop = "6px solid #ff4757";
loader.style.borderRadius = "50%";
loader.style.width = "40px";
loader.style.height = "40px";
loader.style.animation = "spin 1s linear infinite";
loader.style.margin = "20px auto";
loader.style.display = "none"; // Initially hidden

// Insert loader after the button
btn.insertAdjacentElement("afterend", loader);

// Click event for summarization
btn.addEventListener("click", function () {
    btn.disabled = true;
    btn.innerHTML = "Summarising...";
    loader.style.display = "block";  // Show loader
    output.innerHTML = "";  // Clear previous output

    // Get the active tab's URL
    chrome.tabs.query({ currentWindow: true, active: true }, function (tabs) {
        var url = tabs[0].url;

        // Make API request
        var xhr = new XMLHttpRequest();
        xhr.open("GET", "http://127.0.0.1:5000/summary?url=" + encodeURIComponent(url), true);

        xhr.onload = function () {
            try {
                var response = JSON.parse(xhr.responseText);

                if (response.summary) {
                    output.innerHTML = `<strong>Summary of the video:</strong> <br><br> ${response.summary}`;
                } else if (response.error) {
                    output.innerHTML = `<strong>Error:</strong> ${response.error}`;
                } else {
                    output.innerHTML = "Unexpected response from server.";
                }
            } catch (error) {
                output.innerHTML = "Error parsing response.";
            }

            // Hide loader & re-enable button
            loader.style.display = "none";
            btn.disabled = false;
            btn.innerHTML = "Summarise";
        };

        xhr.onerror = function () {
            output.innerHTML = "Network error. Please try again.";
            loader.style.display = "none";
            btn.disabled = false;
            btn.innerHTML = "Summarise";
        };

        xhr.send();
    });
});

// Add CSS animation for loader
const styleSheet = document.createElement("style");
styleSheet.innerHTML = `
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
`;
document.head.appendChild(styleSheet);
