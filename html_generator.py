def generate_html_template(data):
    year = data.get("year", "")
    make = data.get("make", "")
    model = data.get("model", "")
    vin = data.get("vin", "")
    mileage = data.get("mileage", "")
    options = data.get("options", [])
    image_urls = data.get("image_urls", [])
    video_url = data.get("video_url", "")
    carfax_url = data.get("carfax_url", "")
    month = data.get("month", "")

    vehicle_folder = f"{year}{make}{model}-{vin}"
    base_path = f"https://photos.carcafe-tx.com/2025CarPhotos/{month}/{vehicle_folder}"

    options_html = "".join([f"<li>{opt}</li>" for opt in options])

    gallery_html = "\n".join([
        f'<img src="{url}" alt="Image {str(i+1).zfill(3)}" style="width: 100%; max-width: 500px; height: auto; border-radius: 5px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">'
        for i, url in enumerate(image_urls)
    ])

    html_template = f"""
    <meta charset=\"utf-8\">
    <div class=\"auto-style4\">
      <p><img alt=\"\" height=\"500\" src=\"https://photos.carcafe-tx.com/Branding/CarCafeTemplateBanner\" width=\"1500\"></p>

      <!-- VEHICLE DETAILS TABLE -->
      <table style=\"width: 80%; margin: auto; border: 2px solid #ff8307; font-family: Arial, sans-serif; border-collapse: collapse;\">
        <thead>
          <tr style=\"background-color: #ff8307; color: white;\">
            <th>Details</th><th>Information</th><th>Options</th>
          </tr>
        </thead>
        <tbody>
          <tr><td>VIN #</td><td>{vin}</td><td>{options[0] if options else ''}</td></tr>
          <tr><td>Year</td><td>{year}</td><td>{options[1] if len(options) > 1 else ''}</td></tr>
          <tr><td>Make</td><td>{make}</td><td>{options[2] if len(options) > 2 else ''}</td></tr>
          <tr><td>Model</td><td>{model}</td><td>{options[3] if len(options) > 3 else ''}</td></tr>
          <tr><td>Miles</td><td>{mileage}</td><td>{options[4] if len(options) > 4 else ''}</td></tr>
        </tbody>
      </table>

      <!-- DESCRIPTION -->
      <h2 style=\"text-align: center; font-family: Arial; font-size: 28px; margin-top: 50px;\">Description</h2>
      <p style=\"font-family: Arial; font-size: 16px; color: #555; line-height: 1.6; max-width: 900px; margin: auto;\">
        Welcome to <strong>Car Cafe, LLC</strong>! We're proud to offer this well-maintained <strong>{year} {make} {model}</strong>. This vehicle is in excellent condition with {mileage} miles and features:
      </p>
      <ul style=\"max-width: 900px; margin: 20px auto; color: #555; font-family: Arial; font-size: 16px;\">
        {options_html}
      </ul>

      <!-- VIDEO -->
      <div style=\"display: flex; justify-content: center; margin: 30px 0;\">
        <video width=\"640\" height=\"360\" controls style=\"max-width: 100%; border-radius: 8px;\">
          <source src=\"{video_url}\" type=\"video/mp4\">
        </video>
      </div>

      <!-- CALL BANNER -->
      <div style=\"display: flex; justify-content: center; margin: 30px 40px;\">
        <img src=\"https://photos.carcafe-tx.com/Branding/Call%20us%20to%20schedule%20a%20live%20facetime%20video%20(3).png\" style=\"width: 100%; max-width: 600px; height: auto;\">
      </div>

      <!-- GALLERY -->
      <h2 style=\"text-align: center; font-family: Arial; font-size: 28px;\">Gallery</h2>
      <div style=\"display: grid; grid-template-columns: 1fr 1fr; gap: 20px;\">
        {gallery_html}
      </div>

      <!-- ABOUT US -->
      <h2 style=\"text-align: center; font-family: Arial; font-size: 32px; margin-top: 50px;\">About Us</h2>
      <p style=\"font-family: Arial; font-size: 18px; text-align: center; max-width: 900px; margin: auto;\">
        Car Cafe, LLC offers quality used vehicles. Inspected for reliability, our vehicles are available with financing and nationwide shipping.
      </p>

      <!-- CONTACT THUMBNAIL -->
      <div style=\"text-align: center; margin: 30px 0;\">
        <a href=\"https://youtu.be/1IAWKMAt8ak?si=bLYR3Dt7HrPMSwDX\" target=\"_blank\">
          <img src=\"https://photos.carcafe-tx.com/Branding/carcafe%20video%20thumbnail.png\" alt=\"About Us Image\" style=\"width: 50%; border-radius: 8px;\">
        </a>
      </div>
    </div>
    """

    return html_template
