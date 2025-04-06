@app.route("/upload", methods=["POST"])
def upload():
    if request.content_type.startswith("application/json"):
        # Handle raw JSON data (in case no files are sent)
        data = request.get_json()
        vin = data.get("vin")
        year = data.get("year")
        month = data.get("month")
        make_model = data.get("make_model")
        return jsonify({"error": "File uploads must be sent as form-data"}), 415

    elif request.content_type.startswith("multipart/form-data"):
        # Handle file upload from form-data (Glide or Postman)
        vin = request.form.get("vin")
        year = request.form.get("year")
        month = request.form.get("month")
        make_model = request.form.get("make_model")

        if not vin or not year or not month or not make_model or 'files' not in request.files:
            return jsonify({"error": "Missing required fields"}), 400

        uploaded_files = request.files.getlist("files")
        folder_path = f"/photos/2025CarPhotos/{month}/{year}{make_model}-{vin}"

        try:
            transport = paramiko.Transport((FTP_HOST, FTP_PORT))
            transport.connect(username=FTP_USER, password=FTP_PASS)
            sftp = paramiko.SFTPClient.from_transport(transport)

            try:
                sftp.chdir(folder_path)
            except IOError:
                sftp.mkdir(folder_path)

            for file in uploaded_files:
                sftp.putfo(file.stream, f"{folder_path}/{file.filename}")

            sftp.close()
            transport.close()
            return jsonify({"message": "Files uploaded successfully"}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    else:
        return jsonify({"error": "Unsupported Media Type"}), 415
