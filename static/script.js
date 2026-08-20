console.log("✅ GCMS VOC Extractor script loaded");


// =========================================================
// ELEMENTS
// =========================================================

const folderInput = document.getElementById("folderInput");
const folderName = document.getElementById("folderName");
const fileList = document.getElementById("fileList");
const processBtn = document.getElementById("processBtn");
const log = document.getElementById("log");


// =========================================================
// OPTIONAL POLISHED UI ELEMENTS
// =========================================================

// These elements may exist in the polished HTML.
// If they don't, the application still works normally.

const workflowSteps =
    document.querySelectorAll(".workflow-step");

const fileCountBadge =
    document.querySelector(".count-badge");

const folderStatus =
    document.querySelector(".folder-status");

const statusBadge =
    document.querySelector(".status-badge");

const uploadZone =
    document.querySelector(".upload-zone");


// =========================================================
// WORKFLOW STATE
// =========================================================

function setWorkflowState(activeStep) {

    workflowSteps.forEach((step, index) => {

        const stepNumber = index + 1;

        step.classList.remove("active");
        step.classList.remove("completed");

        if (stepNumber < activeStep) {

            step.classList.add("completed");

        } else if (stepNumber === activeStep) {

            step.classList.add("active");

        }

    });

}


// =========================================================
// STATUS BADGE
// =========================================================

function setStatus(text, type = "idle") {

    if (!statusBadge) {
        return;
    }

    const dot =
        statusBadge.querySelector(".status-badge-dot");

    const textElement =
        statusBadge.querySelector(".status-text");

    if (textElement) {
        textElement.textContent = text;
    } else {
        statusBadge.textContent = text;
    }

    if (dot) {

        if (type === "success") {
            dot.style.background = "#16a34a";
        }

        else if (type === "error") {
            dot.style.background = "#dc2626";
        }

        else if (type === "processing") {
            dot.style.background = "#2563eb";
        }

        else {
            dot.style.background = "#94a3b8";
        }

    }

}


// =========================================================
// FILE COUNT
// =========================================================

function updateFileCount(count) {

    if (!fileCountBadge) {
        return;
    }

    fileCountBadge.textContent =
        `${count} ${count === 1 ? "file" : "files"}`;

}


// =========================================================
// FOLDER STATUS
// =========================================================

function updateFolderStatus(text, selected = false) {

    if (!folderStatus) {
        return;
    }

    const statusText =
        folderStatus.querySelector(".folder-status-text");

    if (statusText) {
        statusText.textContent = text;
    } else {
        folderStatus.textContent = text;
    }

    if (selected) {
        folderStatus.classList.add("selected");
    } else {
        folderStatus.classList.remove("selected");
    }

}


// =========================================================
// LOG HELPERS
// =========================================================

function addLog(message, type = "normal") {

    const line = document.createElement("div");

    line.className = "log-line";

    const dot = document.createElement("span");

    dot.className = "log-dot";

    if (type === "success") {
        dot.style.background = "#4ade80";
    }

    else if (type === "error") {
        dot.style.background = "#f87171";
    }

    else if (type === "processing") {
        dot.style.background = "#60a5fa";
    }

    else {
        dot.style.background = "#64748b";
    }

    const text = document.createElement("span");

    text.textContent = message;

    line.appendChild(dot);
    line.appendChild(text);

    log.appendChild(line);

    log.scrollTop = log.scrollHeight;
}


function clearLog() {

    log.innerHTML = "";

}


// =========================================================
// PROCESS BUTTON STATE
// =========================================================

function setProcessButton(text, disabled) {

    processBtn.disabled = disabled;

    const icon =
        processBtn.querySelector(".process-button-icon");

    const textElement =
        processBtn.querySelector(".process-button-text");

    if (textElement) {

        textElement.textContent = text;

    } else {

        // Preserve the button if the polished HTML
        // does not contain the text wrapper.
        processBtn.textContent = text;

        if (icon) {
            processBtn.prepend(icon);
        }

    }

}


// =========================================================
// INITIAL STATE
// =========================================================

setWorkflowState(1);

setStatus("System ready", "idle");

updateFileCount(0);

updateFolderStatus(
    "No folder selected",
    false
);

if (processBtn) {
    processBtn.disabled = true;
}


// =========================================================
// DISPLAY SELECTED FOLDER
// =========================================================

folderInput.addEventListener("change", () => {

    console.log("📂 Folder selection changed");

    clearLog();

    fileList.innerHTML = "";

    const selectedFiles =
        [...folderInput.files];

    // -----------------------------------------------------
    // NOTHING SELECTED
    // -----------------------------------------------------

    if (selectedFiles.length === 0) {

        folderName.textContent =
            "No folder selected";

        updateFolderStatus(
            "No folder selected",
            false
        );

        updateFileCount(0);

        setProcessButton(
            "Process Samples",
            true
        );

        setWorkflowState(1);

        setStatus(
            "System ready",
            "idle"
        );

        fileList.innerHTML = `
            <div class="empty-files">
                <span class="empty-files-icon">—</span>
                <span>No files selected yet.</span>
            </div>
        `;

        return;
    }


    // -----------------------------------------------------
    // GET FOLDER NAME
    // -----------------------------------------------------

    let folder = "Selected folder";

    if (
        selectedFiles[0].webkitRelativePath &&
        selectedFiles[0].webkitRelativePath.includes("/")
    ) {

        folder =
            selectedFiles[0]
                .webkitRelativePath
                .split("/")[0];

    }


    folderName.textContent =
        "📁 " + folder;


    updateFolderStatus(
        folder,
        true
    );


    // -----------------------------------------------------
    // FILTER XLSX FILES
    // -----------------------------------------------------

    const validFiles =
        selectedFiles.filter(file => {

            return file.name
                .toLowerCase()
                .endsWith(".xlsx");

        });


    const invalidFiles =
        selectedFiles.filter(file => {

            return !file.name
                .toLowerCase()
                .endsWith(".xlsx");

        });


    console.log(
        `Found ${validFiles.length} valid XLSX files`
    );


    if (invalidFiles.length > 0) {

        console.warn(
            "Unsupported files:",
            invalidFiles
        );

    }


    // -----------------------------------------------------
    // NO VALID XLSX FILES
    // -----------------------------------------------------

    if (validFiles.length === 0) {

        updateFileCount(0);

        fileList.innerHTML = `
            <div class="empty-files">
                <span class="empty-files-icon">!</span>
                <span>
                    No supported .xlsx files found.
                </span>
            </div>
        `;

        setProcessButton(
            "Process Samples",
            true
        );

        setWorkflowState(1);

        setStatus(
            "Unsupported file type",
            "error"
        );

        addLog(
            "No supported .xlsx files were found.",
            "error"
        );

        return;
    }


    // -----------------------------------------------------
    // UPDATE FILE COUNT
    // -----------------------------------------------------

    updateFileCount(
        validFiles.length
    );


    // -----------------------------------------------------
    // DISPLAY FILES
    // -----------------------------------------------------

    validFiles.forEach(file => {

        const item =
            document.createElement("div");

        item.className =
            "file-item";


        const icon =
            document.createElement("span");

        icon.className =
            "file-icon";

        icon.textContent =
            "XLSX";


        const name =
            document.createElement("span");

        name.className =
            "file-name";

        name.textContent =
            file.name;


        item.appendChild(icon);

        item.appendChild(name);

        fileList.appendChild(item);

    });


    // -----------------------------------------------------
    // WORKFLOW → PROCESS
    // -----------------------------------------------------

    setWorkflowState(2);

    setStatus(
        "Ready to process",
        "idle"
    );


    setProcessButton(
        "Process Samples",
        false
    );


    addLog(
        `${validFiles.length} XLSX ${
            validFiles.length === 1
                ? "file"
                : "files"
        } ready for processing.`
    );


    console.log(
        "✅ Files ready for processing"
    );

});


// =========================================================
// UPLOAD ZONE CLICK
// =========================================================

if (uploadZone) {

    uploadZone.addEventListener("click", () => {

        folderInput.click();

    });

}


// =========================================================
// PROCESS BUTTON
// =========================================================

processBtn.addEventListener("click", async () => {

    console.log("🚀 Process button clicked");


    // =====================================================
    // CHECK FOLDER
    // =====================================================

    if (
        !folderInput.files ||
        folderInput.files.length === 0
    ) {

        alert(
            "Please choose a folder first."
        );

        return;

    }


    // =====================================================
    // GET XLSX FILES
    // =====================================================

    const selectedFiles =
        [...folderInput.files];


    const validFiles =
        selectedFiles.filter(file => {

            return file.name
                .toLowerCase()
                .endsWith(".xlsx");

        });


    if (validFiles.length === 0) {

        alert(
            "No supported .xlsx files were found."
        );

        return;

    }


    // =====================================================
    // DISABLE BUTTON
    // =====================================================

    setProcessButton(
        "Processing...",
        true
    );


    setWorkflowState(2);

    setStatus(
        "Processing",
        "processing"
    );


    // =====================================================
    // CLEAR LOG
    // =====================================================

    clearLog();


    addLog(
        "Preparing files...",
        "processing"
    );


    // =====================================================
    // PREPARE FORM DATA
    // =====================================================

    const formData =
        new FormData();


    validFiles.forEach(file => {

        formData.append(
            "files",
            file
        );

    });


    // =====================================================
    // SEND FILES TO FLASK
    // =====================================================

    try {

        addLog(
            `Uploading ${validFiles.length} ${
                validFiles.length === 1
                    ? "file"
                    : "files"
            } to the server...`,
            "processing"
        );


        console.log(
            "📤 Sending files to Flask..."
        );


        const response =
            await fetch(
                "/process",
                {
                    method: "POST",
                    body: formData
                }
            );


        console.log(
            "Response status:",
            response.status
        );


        // =================================================
        // SERVER ERROR
        // =================================================

        if (!response.ok) {

            let errorMessage =
                "The server could not process the files.";


            try {

                const errorData =
                    await response.json();


                if (errorData.error) {

                    errorMessage =
                        errorData.error;

                }

                else if (errorData.message) {

                    errorMessage =
                        errorData.message;

                }

            }

            catch (parseError) {

                errorMessage =
                    "Server returned error " +
                    response.status;

            }


            throw new Error(
                errorMessage
            );

        }


        // =================================================
        // EXTRACTION
        // =================================================

        setWorkflowState(2);

        setStatus(
            "Running extraction",
            "processing"
        );


        addLog(
            "Running GCMS extraction...",
            "processing"
        );


        console.log(
            "🧪 GCMS extraction started."
        );


        // =================================================
        // RECEIVE EXCEL
        // =================================================

        const blob =
            await response.blob();


        console.log(
            "📊 Excel received."
        );


        addLog(
            "Extraction completed successfully.",
            "success"
        );


        // =================================================
        // CREATE DOWNLOAD
        // =================================================

        const url =
            window.URL.createObjectURL(
                blob
            );


        const a =
            document.createElement("a");


        a.href = url;


        a.download =
            "Combined_Areas.xlsx";


        document.body.appendChild(a);


        // =================================================
        // DOWNLOAD
        // =================================================

        addLog(
            "Preparing Combined_Areas.xlsx...",
            "processing"
        );


        a.click();


        document.body.removeChild(a);


        window.URL.revokeObjectURL(
            url
        );


        // =================================================
        // SUCCESS
        // =================================================

        setWorkflowState(4);

        setStatus(
            "Analysis complete",
            "success"
        );


        addLog(
            "✓ Combined_Areas.xlsx downloaded.",
            "success"
        );


        console.log(
            "✅ Extraction completed successfully."
        );


        // -------------------------------------------------
        // RESTORE BUTTON
        // -------------------------------------------------

        setProcessButton(
            "Process Samples",
            false
        );


    }


    // =====================================================
    // ERROR HANDLING
    // =====================================================

    catch (err) {

        console.error(
            "❌ Processing error:",
            err
        );


        setStatus(
            "Processing failed",
            "error"
        );


        addLog(
            err.message ||
            "An unexpected error occurred.",
            "error"
        );


        setWorkflowState(2);


        setProcessButton(
            "Try Again",
            false
        );

    }

});


// =========================================================
// DRAG & DROP SUPPORT
// =========================================================

if (uploadZone) {

    uploadZone.addEventListener(
        "dragover",
        event => {

            event.preventDefault();

            uploadZone.style.borderColor =
                "#60a5fa";

            uploadZone.style.background =
                "#f8fbff";

        }
    );


    uploadZone.addEventListener(
        "dragleave",
        () => {

            uploadZone.style.borderColor =
                "";

            uploadZone.style.background =
                "";

        }
    );


    uploadZone.addEventListener(
        "drop",
        event => {

            event.preventDefault();

            uploadZone.style.borderColor =
                "";

            uploadZone.style.background =
                "";

            console.log(
                "📂 Files dropped into upload area"
            );

        }
    );

}


// =========================================================
// INITIAL CONSOLE MESSAGE
// =========================================================

console.log(
    "🧪 GCMS VOC Extractor ready."
);