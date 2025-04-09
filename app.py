from flask import Flask, request, jsonify
import os
import datetime
import tempfile
import paramiko
import traceback
from werkzeug.utils import secure_filename
from openai import OpenAI

app = Flask(__name__)

# === SFTP CONFIG ===
SFTP_HOST = "home558455723.1and1-data.host"
SFTP_PORT = 22
SFTP_USER = "u79546177"
SFTP_PASS = "Carcafe123!"

# === OpenAI Client ===
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/", methods=["GET"])
def home():
    return "✅ CarCafe API is live"

def chat_with_pdf(prompt, file_path):
    with open(file_path, "rb") as pdf_file:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a vehicle listing assistant for Car Cafe."},
                {"role": "user", "content": prompt}
            ],
            tools=[{
                "type": "file_search"
            }],
            tool_choice="auto",
            files=[pdf_file]
        )
    return response.choices[0].message.content

@app.route("/upload", methods=["POST"])
def upload():
    try:
        # === Get Form Data ===
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

        # === Folder Setup ===
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

        # === PROMPT TEMPLATES ===
        table_prompt = f"""
Please analyze the attached Carfax PDF and generate an HTML vehicle detail table in the Car Cafe format.

✅ Example:
<table style='width: 80%; margin: 20px auto; border: 2px solid #ff8307; border-collapse: collapse; font-family: Arial;'>
<thead><tr style='background: #ff8307; color: white;'>
<th style='padding: 12px; border: 2px solid #ff8307;'>Details</th>
<th style='padding: 12px; border: 2px solid #ff8307;'>Information</th>
<th style='padding: 12px; border: 2px solid #ff8307;'>Options</th>
</tr></thead>
<tbody>
<tr><td style='padding: 12px; border: 2px solid #ff8307;'>VIN #</td><td style='padding: 12px; border: 2px solid #ff8307;'>{vin}</td><td style='padding: 12px; border: 2px solid #ff8307;'>1 Owner</td></tr>
<tr><td style='padding: 12px; border: 2px solid #ff8307;'>Year</td><td style='padding: 12px; border: 2px solid #ff8307;'>{year}</td><td style='padding: 12px; border: 2px solid #ff8307;'>Clean Title</td></tr>
<tr><td style='padding: 12px; border: 2px solid #ff8307;'>Make</td><td style='padding: 12px; border: 2px solid #ff8307;'>{make}</td><td style='padding: 12px; border: 2px solid #ff8307;'>Low Miles</td></tr>
<tr><td style='padding: 12px; border: 2px solid #ff8307;'>Model</td><td style='padding: 12px; border: 2px solid #ff8307;'>{model}</td><td style='padding: 12px; border: 2px solid #ff8307;'>{options}</td></tr>
<tr><td style='padding: 12px; border: 2px solid #ff8307;'>Mileage</td><td style='padding: 12px; border: 2px solid #ff8307;'>{mileage}</td><td style='padding: 12px; border: 2px solid #ff8307;'>Warranty Eligible</td></tr>
</tbody></table>
""".strip()

        description_prompt = f"""
Read the attached Carfax PDF and write a clean, honest vehicle description in Car Cafe style. Mention:

- Cleanliness
- Service history
- Interior/exterior condition
- Tires

VIN: {vin}
Year: {year}
Make: {make}
Model: {model}
Mileage: {mileage}
Options: {options}

✅ Example style:
Welcome to Car Cafe! We're proud to offer this well-maintained 2014 Ford E350. It's accident-free and shows signs of careful ownership. Inside, you'll find a clean gray interior, cold AC, and well-preserved seats. The tires are in great shape. A great pick for anyone seeking value and reliability.
""".strip()

        # === Call OpenAI for table + description
        table_html = chat_with_pdf(table_prompt, carfax_path)
        description_html = chat_with_pdf(description_prompt, carfax_path)

        # === Generate photo grid
        gallery_html = "\n".join([
            f'<img src="{url}" style="width: 500px; height: auto; border-radius: 5px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">'
            for url in image_urls
        ])

        video_html = ""
        if video_urls:
            video_html = f"""
            <video width="640" height="360" controls style="max-width: 100%; border-radius: 8px;">
                <source src="{video_urls[0]}" type="video/mp4">
            </video>
            """

        # === Final HTML
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
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
