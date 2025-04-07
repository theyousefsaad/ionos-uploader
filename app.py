from flask import Flask, request, jsonify
import logging

app = Flask(__name__)

# Enable debug-level logging
logging.basicConfig(level=logging.DEBUG)

@app.route("/upload", methods=["POST"])
def upload():
    try:
        vin = request.form.get("vin")
        year = request.form.get("year")
        month = request.form.get("month")
        model = request.form.get("model")

        if not vin or not year or not month or not model or 'files' not in request.files:
            return jsonify({"error": "Missing required fields"}), 400

        uploaded_files = request.files.getlist("files")
        folder_path = f"/photos/2025CarPhotos/{month}/{year}{model}-{vin}/"

        # FTP upload code (simplified for now)
        print("Uploading to folder:", folder_path)
        print("Number of files:", len(uploaded_files))

        return jsonify({"message": "Files processed (not actually uploaded in this example)."}), 200

    except Exception as e:
        app.logger.exception("Upload failed due to an error")
        return jsonify({"error": str(e)}), 500

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
