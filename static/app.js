const apiKeyInput = document.getElementById("apiKey");
const messageInput = document.getElementById("message");
const normalButton = document.getElementById("normalButton");
const streamButton = document.getElementById("streamButton");
const output = document.getElementById("output");
const statusLabel = document.getElementById("status");


function setBusy(isBusy) {
    normalButton.disabled = isBusy;
    streamButton.disabled = isBusy;
}


function getMessage() {
    return messageInput.value.trim();
}


function getApiKey() {
    return apiKeyInput.value.trim();
}


function showError(message) {
    statusLabel.textContent = "Error";
    output.textContent = message;
}


// --------------------------------------------------
// NORMAL RESPONSE
// --------------------------------------------------

normalButton.addEventListener("click", async function () {

    const message = getMessage();
    const apiKey = getApiKey();

    if (!message) {
        showError("Please enter a question.");
        return;
    }

    if (!apiKey) {
        showError("Please enter an API key.");
        return;
    }

    setBusy(true);
    statusLabel.textContent = "Loading...";
    output.textContent = "Waiting for the AI...";

    try {

        const response = await fetch("/v1/chat", {
            method: "POST",

            headers: {
                "Content-Type": "application/json",
                "X-API-Key": apiKey,

                // Unique key for this request.
                "Idempotency-Key": "web-" + Date.now()
            },

            body: JSON.stringify({
                message: message,
                temperature: 0.7
            })
        });


        const data = await response.json();


        if (!response.ok) {
            throw new Error(
                data.detail || "Request failed"
            );
        }


        output.textContent =
            data.answer +
            "\n\nModel: " +
            data.model +
            "\nCached: " +
            data.cached;

        statusLabel.textContent = "Completed";

    } catch (error) {

        showError(error.message);

    } finally {

        setBusy(false);
    }
});


// --------------------------------------------------
// STREAMING RESPONSE
// --------------------------------------------------

streamButton.addEventListener("click", async function () {

    const message = getMessage();
    const apiKey = getApiKey();

    if (!message) {
        showError("Please enter a question.");
        return;
    }

    if (!apiKey) {
        showError("Please enter an API key.");
        return;
    }

    setBusy(true);
    statusLabel.textContent = "Streaming...";
    output.textContent = "";

    try {

        const response = await fetch("/v1/chat/stream", {
            method: "POST",

            headers: {
                "Content-Type": "application/json",
                "X-API-Key": apiKey
            },

            body: JSON.stringify({
                message: message,
                temperature: 0.7
            })
        });


        if (!response.ok) {

            const data = await response.json();

            throw new Error(
                data.detail || "Streaming request failed"
            );
        }


        // Read the streamed response manually.
        const reader = response.body.getReader();

        // Convert bytes into text.
        const decoder = new TextDecoder();

        let buffer = "";


        while (true) {

            const { value, done } = await reader.read();

            if (done) {
                break;
            }


            buffer += decoder.decode(
                value,
                { stream: true }
            );


            // SSE events are separated
            // by a blank line.
            const events = buffer.split("\n\n");

            // Keep unfinished data for the next chunk.
            buffer = events.pop();


            for (const eventText of events) {

                const lines = eventText.split("\n");

                for (const line of lines) {

                    if (line.startsWith("data:")) {

                        const text =
                            line.slice(5).trim();

                        if (text !== "completed") {
                            output.textContent +=
                                text + " ";
                        }
                    }
                }
            }
        }


        statusLabel.textContent = "Completed";

    } catch (error) {

        showError(error.message);

    } finally {

        setBusy(false);
    }
});
