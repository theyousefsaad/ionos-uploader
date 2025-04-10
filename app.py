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
            {"role": "system", "content": "You are a professional HTML generator for used car listings. Always use the exact orange table format and detailed, organized descriptions as used by Car Cafe."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

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

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as carfax_temp:
            carfax_file.save(carfax_temp.name)
            carfax_path = carfax_temp.name

        table_prompt = f"""
Using the vehicle info below, generate an HTML table in Car Cafe’s EXACT orange 3-column format (details, information, options). Use bold headers, orange #ff8307 borders, and match all styling from previous samples. Use this format as the template always: <table style="width: 80%; border-collapse: collapse; font-family: Arial, sans-serif; margin: 20px auto; border-radius: 8px; overflow: hidden; border: 2px solid #ff8307;">
  <thead>
    <tr style="background-color: #ff8307; color: white;">
      <th style="padding: 12px 15px; text-transform: uppercase; font-size: 16px; font-weight: bold; border: 2px solid #ff8307;">Details</th>
      <th style="padding: 12px 15px; text-transform: uppercase; font-size: 16px; font-weight: bold; border: 2px solid #ff8307;">Information</th>
      <th style="padding: 12px 15px; text-transform: uppercase; font-size: 16px; font-weight: bold; border: 2px solid #ff8307;">Options</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="padding: 12px 15px; text-align: center; font-weight: bold; border: 2px solid #ff8307;">VIN #</td>
      <td style="padding: 12px 15px; text-align: center; font-weight: bold; background-color: #fff; color: #333; border: 2px solid #ff8307;">1GCHK29U94E108866</td>
      <td style="padding: 12px 15px; text-align: center; border: 2px solid #ff8307;">2 Owner</td>
    </tr>
    <tr>
      <td style="padding: 12px 15px; text-align: center; font-weight: bold; border: 2px solid #ff8307;">Year</td>
      <td style="padding: 12px 15px; text-align: center; font-weight: bold; background-color: #fff; color: #333; border: 2px solid #ff8307;">2004</td>
      <td style="padding: 12px 15px; text-align: center; border: 2px solid #ff8307;">Accident Free</td>
    </tr>
    <tr>
      <td style="padding: 12px 15px; text-align: center; font-weight: bold; border: 2px solid #ff8307;">Make</td>
      <td style="padding: 12px 15px; text-align: center; font-weight: bold; background-color: #fff; color: #333; border: 2px solid #ff8307;">Chevrolet</td>
      <td style="padding: 12px 15px; text-align: center; border: 2px solid #ff8307;">6.0L V8</td>
    </tr>
    <tr>
      <td style="padding: 12px 15px; text-align: center; font-weight: bold; border: 2px solid #ff8307;">Model</td>
      <td style="padding: 12px 15px; text-align: center; font-weight: bold; background-color: #fff; color: #333; border: 2px solid #ff8307;">Silverado 2500 LS</td>
      <td style="padding: 12px 15px; text-align: center; border: 2px solid #ff8307;">4X4 Extended Cab</td>
    </tr>
    <tr>
      <td style="padding: 12px 15px; text-align: center; font-weight: bold; border: 2px solid #ff8307;">Exterior</td>
      <td style="padding: 12px 15px; text-align: center; font-weight: bold; background-color: #fff; color: #333; border: 2px solid #ff8307;">White</td>
      <td style="padding: 12px 15px; text-align: center; border: 2px solid #ff8307;">CD Player</td>
    </tr>
    <tr>
      <td style="padding: 12px 15px; text-align: center; font-weight: bold; border: 2px solid #ff8307;">Interior</td>
      <td style="padding: 12px 15px; text-align: center; font-weight: bold; background-color: #fff; color: #333; border: 2px solid #ff8307;">Gray Cloth</td>
      <td style="padding: 12px 15px; text-align: center; border: 2px solid #ff8307;">Cloth Seats</td>
    </tr>
    <tr>
      <td style="padding: 12px 15px; text-align: center; font-weight: bold; border: 2px solid #ff8307;">Transmission</td>
      <td style="padding: 12px 15px; text-align: center; font-weight: bold; background-color: #fff; color: #333; border: 2px solid #ff8307;">Automatic</td>
      <td style="padding: 12px 15px; text-align: center; border: 2px solid #ff8307;">Michelin Tires</td>
    </tr>
    <tr>
      <td style="padding: 12px 15px; text-align: center; font-weight: bold; border: 2px solid #ff8307;">Miles</td>
      <td style="padding: 12px 15px; text-align: center; font-weight: bold; background-color: #fff; color: #333; border: 2px solid #ff8307;">170,043</td>
      <td style="padding: 12px 15px; text-align: center; border: 2px solid #ff8307;">265/75R16 Tires</td>
    </tr>
  </tbody>
</table>
give me only the code for the table using the information given in the same style as always, always keep mileage at the bottom
VIN: {vin}
Year: {year}
Make: {make}
Model: {model}
Mileage: {mileage}
Options: {options}
"""

        description_prompt = f"""
Write a professional, factual, and clean vehicle description in the tone of Car Cafe. Mention condition, tires, service, interior/exterior. Structure it into 2-3 paragraphs with HTML <p> tags. Keep it consistent across all listings. Always make it look something like this: <p style="font-family: Arial, sans-serif; font-size: 16px; color: #555; line-height: 1.6; text-align: justify; max-width: 900px; margin: 20px auto;">
    Welcome to <strong>Car Cafe, LLC</strong>! We're proud to offer this clean and well-kept <strong>2004 Chevrolet Silverado 2500 LS</strong> 4x4 with a 6.0L V8 engine. This accident-free, two-owner truck stands out for its care and condition, inside and out.
</p>

<p style="font-family: Arial, sans-serif; font-size: 16px; color: #555; line-height: 1.6; text-align: justify; max-width: 900px; margin: 20px auto;">
    The interior features comfortable <strong>cloth seats</strong> and a reliable <strong>CD player</strong>, making every drive simple and functional. It’s equipped with a spacious <strong>Extended Cab</strong> layout for added versatility. This truck rides on a set of <strong>Michelin 265/75R16 tires</strong> that are in strong shape, offering durability and a confident drive.
</p>

<p style="font-family: Arial, sans-serif; font-size: 16px; color: #555; line-height: 1.6; text-align: justify; max-width: 900px; margin: 20px auto;">
    At <strong>Car Cafe</strong>, we focus on offering clean, dependable vehicles that have been properly maintained. Financing options are available for qualified buyers, and we can assist with nationwide shipping. Service contracts are available upon request. Feel free to reach out to us with any questions or to schedule a time to see it in person.
</p>
give me only the code for the description in the same style, given the infromation, dont use words like excellent or perfect, mention how clean everything is, keep it simple focusing on the key points without glazing. make this description a selling point for the vehicle and taking about how every aspect is above average 
VIN: {vin}
Year: {year}
Make: {make}
Model: {model}
Mileage: {mileage}
Options: {options}
"""

        table_html = chat_with_pdf(table_prompt)
        description_html = chat_with_pdf(description_prompt)

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
            <img alt="" height="100" src="https://photos.carcafe-tx.com/Branding/Call%20us%20to%20schedule%20a%20live%20facetime%20video%20(3).png" width="600" class="auto-style7">
            <h2 style='text-align: center; font-size: 28px;'>Gallery</h2>
            <div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;'>{gallery_html}</div>
            </body>
</html>

<!-- About Us Section -->
<h2 style="text-align: center; font-family: Arial, sans-serif; font-size: 32px; color: #333; margin-top: 50px; font-weight: bold;">About Us</h2>

<p style="font-family: Arial, sans-serif; font-size: 18px; color: #555; line-height: 1.6; text-align: center; max-width: 900px; margin: 20px auto;">
    Car Cafe, LLC maintains a high quantity of quality used vehicles. Our fine pre-owned vehicles come to us as new-car franchise trade-ins, off lease, and package programs. Car Cafe inspects each vehicle for reliability and durability. We assure you satisfaction at the time of delivery and welcome pre-purchase inspections. Vehicles are accurately described on each individual listing. Car Cafe's descriptions and mass quantity of photos really allow our customers to feel comfortable and confident with what they are purchasing.
</p>

<p style="font-family: Arial, sans-serif; font-size: 18px; color: #555; line-height: 1.6; text-align: center; max-width: 900px; margin: 20px auto;">
    We invite you to take advantage of the tremendous savings found at Car Cafe, LLC. Please, before buying, carefully read the complete contents of our listing. We welcome all dealers and qualified individuals to make us an offer today! We look forward to speaking with you!
</p>

<!-- Image that Links to Another Page -->
<div style="text-align: center; margin: 30px 0;">
  <a href="https://youtu.be/1IAWKMAt8ak?si=bLYR3Dt7HrPMSwDX" target="_blank">
    <img src="https://photos.carcafe-tx.com/Branding/carcafe%20video%20thumbnail.png" alt="About Us Image" style="width: 50%; height: auto; border-radius: 8px;">
  </a>
</div>



</font><font size="4" rwr="1" style="font-family: Arial; font-size: 14pt;">

&lt;<table width="100%" height="107" bordercolor="#000000" border="4" bordercolorlight="#000000" bordercolordark="#000000" style="font-family: Arial; font-size: 14pt;">
  <tbody>
    <tr>
      <td width="100%" height="19" bordercolorlight="#000000" bordercolordark="#000000" bordercolor="#000000">
        <p align="center"><b><font size="4">WARRANTYY</font></b></p>
      </td>
    </tr>
    <tr>
      <td width="100%" height="76" bordercolorlight="#000000" bordercolordark="#000000" bordercolor="#000000">
        <table width="100%" height="107" bordercolor="#000000" border="4" bordercolorlight="#000000" bordercolordark="#000000">
          <tbody>
            <tr>
              <td width="100%" height="76" bordercolorlight="#000000" bordercolordark="#000000" bordercolor="#000000"><font color="#000000" size="4">This 
                vehicle is being sold as is, where is with no warranty, 
                expressed written or implied. The seller shall not be 
                responsible for the correct description, authenticity, 
                genuineness, or defects herein, and makes no warranty in 
                connection therewith. Please refer to our photos or call for 
                exact options and equipment on this vehicle. Options listed for 
                this vehicle may be inaccurate due to our high volume of 
                advertising, however we try our best to list the options and 
                equipment as accurately as possible. No allowance or set aside 
                will be made on account of any incorrectness, imperfection, 
                defect or damage. Any descriptions or representations are for 
                identification purposes only and are not to be construed as a 
                warranty of any type. It is the responsibility of the buyer to 
                have thoroughly inspected the vehicle, and to have satisfied 
                himself or herself as to the condition and value and to bid 
                based upon that judgment solely. The seller shall and will make 
                every reasonable effort to disclose any known defects associated 
                with this vehicle at the buyer's request prior to the close of 
                sale. Seller assumes no responsibility for any repairs 
                regardless of any oral statements about the vehicle.&nbsp;&nbsp;</font></td>
            </tr>
          </tbody>
        </table>
      </td>
    </tr>
  </tbody>
</table>
<table width="100%" bordercolor="#ff0000" border="4" bordercolorlight="#FF0000" bordercolordark="#FF0000" style="font-family: Arial; font-size: 14pt;">
  <tbody>
    <tr>
      <td width="100%" bordercolor="#FF0000">
        <p align="center"><font color="#ff0000" size="4"><b>ABOUT CAR CAFE, LLCC</b></font></p>
      </td>
    </tr>
    <tr>
      <td width="100%" bordercolor="#FF0000">Car Cafe, LLC maintains a high 
        quantity of quality used vehicles. Our fine pre-owned vehicles come to 
        us as new-car franchise trade-ins off lease and package programs. Car 
        Cafe inspects each vehicle for reliability and durability. We assure you 
        satisfaction at the time of delivery and welcome pre-purchase 
        inspections. Vehicles are accurately described on each individual 
        listing. Car Cafe's descriptions and mass quantity of photos really 
        allows our customers to feel comfortable and confident with what they 
        are purchasing. We invite you to take advantage of the tremendous 
        savings found at Car Cafe, LLC. Please before buying, carefully read the 
        complete contents of our listing. We welcome all dealers and qualified 
        individuals to make us an offer today! We look forward to speaking with 
        you!!</td>
    </tr>
  </tbody>
</table>
<table width="100%" bordercolor="#0000ff" border="4" bordercolorlight="#0000FF" bordercolordark="#0000FF" style="font-family: Arial; font-size: 14pt;">
  <tbody>
    <tr>
      <td width="100%">
        <p align="center"><b><font size="4">TERMS AND CONDITIONS</font></b></p>
      </td>
    </tr>
    <tr>
      <td width="100%"><span class="style24"><strong>PAYMENT OPTIONS&nbsp;&nbsp;</strong></span><br>
        -We accept the following payment options: Cashiers Checks/Money orders, 
        Verified funds from known financial institutions, and Cashh
        <p class="style24"><strong>VEHICLE PICKUP AND SHIPPING&nbsp;&nbsp;</strong></p>
        <p>-All shipping charges are the buyers responsibility&nbsp;&nbsp;</p>
        <p class="style24"><strong>GENERAL TERMSS</strong></p>
        <p>-Successful high bidder should contact Car Cafe, LLC&nbsp;within 24 
        hours, or next business day after the auction has ended to make 
        arrangements to complete the transaction..</p>
        <p>-&nbsp;Within 24 hours following the end of the auction, a $500 
        non-refundable deposit shall be sent over-night express in the form of 
        PayPal, Cashiers Check, or certified funds. If a deposit is not 
        received, and an alternate arrangement has not been made, the vehicle 
        will be made available to other potential buyers on a first-come, 
        first-serve basis..</p>
        <p>-All financial transactions should be completed within a reasonable 
        period of time, usually within 7 days after the auction..</p>
        <p>-Buyer is responsible for transportation to our location, which 
        includes taxi fares, rental car etc. Contact us if you require any 
        special assistance..</p>
        <p>-Seller accepts Cashier's Check, Certified funds, or verified funds 
        from known financial institutions, and cashh</p>
        <p>-Car Cafe, LLC discloses as much information as possible about our 
        vehicles. We welcome pre-purchase on site inspections by competent 
        parties. All vehicles are available for inspection by appointment. Buyer 
        is responsible for fees and charges of inspections made..</p>
        <p>-You are entering a legal and binding contract to purchase the 
        vehicle described above once your offer has been accepted..</p>
        <p>-If you are paying with a loan check, please be pre-approved on your 
        loan before making an offer. We do not accept RoadLoans!!</p>
        <p>-Unqualified bidding, Fake bidders, Auction interference, Shill 
        bidding, or any form of harassment can be subject to legal prosecution..</p>

        <p>-We offer shipping anywhere in the United States. The companies we 
        use offer a direct to your door delivery service, are fully insured and 
        licensed and bonded. Please contact us for a quote..</p>
        <p class="style24"><strong>FEES AND TAXESS</strong></p>
        <p>-All buyers pay a V.I.T. (Vehicle Inventory Tax) which is 0.002256 of 
        the purchase price (example $10,000 purchase = $22.56), a Documentary 
        Fee, and a $90 Administrative feee</p>
        <p><strong>TEXAS BUYERSS</strong>: There is a 6.26% sales tax. All Tax, 
        Title, and License fees apply..</p>
        <p>-Out of state buyers are responsible for their own taxes in their own 
        state..</p>
        <p>-We do provide temporary plates!&nbsp;&nbsp;</p>
      </td>
    </tr>
  </tbody>
</table>

<p style="color: rgb(0, 0, 0); font-family: &quot;Times New Roman&quot;; font-size: medium; font-style: normal; font-variant-ligatures: normal; font-variant-caps: normal; font-weight: 400; letter-spacing: normal; orphans: 2; text-align: start; text-indent: 0px; text-transform: none; widows: 2; word-spacing: 0px; -webkit-text-stroke-width: 0px; white-space: normal; text-decoration-thickness: initial; text-decoration-style: initial; text-decoration-color: initial;">&nbsp;
</p>
<p style="color: rgb(0, 0, 0); font-family: &quot;Times New Roman&quot;; font-size: medium; font-style: normal; font-variant-ligatures: normal; font-variant-caps: normal; font-weight: 400; letter-spacing: normal; orphans: 2; text-align: start; text-indent: 0px; text-transform: none; widows: 2; word-spacing: 0px; -webkit-text-stroke-width: 0px; white-space: normal; text-decoration-thickness: initial; text-decoration-style: initial; text-decoration-color: initial;">&nbsp;</p></font>
            <p style='text-align: center; margin-top: 40px; font-size: 14px; color: #aaa;'>Created by Yousef Saad 🚀</p>
        </div>
        """

        return jsonify({"html": final_html}), 200

    except Exception as e:
        print("❌ ERROR:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
