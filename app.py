from flask import Flask, request, jsonify
import os
import datetime
import paramiko
import tempfile
from werkzeug.utils import secure_filename
import openai

app = Flask(__name__)

# ==== SFTP Config ====
SFTP_HOST = "home558455723.1and1-data.host"
SFTP_PORT = 22
SFTP_USER = "u79546177"
SFTP_PASS = "Carcafe123!"

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/upload", methods=["POST"])
def upload():
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

    try:
        now = datetime.datetime.now()
        folder_year = now.strftime("%Y")
        vehicle_folder = f"{year}{make}{model}-{vin}"
        remote_base = f"/{folder_year}CarPhotos/{month}/{vehicle_folder}/"

        # ==== Connect to SFTP ====
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

        # ==== Upload Images ====
        image_urls = []
        for idx, file in enumerate(image_files, 1):
            ext = secure_filename(file.filename).split(".")[-1]
            new_name = f"{str(idx).zfill(3)}.{ext}"
            with tempfile.NamedTemporaryFile(delete=False) as temp:
                file.save(temp.name)
                sftp.put(temp.name, remote_base + new_name)
                os.remove(temp.name)
            image_urls.append(f"https://photos.carcafe-tx.com{remote_base}{new_name}")

        # ==== Upload Videos ====
        video_urls = []
        for file in video_files:
            original_name = secure_filename(file.filename)
            with tempfile.NamedTemporaryFile(delete=False) as temp:
                file.save(temp.name)
                sftp.put(temp.name, remote_base + original_name)
                os.remove(temp.name)
            video_urls.append(f"https://photos.carcafe-tx.com{remote_base}{original_name}")

        # ==== Save Carfax Temporarily ====
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as carfax_temp:
            carfax_file.save(carfax_temp.name)
            carfax_path = carfax_temp.name

        # ==== Send to OpenAI ====
        with open(carfax_path, "rb") as pdf_file:
            table_prompt = f"""
            Analyze this Carfax PDF and create an HTML vehicle detail table in the exact Car Cafe format with three columns (Details, Information, Options). Always keep mileage at the bottom.
            VIN: {vin}
            Year: {year}
            Make: {make}
            Model: {model}
            Mileage: {mileage}
            Options: {options}
            """

            description_prompt = f"""
            Read this Carfax PDF and write a clean, factual vehicle description in the Car Cafe style. Don't exaggerate. Mention how clean it is, highlight service history if any, interior/exterior details, and tires.
            VIN: {vin}
            Year: {year}
            Make: {make}
            Model: {model}
            Mileage: {mileage}
            Options: {options}
            """

            table_response = openai.ChatCompletion.create(
                model="gpt-4-vision-preview",
                messages=[
                    {"role": "system", "content": "You are an expert HTML formatter for vehicle listings."},
                    {"role": "user", "content": [
                        {"type": "text", "text": table_prompt},
                        {"type": "image_file", "image_file": {"file": pdf_file}}
                    ]},
                ],
                max_tokens=1500
            )

            pdf_file.seek(0)  # Reset to read again
            description_response = openai.ChatCompletion.create(
                model="gpt-4-vision-preview",
                messages=[
                    {"role": "system", "content": "You write clean, honest vehicle descriptions for online listings."},
                    {"role": "user", "content": [
                        {"type": "text", "text": description_prompt},
                        {"type": "image_file", "image_file": {"file": pdf_file}}
                    ]},
                ],
                max_tokens=1000
            )

        table_html = table_response.choices[0].message.content
        description_html = description_response.choices[0].message.content

        # ==== Generate photo grid HTML ====
        gallery_html = "\n".join([
            f'<img src="{url}" alt="Image {i+1:03d}" style="width: 500px; height: auto; border-radius: 5px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">'
            for i, url in enumerate(image_urls)
        ])

        # ==== Use first video (if exists) ====
        video_html = ""
        if video_urls:
            video_html = f'''
            <video width="640" height="360" controls style="max-width: 100%; border-radius: 8px;">
                <source src="{video_urls[0]}" type="video/mp4">
            </video>
            '''

        # ==== Final Template Injection ====
        full_html_template = f"""
        <meta charset='utf-8'>
        <div>
            <p><img src='https://photos.carcafe-tx.com/Branding/CarCafeTemplateBanner' width='1500' height='500'></p>
            {table_html}
            <h2 style='text-align: center; font-family: Arial; font-size: 28px; margin-top: 50px;'>Description</h2>
            {description_html}
            {video_html}
            <h2 style='text-align: center; font-family: Arial; font-size: 28px; margin-top: 50px;'>Gallery</h2>
            <div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; justify-content: center;'>
                {gallery_html}
            </div>
        </div>
        """

        return jsonify({"html": full_html_template}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
