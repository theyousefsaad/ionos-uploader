from flask import Flask, request, jsonify
import os
import datetime
import tempfile
import paramiko
import openai
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ==== SFTP Config ====
SFTP_HOST = "home558455723.1and1-data.host"
SFTP_PORT = 22
SFTP_USER = "u79546177"
SFTP_PASS = "Carcafe123!"

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/", methods=["GET"])
def home():
    return "✅ CarCafe API is live"

@app.route("/upload", methods=["POST"])
def upload():
    try:
        vin = request.form.get("vin")
        year = request.form.get("year")
        month = request.form.get("month")
        make = request.form.get("make")
        model = request.form.get("model")
        mileage = request.form.get("mileage")
        options = request.form.get("options")

        image_files = request.files.getlist("images")
        video_files = request.files.getlist("videos")
        carfax_file = request.files.get("carfax")

        if not all([vin, year, month, make, model, mileage, carfax_file]):
            return jsonify({"error": "Missing required fields"}), 400

        now = datetime.datetime.now()
        folder_year = now.strftime("%Y")
        vehicle_folder = f"{year}{make}{model}-{vin}"
        remote_base = f"/{folder_year}CarPhotos/{month}/{vehicle_folder}/"

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
        for idx, file in enumerate(image_files, 1):
            ext = secure_filename(file.filename).split(".")[-1]
            new_name = f"{str(idx).zfill(3)}.{ext}"
            with tempfile.NamedTemporaryFile(delete=False) as temp:
                file.save(temp.name)
                sftp.put(temp.name, remote_base + new_name)
                os.remove(temp.name)
            image_urls.append(f"https://photos.carcafe-tx.com{remote_base}{new_name}")

        video_urls = []
        for file in video_files:
            original_name = secure_filename(file.filename)
            with tempfile.NamedTemporaryFile(delete=False) as temp:
                file.save(temp.name)
                sftp.put(temp.name, remote_base + original_name)
                os.remove(temp.name)
            video_urls.append(f"https://photos.carcafe-tx.com{remote_base}{original_name}")

        # === Save Carfax PDF and upload to OpenAI ===
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as carfax_temp:
            carfax_file.save(carfax_temp.name)
            carfax_path = carfax_temp.name

        uploaded_pdf = openai.files.create(
            file=open(carfax_path, "rb"),
            purpose="assistants"
        )

        table_prompt = f"""
        Create an HTML table in the Car Cafe 3-column style: Details, Information, and Options.
        Always include VIN, Year, Make, Model, Mileage (last row), and Options.
        Use this style as a reference:

        <table style=\"width: 80%; border-collapse: collapse; font-family: Arial; border: 2px solid #ff8307;\">
        ...
        """

        description_prompt = f"""
        Write a clean, factual Car Cafe style vehicle description.
        Mention cleanliness, service history, condition, and tires.
        Use this HTML format:

        <h2 style='text-align: center; font-family: Arial; font-size: 28px;'>Description</h2>
        <p style='text-align: justify;'>...</p>
        """

        table_response = openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": table_prompt},
                        {"type": "file", "file_id": uploaded_pdf.id}
                    ]
                }
            ]
        )

        description_response = openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": description_prompt},
                        {"type": "file", "file_id": uploaded_pdf.id}
                    ]
                }
            ]
        )

        table_html = table_response.choices[0].message.content
        description_html = description_response.choices[0].message.content

        gallery_html = "\n".join([
            f'<img src="{url}" alt="Image {i+1:03d}" style="width: 500px; height: auto; border-radius: 5px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">'
            for i, url in enumerate(image_urls)
        ])

        video_html = ""
        if video_urls:
            video_html = f"""
            <video width="640" height="360" controls style="max-width: 100%; border-radius: 8px;">
                <source src="{video_urls[0]}" type="video/mp4">
            </video>
            """

        final_html = f"""
        <meta charset='utf-8'>
        <div style="font-family: Arial;">
            <p><img src='https://photos.carcafe-tx.com/Branding/CarCafeTemplateBanner' width='1500' height='500'></p>
            {table_html}
            <h2 style='text-align: center; font-size: 28px; margin-top: 50px;'>Description</h2>
            {description_html}
            <div style='margin: 30px 0;'>{video_html}</div>
            <h2 style='text-align: center; font-size: 28px;'>Gallery</h2>
            <div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;'>{gallery_html}</div>
            <p style='text-align: center; margin-top: 40px; font-size: 14px; color: #aaa;'>Created by Yousef Saad</p>
        </div>
        """

        return jsonify({"html": final_html}), 200

    except Exception as e:
        print("❌ ERROR:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
