from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
from extractor import process_folder, load_voc_reference
import os
import json
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

@app.route("/vocs")
def vocs():

    reference_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "voc_reference.json"
    )

    with open(reference_file, "r", encoding="utf-8") as file:
        data = json.load(file)

    voc_reference = []

    for voc in data:

        voc_reference.append(
            (
                voc["name"],
                float(voc["reference_rt"]),
                int(voc["mz"]),
                float(voc["threshold"]),
                voc.get("active", True)
            )
        )

    return render_template(
        "vocs.html",
        vocs=voc_reference
    )

@app.route("/vocs/update", methods=["POST"])
def update_voc():

    data = request.get_json()

    index = data.get("index")
    name = data.get("name")
    reference_rt = data.get("reference_rt")
    mz = data.get("mz")
    threshold = data.get("threshold")

    reference_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "voc_reference.json"
    )

    with open(reference_file, "r", encoding="utf-8") as file:
        vocs = json.load(file)

    index = int(index)

    vocs[index]["name"] = name
    vocs[index]["reference_rt"] = float(reference_rt)
    vocs[index]["mz"] = int(mz)
    vocs[index]["threshold"] = float(threshold)

    with open(reference_file, "w", encoding="utf-8") as file:
        json.dump(vocs, file, indent=4)

    return jsonify({
        "success": True,
        "message": "VOC updated successfully"
    })
@app.route("/vocs/add", methods=["POST"])
def add_voc():

    data = request.get_json()

    name = str(data.get("name", "")).strip()

    reference_rt = data.get("reference_rt")
    mz = data.get("mz")
    threshold = data.get("threshold")

    # Check required fields
    if not name or reference_rt is None or mz is None or threshold is None:

        return jsonify({
            "success": False,
            "message": "All VOC fields are required."
        }), 400

    # Convert numeric values
    try:

        reference_rt = float(reference_rt)
        mz = int(mz)
        threshold = float(threshold)

    except (ValueError, TypeError):

        return jsonify({
            "success": False,
            "message": "RT, m/z, and threshold must be valid numbers."
        }), 400

    # Validate numeric values
    if reference_rt < 0:

        return jsonify({
            "success": False,
            "message": "Reference RT cannot be negative."
        }), 400

    if mz < 0:

        return jsonify({
            "success": False,
            "message": "m/z cannot be negative."
        }), 400

    if threshold < 0:

        return jsonify({
            "success": False,
            "message": "RT threshold cannot be negative."
        }), 400

    reference_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "voc_reference.json"
    )

    with open(reference_file, "r", encoding="utf-8") as file:
        vocs = json.load(file)

    # Check for duplicate VOC names
    for voc in vocs:

        if voc["name"].strip().lower() == name.lower():

            return jsonify({
                "success": False,
                "message": "A VOC with this name already exists."
            }), 400

    # Create new VOC
    new_voc = {
        "name": name,
        "reference_rt": reference_rt,
        "mz": mz,
        "threshold": threshold,
        "active": True
    }

    vocs.append(new_voc)

    # Save updated list
    with open(reference_file, "w", encoding="utf-8") as file:

        json.dump(
            vocs,
            file,
            indent=4
        )

    return jsonify({
        "success": True,
        "message": "VOC added successfully."
    })

@app.route("/vocs/toggle", methods=["POST"])
def toggle_voc():

    data = request.get_json()

    index = data.get("index")

    if index is None:
        return jsonify({
            "success": False,
            "message": "VOC index is required."
        }), 400

    reference_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "voc_reference.json"
    )

    with open(reference_file, "r", encoding="utf-8") as file:
        vocs = json.load(file)

    index = int(index)

    if index < 0 or index >= len(vocs):
        return jsonify({
            "success": False,
            "message": "Invalid VOC index."
        }), 400

    vocs[index]["active"] = not vocs[index].get("active", True)

    with open(reference_file, "w", encoding="utf-8") as file:
        json.dump(vocs, file, indent=4)

    return jsonify({
        "success": True,
        "active": vocs[index]["active"],
        "message": "VOC status updated successfully."
    })

@app.route("/vocs/delete", methods=["POST"])
def delete_voc():

    data = request.get_json()

    index = data.get("index")

    if index is None:
        return jsonify({
            "success": False,
            "message": "VOC index is required."
        }), 400

    reference_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "voc_reference.json"
    )

    with open(reference_file, "r", encoding="utf-8") as file:
        vocs = json.load(file)

    index = int(index)

    if index < 0 or index >= len(vocs):
        return jsonify({
            "success": False,
            "message": "Invalid VOC index."
        }), 400

    deleted_voc = vocs.pop(index)

    with open(reference_file, "w", encoding="utf-8") as file:
        json.dump(vocs, file, indent=4)

    return jsonify({
        "success": True,
        "message": f"{deleted_voc['name']} deleted successfully."
    })

@app.route("/vocs/download")
def download_vocs():

    reference_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "voc_reference.json"
    )

    return send_file(
        reference_file,
        as_attachment=True,
        download_name="voc_reference_backup.json"
    )

@app.route("/process", methods=["POST"])
def process():

        # Clear old uploaded files
    if os.path.exists(UPLOAD_FOLDER):

        for filename in os.listdir(UPLOAD_FOLDER):

            file_path = os.path.join(UPLOAD_FOLDER, filename)

            if os.path.isfile(file_path):

                try:
                    os.remove(file_path)

                except PermissionError:
                    pass

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    uploaded_files = request.files.getlist("files")

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