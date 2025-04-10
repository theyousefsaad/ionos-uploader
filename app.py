from flask import Flask, request, jsonify
import os
import datetime
import tempfile
import paramiko
from openai import OpenAI
from werkzeug.utils import secure_filename

from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/upload": {"origins": "http://localhost:3000"}})
  # ✅ Allow all origins (good for testing)


# ==== SFTP Config ====
SFTP_HOST = "home558455723.1and1-data.host"
SFTP_PORT = 22
SFTP_USER = "u79546177"
SFTP_PASS = "Carcafe123!"

# ==== OpenAI Client ====
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@app.route("/", methods=["GET"])
def home():
    return "✅ CarCafe API is live"


def chat_with_pdf(prompt):
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a vehicle listing assistant for Car Cafe. Generate professional eBay-style HTML content."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


@app.route("/upload", methods=["POST"])
def upload():
    try:
        # === Get Form Fields ===
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

        # === Save Carfax PDF ===
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as carfax_temp:
            carfax_file.save(carfax_temp.name)
            carfax_path = carfax_temp.name

        # === Create Prompts ===
        table_prompt = f"""
Use the vehicle info below to generate an HTML table in Car Cafe’s orange 3-column style. Use <table> with orange borders and clean rows like this example:
<tr><td>Make</td><td>Ford</td><td>5.4L V8 CNG</td></tr>
<tr><td>Interior</td><td>Gray</td><td>Natural Gas</td></tr>
<tr><td>Miles</td><td>6,700</td><td>245/75R16 Tires</td></tr>

VIN: {vin}
Year: {year}
Make: {make}
Model: {model}
Mileage: {mileage}
Options: {options}
"""

        description_prompt = f"""
Write a professional Car Cafe vehicle description. Mention service history, tire condition, interior/exterior details. Don’t exaggerate. Sound factual and clean.

VIN: {vin}
Year: {year}
Make: {make}
Model: {model}
Mileage: {mileage}
Options: {options}
"""

        # === Get HTML from OpenAI ===
        table_html = chat_with_pdf(table_prompt)
        description_html = chat_with_pdf(description_prompt)

        # === Build Image Grid HTML ===
        gallery_html = "\n".join([
            f'<img src="{url}" alt="Image {i+1:03d}" style="width: 500px; height: auto; border-radius: 5px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">'
            for i, url in enumerate(image_urls)
        ])

        # === Build Video HTML ===
        video_html = ""
        if video_urls:
            video_html = f"""
            <video width="640" height="360" controls style="max-width: 100%; border-radius: 8px;">
                <source src="{video_urls[0]}" type="video/mp4">
            </video>
            """

        # === Final Template HTML ===
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
            <p style='text-align: center; margin-top: 40px; font-size: 14px; color: #aaa;'>Created by Yousef Saad 🚀</p>
        </div>
        """

        return jsonify({"html": final_html}), 200

    except Exception as e:
        print("❌ ERROR:", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
