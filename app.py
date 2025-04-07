from flask import Flask, request, jsonify
import os
import paramiko
import tempfile
import requests
from werkzeug.utils import secure_filename

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
    month = request.form.get("month")
    file_urls = request.form.getlist("files")  # Glide sends image URLs here

    if not all([year, make, model, vin, month]) or not files:
     print("DEBUG - year:", year)
     print("DEBUG - make:", make)
     print("DEBUG - model:", model)
     print("DEBUG - vin:", vin)
     print("DEBUG - month:", month)
     print("DEBUG - files:", files)
    return jsonify({"error": "Missing one or more required fields."}), 400


    try:
        folder_year = "2025"  # You can make this dynamic if needed
        vehicle_folder = f"{year}{make}{model}-{vin}"
        remote_base = f"/{folder_year}CarPhotos/{month}/{vehicle_folder}/"

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
        for idx, url in enumerate(file_urls, 1):
            ext = url.split(".")[-1].split("?")[0]
            new_name = f"{str(idx).zfill(3)}.{ext}"

            response = requests.get(url)
            if response.status_code != 200:
                continue

            with tempfile.NamedTemporaryFile(delete=False) as temp:
                temp.write(response.content)
                temp.flush()
                sftp.put(temp.name, remote_base + new_name)
                os.remove(temp.name)

            full_url = f"https://photos.carcafe-tx.com{remote_base}{new_name}"
            image_urls.append(full_url)

        sftp.close()
        transport.close()

        return jsonify({"uploaded": image_urls}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
