# flask_app.py
from flask import Flask, jsonify, request, send_from_directory
import os
from whatsapp_group_sender import list_visible_groups, send_recent_pdfs_to_group, gather_recent_pdfs

app = Flask(__name__, static_folder="static", template_folder="templates")

@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/api/whatsapp/groups", methods=["GET"])
def api_groups():
    # quick wrapper: returns visible groups or error
    res = list_visible_groups(timeout=20)
    if "error" in res:
        return jsonify({"status": "error", "message": res["error"]}), 500
    return jsonify({"status": "ok", "groups": res.get("groups", [])})

@app.route("/api/whatsapp/send", methods=["POST"])
def api_send():
    data = request.get_json() or {}
    group = data.get("group")
    limit = int(data.get("limit", 5))
    if not group:
        return jsonify({"status": "error", "message": "missing 'group' parameter"}), 400
    res = send_recent_pdfs_to_group(group, limit=limit)
    if "error" in res:
        return jsonify({"status": "error", "message": res["error"]}), 500
    return jsonify({"status": "ok", "sent": res.get("sent", [])})

# convenience route to serve downloaded pdfs to UI links
@app.route("/pdfs/<path:filename>")
def serve_pdfs(filename):
    pdf_dir = os.getenv("DOWNLOAD_DIR", os.getenv("PDF_DIR", "pdfs"))
    return send_from_directory(pdf_dir, filename, as_attachment=False)

# serve index page
@app.route("/")
def index():
    return app.send_static_file("index.html")  # if you serve via static; or use render_template

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
