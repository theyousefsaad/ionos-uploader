from flask import Flask, request, jsonify
import os
import datetime
import paramiko
from werkzeug.utils import secure_filename
import tempfile

app = Flask(__name__)

# ==== SFTP Config ====
SFTP_HOST = "home558455723.1and1-data.host"
SFTP_PORT = 22
SFTP_USER = "u79546177"
SFTP_PASS = "Carcafe123!"

@app.route('/upload_images', methods=['POST'])
def upload_images():
    year = request.form.get("year")
    make = request.form.get("make")
    model = request.form.get("model")
    vin = request.form.get("vin")
    files = request.files.getlist("files")

    if not all([year, make, model, vin]) or not files:
        return jsonify({"error": "Missing one or more required fields."}), 400

    try:
        now = datetime.datetime.now()
        folder_year = now.strftime("%Y")
        folder_month = now.strftime("%b")
        vehicle_folder = f"{year}{make}{model}-{vin}"
        remote_base = f"/{folder_year}CarPhotos/{folder_month}/{vehicle_folder}/"

        # Connect to SFTP
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.connect(username=SFTP_USER, password=SFTP_PASS)
        sftp = paramiko.SFTPClient.from_transport(transport)

        # Create nested folders
        def make_remote_dirs(path):
            dirs = path.strip("/").split("/")
            current = ""
            for d in dirs:
                current += "/" + d
                try:
                    sftp.mkdir(current)
                except IOError:
                    pass  # Already exists

        make_remote_dirs(remote_base)

        # Upload files
        image_urls = []
        for idx, file in enumerate(files, 1):
            filename = secure_filename(file.filename)
            ext = filename.split(".")[-1]
            new_name = f"{str(idx).zfill(3)}.{ext}"

            # Save temporarily
            with tempfile.NamedTemporaryFile(delete=False) as temp:
                file.save(temp.name)
                sftp.put(temp.name, remote_base + new_name)
                os.remove(temp.name)

            url = f"https://photos.carcafe-tx.com{remote_base}{new_name}"
            image_urls.append(url)

        sftp.close()
        transport.close()

        return jsonify({"uploaded": image_urls}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
