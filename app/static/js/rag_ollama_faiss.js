// Handle PDF Upload Form Submission
document.getElementById("pdfUploadForm").addEventListener("submit", function (event) {
    event.preventDefault(); // Prevent the form from submitting the traditional way

    // Get the folder path from the form
    const folderPath = document.getElementById("folder_path").value;

    // Make an asynchronous POST request to the upload endpoint
    fetch('/api/faiss/rag/upload', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ folder_path: folderPath })
    })
    .then(response => response.json())
    .then(data => {
        // Display success or error message
        if (data.message) {
            document.getElementById("uploadMessage").innerHTML = `<p style="color:green;">${data.message}</p>`;
        } else if (data.error) {
            document.getElementById("uploadMessage").innerHTML = `<p style="color:red;">${data.error}</p>`;
        }
    })
    .catch(error => {
        document.getElementById("uploadMessage").innerHTML = `<p style="color:red;">Error: ${error}</p>`;
    });
});

// Handle Query Form Submission
document.getElementById("queryForm").addEventListener("submit", function (event) {
    event.preventDefault(); // Prevent the form from submitting the traditional way

    // Get the question from the form
    const question = document.getElementById("question").value;

    // Make an asynchronous POST request to the query endpoint
    fetch('/api/faiss/rag/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: question })
    })
    .then(response => response.json())
    .then(data => {
        // Display the result or error
        if (data.answer) {
            document.getElementById("queryResult").innerHTML = `<p><strong>Answer:</strong> ${data.answer}</p>`;
        } else if (data.error) {
            document.getElementById("queryResult").innerHTML = `<p style="color:red;">${data.error}</p>`;
        }
    })
    .catch(error => {
        document.getElementById("queryResult").innerHTML = `<p style="color:red;">Error: ${error}</p>`;
    });
});
