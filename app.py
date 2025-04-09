from flask import Flask, request, jsonify
import os
import datetime
import tempfile
import paramiko
import openai
import traceback
from werkzeug.utils import secure_filename

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

SFTP_HOST = "home558455723.1and1-data.host"
SFTP_PORT = 22
SFTP_USER = "u79546177"
SFTP_PASS = "Carcafe123!"

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

        # === Connect to SFTP ===
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

        # === Upload Images ===
        image_urls = []
        for idx, file in enumerate(image_files, 1):
            ext = secure_filename(file.filename).split(".")[-1]
            new_name = f"{str(idx).zfill(3)}.{ext}"
            with tempfile.NamedTemporaryFile(delete=False) as temp:
                file.save(temp.name)
                sftp.put(temp.name, remote_base + new_name)
                os.remove(temp.name)
            image_urls.append(f"https://photos.carcafe-tx.com{remote_base}{new_name}")

        # === Upload Videos ===
        video_urls = []
        for file in video_files:
            original_name = secure_filename(file.filename)
            with tempfile.NamedTemporaryFile(delete=False) as temp:
                file.save(temp.name)
                sftp.put(temp.name, remote_base + original_name)
                os.remove(temp.name)
            video_urls.append(f"https://photos.carcafe-tx.com{remote_base}{original_name}")

        # === Save Carfax ===
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as carfax_temp:
            carfax_file.save(carfax_temp.name)
            carfax_path = carfax_temp.name

        html_example = """
        <table style='width:80%; border:2px solid #ff8307; margin:auto; border-collapse:collapse;'>
        <thead><tr style='background-color:#ff8307; color:white;'>
        <th>Details</th><th>Information</th><th>Options</th></tr></thead>
        <tbody><tr><td>Year</td><td>2014</td><td>1 Owner</td></tr>
        <tr><td>Make</td><td>Ford</td><td>Backup Camera</td></tr>
        <tr><td>Model</td><td>E350</td><td>Clean Title</td></tr>
        <tr><td>Mileage</td><td>72,500</td><td>Bluetooth</td></tr></tbody></table>
        """

        table_prompt = f"""
        Generate a clean HTML table using this format:\n{html_example}\n
        VIN: {vin}, Year: {year}, Make: {make}, Model: {model}, Mileage: {mileage}, Options: {options}
        """

        description_prompt = f"""
        Write a vehicle description in Car Cafe style. Mention cleanliness, tires, service history, interior/exterior condition.
        VIN: {vin}, Year: {year}, Make: {make}, Model: {model}, Mileage: {mileage}, Options: {options}
        """

        # === GPT-4 Vision request (new SDK)
        with open(carfax_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()

        def chat_with_pdf(prompt):
            return openai.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {"role": "system", "content": "You format clean vehicle listings in HTML."},
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "file", "file": {"name": "carfax.pdf", "content": pdf_bytes}},
                    ]}
                ],
                max_tokens=1500
            )

        table_resp = chat_with_pdf(table_prompt)
        description_resp = chat_with_pdf(description_prompt)

        table_html = table_resp.choices[0].message.content
        description_html = description_resp.choices[0].message.content

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
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
