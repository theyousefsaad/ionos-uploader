from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "IONOS Uploader is running"

@app.route("/upload", methods=["POST"])
def upload():
    data = request.get_json()

    # Extract input values
    vin = data.get("vin")
    year = data.get("year")
    month = data.get("month")
    make = data.get("make")
    model = data.get("model")

    # Check required fields
    if not vin or not year or not month or not make or not model:
        return jsonify({"error": "Missing one or more required fields: vin, year, month, make, model"}), 400

    # Clean and format model name (remove spaces, title-case optional)
    model_name = f"{year}{make}{model}".replace(" ", "")

    # Construct full IONOS path
    folder_path = f"/photos/2025CarPhotos/{month}/{model_name}-{vin}"

    # Respond with folder path for your Python uploader or for Glide to use later
    return jsonify({
        "message": "Upload path generated successfully",
        "folder_path": folder_path
    }), 200

if __name__ == "__main__":
    import os

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)


