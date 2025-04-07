from flask import Flask, request, jsonify
import paramiko
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# SFTP credentials
FTP_HOST = "ftp.yourdomain.com"
FTP_PORT = 22
FTP_USER = "your_username"
FTP_PASS = "your_password"

@app.route("/upload", methods=["POST"])
def upload():
    vin = request.form.get("vin")
    year = request.form.get("year")
    month = request.form.get("month")
    make = request.form.get("make")
    model = request.form.get("model")

    if not vin or not year or not month or not make or not model or 'files' not in request.files:
        return jsonify({"error": "Missing required fields"}), 400

    uploaded_files = request.files.getlist("files")
    model_name = f"{year}{make}{model}".replace(" ", "")
    folder_path = f"/photos/2025CarPhotos/{month}/{model_name}-{vin}"

    try:
        transport = paramiko.Transport((FTP_HOST, FTP_PORT))
        transport.connect(username=FTP_USER, password=FTP_PASS)
        sftp = paramiko.SFTPClient.from_transport(transport)

        try:
            sftp.chdir(folder_path)
        except IOError:
            sftp.mkdir(folder_path)
            sftp.chdir(folder_path)

        for file in uploaded_files:
            filename = secure_filename(file.filename)
            sftp.putfo(file.stream, filename)

        sftp.close()
        transport.close()
        return jsonify({"message": "Files uploaded successfully", "folder": folder_path}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)

    app.run(host="0.0.0.0", port=port)
