@app.route("/")
def index():
    return "IONOS uploader is working!"

from flask import Flask, request, jsonify
import os
import paramiko
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Load env vars
FTP_HOST = os.getenv("FTP_HOST")
FTP_PORT = int(os.getenv("FTP_PORT", 22))
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
BASE_URL = os.getenv("BASE_URL")

@app.route("/upload", methods=["POST"])
def upload():
    vin = request.form.get("vin")
    year = request.form.get("year")
    month = request.form.get("month")

    if not vin or not year or not month or 'files' not in request.files:
        return jsonify({"error": "Missing required fields"}), 400

    uploaded_files = request.files.getlist("files")
    folder_path = f"/photos/2025CarPhotos/{month}/{year}{vin}/"

    try:
        transport = paramiko.Transport((FTP_HOST, FTP_PORT))
        transport.connect(username=FTP_USER, password=FTP_PASS)
        sftp = paramiko.SFTPClient.from_transport(transport)

        try:
            sftp.chdir(folder_path)
        except IOError:
            sftp.mkdir(folder_path)
            sftp.chdir(folder_path)

        urls = []
        for idx, file in enumerate(uploaded_files):
            filename = f"{str(idx+1).zfill(3)}.jpg"
            local_path = f"/tmp/{filename}"
            file.save(local_path)
            remote_path = folder_path + filename
            sftp.put(local_path, remote_path)
            urls.append(f"{BASE_URL}{folder_path}{filename}")
            os.remove(local_path)

        sftp.close()
        transport.close()

        return jsonify({"urls": urls}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    import os

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)


