from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import datetime
import paramiko
import tempfile

app = Flask(__name__)

# ==== CONFIG ====
SFTP_HOST = "home558455723.1and1-data.host"
SFTP_PORT = 22
SFTP_USER = "u79546177"
SFTP_PASS = "Carcafe123!"

def upload_to_ionos(car_year, car_make, car_model, vin_last8, local_folder):
    now = datetime.datetime.now()
    folder_year = now.strftime("%Y")
    folder_month = now.strftime("%b")
    vehicle_folder = f"{car_year}{car_make}{car_model}-{vin_last8}"
    remote_base = f"/{folder_year}CarPhotos/{folder_month}/{vehicle_folder}/"

    transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
    transport.connect(username=SFTP_USER, password=SFTP_PASS)
    sftp = paramiko.SFTPClient.from_transport(transport)

    def make_remote_dirs(path):
        dirs = path.strip("/").split("/")
        current = ""
        for d in dirs:
            current += "/" + d
            try:
                sftp.mkdir(current)
            except IOError:
                pass

    make_remote_dirs(remote_base)

    image_urls = []
    for idx, filename in enumerate(sorted(os.listdir(local_folder)), 1):
        ext = filename.split(".")[-1]
        new_name = f"{str(idx).zfill(3)}.{ext}"
        local_path = os.path.join(local_folder, filename)
        remote_path = f"{remote_base}{new_name}"
        sftp.put(local_path, remote_path)
        image_urls.append(f"https://photos.carcafe-tx.com{remote_path}")

    sftp.close()
    transport.close()
    return image_urls

@app.route('/upload', methods=['POST'])
def upload():
    data = request.form
    vin = data.get('vin')
    year = data.get('year')
    make = data.get('make')
    model = data.get('model')
    folder_path = data.get('folder_path')

    if not all([vin, year, make, model, folder_path]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        urls = upload_to_ionos(year, make, model, vin, folder_path)
        return jsonify({"uploaded": urls}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
