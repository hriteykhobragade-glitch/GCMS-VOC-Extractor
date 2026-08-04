from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
from extractor import process_folder
import os
import shutil
import tempfile

app = Flask(__name__)

# Create temporary folders if they don't exist
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():

    # Clear old uploaded files
    if os.path.exists(UPLOAD_FOLDER):
        shutil.rmtree(UPLOAD_FOLDER)

    os.makedirs(UPLOAD_FOLDER)

    uploaded_files = request.files.getlist("files")

    if len(uploaded_files) == 0:
        return jsonify({"error": "No files uploaded"}), 400

    print("\n===================================")
    print("Receiving uploaded files...")
    print("===================================")

    for file in uploaded_files:

        if file.filename == "":
            continue

        filename = secure_filename(file.filename)

        save_path = os.path.join(
            UPLOAD_FOLDER,
            filename
        )

        file.save(save_path)

        print("Saved:", filename)

    output_excel = os.path.join(
        OUTPUT_FOLDER,
        "Combined_Areas.xlsx"
    )

    print("\nStarting GCMS extraction...\n")

    process_folder(
        UPLOAD_FOLDER,
        output_excel
    )

    print("\nExtraction Finished.\n")

    return send_file(
        output_excel,
        as_attachment=True
    )


if __name__ == "__main__":
    app.run(
        debug=True
    )