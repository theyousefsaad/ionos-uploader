from flask import Flask, request, jsonify
import os
import datetime
import paramiko
import tempfile
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ==== SFTP Config ====
SFTP_HOST = "home558455723.1and1-data.host"
SFTP_PORT = 22
SFTP_USER = "u79546177"
SFTP_PASS = "Carcafe123!"

@app.route("/upload", methods=["POST"])
def upload():
    vin = request.form.get("vin")
    year = request.form.get("year")
    month = request.form.get("month")
    make = request.form.get("make")
    model = request.form.get("model")
    image_files = request.files.getlist("images")
    video_files = request.files.getlist("videos")

    print("DEBUG - vin:", vin)
    print("DEBUG - year:", year)
    print("DEBUG - month:", month)
    print("DEBUG - make:", make)
    print("DEBUG - model:", model)
    print("DEBUG - image files:", len(image_files))
    print("DEBUG - video files:", len(video_files))

    if not all([vin, year, month, make, model]) or (not image_files and not video_files):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # ==== Build Remote Folder ====
        now = datetime.datetime.now()
        folder_year = now.strftime("%Y")
        vehicle_folder = f"{year}{make}{model}-{vin}"
        remote_base = f"/{folder_year}CarPhotos/{month}/{vehicle_folder}/"

        # ==== Connect to SFTP ====
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        transport.connect(username=SFTP_USER, password=SFTP_PASS)
        sftp = paramiko.SFTPClient.from_transport(transport)

        # ==== Create Folders ====
        def make_remote_dirs(path):
            dirs = path.strip("/").split("/")
            current = ""
            for d in dirs:
                current += "/" + d
                try:
                    sftp.mkdir(current)
                    print("Created folder:", current)
                except IOError:
                    pass

        make_remote_dirs(remote_base)

        # ==== Upload Utility ====
        def upload_files(file_list, prefix):
            urls = []
            for idx, file in enumerate(file_list, 1):
                filename = secure_filename(file.filename)
                ext = filename.split(".")[-1]
                new_name = f"{prefix}{str(idx).zfill(3)}.{ext}"

                with tempfile.NamedTemporaryFile(delete=False) as temp:
                    file.save(temp.name)
                    sftp.put(temp.name, remote_base + new_name)
                    os.remove(temp.name)

                url = f"https://photos.carcafe-tx.com{remote_base}{new_name}"
                urls.append(url)
            return urls

        # ==== Upload ====
        image_urls = upload_files(image_files, "img_")
        video_urls = upload_files(video_files, "vid_")

        sftp.close()
        transport.close()

        return jsonify({
            "uploaded_images": image_urls,
            "uploaded_videos": video_urls
        }), 200

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
