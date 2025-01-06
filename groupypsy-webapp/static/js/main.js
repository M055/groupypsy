// Initialize sessionID first
if (!window.sessionID) {
    window.sessionID = Math.random().toString(36).substring(2, 15);
}



// Track upload status for each required file
const uploadedFiles = {
    students: false,
    projects: false,
    requirements: false,
    choices: false,
};

// Helper to update upload status and manage the "Process" button state
function updateUploadStatus(fileType, status) {
    uploadedFiles[fileType] = status;
    // console.log("Uploaded Files Status:", uploadedFiles);

    // Enable or disable the "Process" button based on upload status
    const allFilesUploaded = Object.values(uploadedFiles).every(value => value === true);
    const processButton = document.getElementById("processButton");
    processButton.disabled = !allFilesUploaded;
}

// Initialize FilePond elements
const filePondInstances = {}; // To keep track of each FilePond instance
['students', 'projects', 'requirements', 'choices'].forEach(fileType => {
    const pond = FilePond.create(document.getElementById(`${fileType}File`));
    pond.setOptions({
        server: {
            process: {
                url: `/upload/${fileType}`,
                method: 'POST',
                headers: { 'Accept': 'application/json' },
                ondata: (formData) => {
                    formData.append('sessionID', window.sessionID);
                    return formData;
                },
                onload: () => updateUploadStatus(fileType, true),
                onerror: () => updateUploadStatus(fileType, false),
            },
        },
    });

    filePondInstances[fileType] = pond; // Store the instance for later access
});

// Handle "Process" button click
document.getElementById("processButton").addEventListener("click", function () {
    // Check if all files are uploaded
    if (!Object.values(uploadedFiles).every(value => value === true)) {
        Swal.fire("Error", "Please upload all required files before processing.", "error");
        return;
    }

    // Trigger backend processing
    fetch('/process_files', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sessionID: sessionID }), // Send session ID to backend
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(errData => {
                    throw new Error(errData.error || "Processing failed.");
                });
            }
            return response.json();
        })
        .then(data => {
            // console.log("Processing complete:", data.message);

            // Display the CSV file in a table
            displayCSV();

            // Create a dynamic download link for the processed file
            const downloadLink = document.createElement("a");
            downloadLink.href = data.download_url;
            downloadLink.textContent = "Download Processed Data";
            downloadLink.className = "btn btn-success mt-3";
            document.getElementById("downloadLinkContainer").innerHTML = ""; // Clear previous links
            document.getElementById("downloadLinkContainer").appendChild(downloadLink);

            // Display the plot
            const plotContainer = document.getElementById("plotContainer");
            const img = document.createElement("img");
            img.src = data.plot_url;
            // console.log(data.plot_url);
            img.alt = "Generated Plot";
            img.className = "img-fluid mt-3";
            plotContainer.innerHTML = ""; // Clear previous plot
            plotContainer.appendChild(img);

             // Dynamically add legend text below the plot
             const legendText = document.createElement("p");
             legendText.textContent = "Cumulative Histogram of Ranks of Assigned Projects. X-axis values are the rank choices from 1(most desirable) to N (least desirable, Nth project). Y-values at each Rank represent the probability of being assigned that rank or lower.";
             legendText.style.fontStyle = "italic";
             plotContainer.appendChild(legendText);

            // Swal.fire("Success", "Files processed successfully. You can download the result.", "success");
            const successMesg = data.check_mesg + "<br><br>" + 'Files processed successfully. You can download the result.';
            Swal.fire({
                title: 'Success',
                html: successMesg,
                icon: 'info',
                confirmButtonText: 'Got it!',
                timer: 20000, // Close after 5 seconds
                timerProgressBar: true // Show progress bar
            });
        })
        .catch(error => {
            console.error("Error during processing:", error);
            Swal.fire("Error", error.message, "error");
        });
});


// Handle "Clear Data" button click
document.getElementById("clearDataButton").addEventListener("click", function () {
    // console.log("Session ID before clearing data:", window.sessionID);

    Swal.fire({
        title: 'Are you sure?',
        text: 'This will delete all uploaded and generated data for this session!',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Yes, clear data!',
        cancelButtonText: 'No, keep it',
    }).then((result) => {
        if (result.isConfirmed) {
            // Make a request to clear data
            fetch('/clear_data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sessionID: window.sessionID }),
            })
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(errData => {
                            throw new Error(errData.error || "Failed to clear data.");
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    // console.log("Clear Data Response:", data);
                    Swal.fire('Cleared!', data.message, 'success');

                    // Reinitialize FilePond elements
                    Object.values(filePondInstances).forEach(pond => {
                        pond.removeFiles(); // Clears all files from the FilePond instance
                    });

                    // Reset the page state
                    const plotContainer = document.getElementById("plotContainer");
                    const downloadLinkContainer = document.getElementById("downloadLinkContainer");
                    plotContainer.innerHTML = "";
                    downloadLinkContainer.innerHTML = "";
                    // Empty the CSV table 
                    // Make the table container visible
                    const tableContainer = document.getElementById("csvTableContainer");
                    tableContainer.style.display = "none";

                    // Disable the Process button
                    document.getElementById("processButton").disabled = true;

                    // Clear uploaded files tracking
                    ['students', 'projects', 'requirements', 'choices'].forEach(fileType => {
                        uploadedFiles[fileType] = false;
                    });
                })
                .catch(error => {
                    console.error("Error clearing data:", error);
                    Swal.fire('Error', error.message, 'error');
                });
        }
    });
});



// Display CSV
function displayCSV() {
    fetch(`/display_csv?sessionID=${window.sessionID}`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(errData => {
                    throw new Error(errData.error || "Failed to fetch CSV data.");
                });
            }
            return response.json();
        })
        .then(data => {
            // console.log("CSV Data:", data);

            // Clear existing table content
            const tableHeaders = document.getElementById("csvTableHeaders");
            const tableBody = document.getElementById("csvTableBody");
            tableHeaders.innerHTML = ""; // Clear headers
            tableBody.innerHTML = "";   // Clear body

            // Get table headers dynamically from the data
            //const headers = Object.keys(data.data[0]);
            const headers = data.column_order;
            // console.log("Table Headers:", headers);
            headers.forEach(header => {
                const th = document.createElement("th");
                th.textContent = header;
                tableHeaders.appendChild(th);
            });

            // Populate table rows
            data.data.forEach(row => {
                // console.log("Row data:", row); // Debug log
                const tr = document.createElement("tr");
                headers.forEach(header => {
                    const td = document.createElement("td");
                    td.textContent = row[header];
                    tr.appendChild(td);
                });
                tableBody.appendChild(tr);
            });

            // Make the table container visible
            const tableContainer = document.getElementById("csvTableContainer");
            tableContainer.style.display = "block";

            // Initialize or reinitialize DataTables
            if ($.fn.DataTable.isDataTable('#csvTable')) {
                $('#csvTable').DataTable().clear().destroy(); // Destroy previous instance
            }
            $('#csvTable').DataTable({
                paging: true,
                searching: true,
                ordering: true,
                info: true,
                responsive: true,
            });
        })
        .catch(error => {
            console.error("Error fetching CSV data:", error);
            Swal.fire("Error", error.message, "error");
        });
}



