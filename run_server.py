"""Start the poultry defect detection web server."""

from web.backend.app import app

if __name__ == "__main__":
    print("Poultry Carcass Defect Detection — http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
