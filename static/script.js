console.log("✅ script.js loaded");

const folderInput = document.getElementById("folderInput");
const folderName = document.getElementById("folderName");
const fileList = document.getElementById("fileList");
const processBtn = document.getElementById("processBtn");
const log = document.getElementById("log");

// ===============================
// DISPLAY SELECTED FOLDER
// ===============================

folderInput.addEventListener("change", () => {

    console.log("📂 Folder selected");

    fileList.innerHTML = "";

    if (folderInput.files.length === 0) {

        folderName.innerHTML = "No folder selected";

        return;

    }

    const folder = folderInput.files[0].webkitRelativePath.split("/")[0];

    folderName.innerHTML = "📁 " + folder;

    [...folderInput.files].forEach(file => {

        fileList.innerHTML += `✔ ${file.name}<br>`;

    });

});


// =========================================================
// PROCESS BUTTON
// =========================================================

processBtn.addEventListener("click", async () => {

    console.log("🚀 Process button clicked");


    // =========================================================
    // CHECK FOLDER SELECTION
    // =========================================================

    if (folderInput.files.length === 0) {

        alert("Please choose a folder first.");

        return;
    }


    // =========================================================
    // PREPARE UPLOAD
    // =========================================================

    log.innerHTML = "Uploading files...<br>";

    const formData = new FormData();


    [...folderInput.files].forEach(file => {

        formData.append("files", file);

    });


    // =========================================================
    // SEND FILES TO FLASK
    // =========================================================

    try {

        console.log("📤 Sending files to Flask...");

        const response = await fetch("/process", {

            method: "POST",

            body: formData

        });


        console.log(
            "Response status:",
            response.status
        );


        // =====================================================
        // HANDLE SERVER ERRORS
        // =====================================================

        if (!response.ok) {

            let errorMessage =
                "The server could not process the files.";


            try {

                const errorData =
                    await response.json();


                if (errorData.error) {

                    errorMessage =
                        errorData.error;

                } else if (errorData.message) {

                    errorMessage =
                        errorData.message;
                }


            } catch (parseError) {

                errorMessage =
                    "Server returned error " +
                    response.status;
            }


            throw new Error(errorMessage);
        }


        // =====================================================
        // EXTRACTION STARTED
        // =====================================================

        log.innerHTML +=
            "Running GCMS extraction...<br>";


        console.log(
            "GCMS extraction started."
        );


        // =====================================================
        // RECEIVE EXCEL FILE
        // =====================================================

        const blob =
            await response.blob();


        console.log(
            "Excel received."
        );


        // =====================================================
        // CREATE DOWNLOAD
        // =====================================================

        const url =
            window.URL.createObjectURL(blob);


        const a =
            document.createElement("a");


        a.href = url;


        a.download =
            "Combined_Areas.xlsx";


        document.body.appendChild(a);


        a.click();


        document.body.removeChild(a);


        window.URL.revokeObjectURL(url);


        // =====================================================
        // SUCCESS MESSAGE
        // =====================================================

        log.innerHTML +=
            "✅ Extraction complete.<br>";


        log.innerHTML +=
            "Downloading Combined_Areas.xlsx...";


        console.log(
            "Extraction completed successfully."
        );


    } catch (err) {

        // =====================================================
        // ERROR HANDLING
        // =====================================================

        console.error(err);


        log.innerHTML +=
            '<br><span style="color:red;">' +
            '❌ ' +
            err.message +
            '</span>';

    }

});