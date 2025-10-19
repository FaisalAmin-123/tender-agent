# # api.py — imports (robust cross-version)
# import os
# import sys
# import traceback
# import logging
# from datetime import datetime
# from flask_cors import CORS

# # flask + helpers
# try:
#     # common: send_from_directory and abort come from flask
#     from flask import Flask, request, jsonify, render_template, send_from_directory, abort
#     # safe_join lives in werkzeug.utils on recent versions
#     try:
#         from werkzeug.utils import safe_join
#     except Exception:
#         # fallback for older/newer combos
#         try:
#             from flask.helpers import safe_join
#         except Exception:
#             # last resort: define a minimal safe_join that resolves path and ensures it's inside directory
#             import os
#             def safe_join(directory, *paths):
#                 final = os.path.abspath(os.path.join(directory, *paths))
#                 if not final.startswith(os.path.abspath(directory) + os.sep):
#                     raise ValueError("Resulting path is outside the directory")
#                 return final
# except Exception as _e:
#     print("❌ ERROR: Flask (or werkzeug) not available or import failed:", _e)
#     raise


# # Add current directory to path
# sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# # Import your modules
# try:
#     import main
#     import whatsapp_group_sender
#     print("✅ Successfully imported main.py and whatsapp_group_sender.py")
    
#     # Use the main function from main.py
#     scrape_anantnag_tenders = main.main
#     print("✅ Found scraping function: main.main()")
    
#     # Use the main function from whatsapp_group_sender.py
#     send_to_whatsapp = whatsapp_group_sender.main
#     print("✅ Found WhatsApp function: whatsapp_group_sender.main()")
        
# except ImportError as e:
#     print(f"❌ ERROR: Could not import modules: {e}")
#     print("Make sure main.py and whatsapp_group_sender.py are in the same folder!")
#     scrape_anantnag_tenders = None
#     send_to_whatsapp = None

# # Initialize Flask app
# app = Flask(__name__)
# CORS(app)

# # Set up logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# # Store execution history
# execution_history = []

# # ============================================================
# # ROUTES
# # ============================================================

# @app.route('/')
# def index():
#     """Serve the web UI homepage"""
#     return render_template('index.html')

# @app.route('/api/info')
# def api_info():
#     """Show API information"""
#     return jsonify({
#         "message": "Anantnag Tender Scraper API",
#         "status": "active",
#         "version": "1.0",
#         "endpoints": {
#             "web_ui": "GET /",
#             "scrape": "POST /api/scrape-tenders",
#             "status": "GET /api/status",
#             "health": "GET /api/health",
#             "info": "GET /api/info"
#         }
#     }), 200

# @app.route('/api/health', methods=['GET'])
# def health_check():
#     """Health check endpoint"""
#     return jsonify({
#         "status": "healthy",
#         "timestamp": datetime.now().isoformat()
#     }), 200
# @app.route('/pdfs/<path:filename>', methods=['GET'])
# def serve_pdf(filename):
#     """Serve a downloaded PDF from DOWNLOAD_DIR"""
#     download_dir = os.getenv("DOWNLOAD_DIR", "pdfs")
#     # Security: ensure path stays inside download_dir
#     try:
#         safe_path = safe_join(download_dir, filename)
#     except Exception:
#         return abort(404)
#     if not safe_path or not os.path.exists(safe_path):
#         return abort(404)
#     return send_from_directory(download_dir, filename, as_attachment=False)


# @app.route('/api/status', methods=['GET'])
# def get_status():
#     """Get execution status and history"""
#     try:
#         if not execution_history:
#             return jsonify({
#                 "status": "no_executions_yet",
#                 "message": "No tenders have been scraped yet",
#                 "total_executions": 0
#             }), 200
        
#         last_execution = execution_history[-1]
#         return jsonify({
#             "status": "success",
#             "last_execution": last_execution,
#             "total_executions": len(execution_history),
#             "recent_executions": execution_history[-5:]
#         }), 200
        
#     except Exception as e:
#         logger.error(f"Error getting status: {str(e)}")
#         return jsonify({
#             "status": "error",
#             "message": str(e)
#         }), 500

# @app.route('/api/scrape-tenders', methods=['POST'])
# def scrape_tenders():
#     """
#     Main scraping endpoint
    
#     POST /api/scrape-tenders
#     Body: {
#         "location": "anantnag",
#         "num_tenders": 10
#     }
#     """
#     start_time = datetime.now()
    
#     try:
#         # Get parameters from request
#         data = request.get_json() or {}
#         location = data.get('location', 'anantnag')
#         num_tenders = int(data.get('num_tenders', 10))
        
#         logger.info("=" * 60)
#         logger.info("Starting tender scraping")
#         logger.info("=" * 60)
#         logger.info(f"Location: {location}")
#         logger.info(f"Number of tenders requested: {num_tenders}")
        
#         # Validate parameters
#         if num_tenders < 1 or num_tenders > 100:
#             return jsonify({
#                 "status": "error",
#                 "message": "num_tenders must be between 1 and 100"
#             }), 400
        
#         # Check if functions are available
#         if scrape_anantnag_tenders is None:
#             return jsonify({
#                 "status": "error",
#                 "message": "Scraping function not found. Check main.py"
#             }), 500
        
#         if send_to_whatsapp is None:
#             return jsonify({
#                 "status": "error", 
#                 "message": "WhatsApp function not found. Check whatsapp_group_sender.py"
#             }), 500
        
#         # Update environment variable
#         if num_tenders != 10:
#             os.environ['MAX_PDFS'] = str(num_tenders)
#             logger.info(f"Updated MAX_PDFS to {num_tenders}")
        
#         # STEP 1: Scrape tenders
#         logger.info("Step 1: Scraping tenders from website...")
#         scrape_anantnag_tenders()
#         logger.info("Step 1 completed: Scraping finished")
        
#         # Check if PDFs were downloaded
#         pdf_dir = os.getenv("DOWNLOAD_DIR", "pdfs")
#         if not os.path.exists(pdf_dir):
#             logger.warning("PDF directory does not exist")
#             tender_files = []
#         else:
#             tender_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
#             logger.info(f"Found {len(tender_files)} PDFs in {pdf_dir}")
        
#         # Handle case where no tenders found
#         if not tender_files:
#             logger.warning("No tenders were downloaded")
#             execution_record = {
#                 "timestamp": start_time.isoformat(),
#                 "status": "no_tenders",
#                 "tenders_count": 0,
#                 "duration_seconds": (datetime.now() - start_time).total_seconds()
#             }
#             execution_history.append(execution_record)
            
#             return jsonify({
#                 "status": "warning",
#                 "message": "No new tenders found for Anantnag",
#                 "tenders_count": 0,
#                 "execution_time": execution_record["duration_seconds"]
#             }), 200
        
#         # STEP 2: Send to WhatsApp
#         logger.info("Step 2: Sending tenders to WhatsApp...")
#         send_to_whatsapp()
#         logger.info("Step 2 completed: WhatsApp sending finished")
        
#         # Record successful execution
#         execution_record = {
#             "timestamp": start_time.isoformat(),
#             "status": "success",
#             "tenders_count": len(tender_files),
#             "tender_files": tender_files,
#             "duration_seconds": (datetime.now() - start_time).total_seconds()
#         }
#         execution_history.append(execution_record)
        
#         # Keep only last 50 executions in memory
#         if len(execution_history) > 50:
#             execution_history.pop(0)
        
#         logger.info("=" * 60)
#         logger.info("Tender scraping completed successfully")
#         logger.info("=" * 60)
        
#         return jsonify({
#             "status": "success",
#             "message": f"Successfully processed {len(tender_files)} tenders and sent to WhatsApp",
#             "tenders_count": len(tender_files),
#             "tender_files": tender_files,
#             "execution_time": execution_record["duration_seconds"]
#         }), 200
        
#     except Exception as e:
#         error_msg = str(e)
#         error_trace = traceback.format_exc()
#         logger.error("=" * 60)
#         logger.error(f"ERROR in scraping: {error_msg}")
#         logger.error(f"Traceback: {error_trace}")
#         logger.error("=" * 60)
        
#         # Record failed execution
#         execution_record = {
#             "timestamp": start_time.isoformat(),
#             "status": "error",
#             "error": error_msg,
#             "duration_seconds": (datetime.now() - start_time).total_seconds()
#         }
#         execution_history.append(execution_record)
        
#         return jsonify({
#             "status": "error",
#             "message": f"Error occurred: {error_msg}",
#             "error_details": error_trace
#         }), 500

# # ============================================================
# # ERROR HANDLERS
# # ============================================================

# @app.errorhandler(404)
# def not_found(error):
#     """Handle 404 errors"""
#     return jsonify({
#         "status": "error",
#         "message": "Endpoint not found",
#         "code": 404
#     }), 404

# @app.errorhandler(500)
# def server_error(error):
#     """Handle 500 errors"""
#     return jsonify({
#         "status": "error",
#         "message": "Internal server error",
#         "code": 500
#     }), 500

# # ============================================================
# # MAIN
# # ============================================================

# if __name__ == '__main__':
#     print("\n" + "="*60)
#     print("🚀 ANANTNAG TENDER SCRAPER API")
#     print("="*60)
#     print("API is starting...")
#     print("\nAccess points:")
#     print("  Web UI: http://localhost:5000")
#     print("  API Info: http://localhost:5000/api/info")
#     print("  Health Check: http://localhost:5000/api/health")
#     print("\nStarting on all interfaces (0.0.0.0) on port 5000")
#     print("="*60 + "\n")
    
#     app.run(
#         host='0.0.0.0',
#         port=5000,
#         debug=True
#     )


# api.py — robust Flask API for Anantnag Tender Scraper (final version)


# api.py — imports (robust cross-version)
import os
import sys
import traceback
import logging
from datetime import datetime
from flask_cors import CORS
import subprocess
import base64
import sys
from functools import wraps

# flask + helpers
try:
    from flask import Flask, request, jsonify, render_template, send_from_directory, abort
    try:
        from werkzeug.utils import safe_join
    except Exception:
        try:
            from flask.helpers import safe_join
        except Exception:
            import os
            def safe_join(directory, *paths):
                final = os.path.abspath(os.path.join(directory, *paths))
                if not final.startswith(os.path.abspath(directory) + os.sep):
                    raise ValueError("Resulting path is outside the directory")
                return final
except Exception as _e:
    print("❌ ERROR: Flask (or werkzeug) not available or import failed:", _e)
    raise

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import your modules
scrape_anantnag_tenders = None
send_to_whatsapp = None
import whatsapp_group_sender

try:
    import main
    scrape_anantnag_tenders = main.main
    print("✅ Found scraping function: main.main()")
except Exception as e:
    print("⚠️ Could not import main.main():", e)

try:
    # whatsapp_group_sender exposes send_recent_pdfs_to_group and main (legacy)
    if hasattr(whatsapp_group_sender, "send_recent_pdfs_to_group"):
        send_to_whatsapp = whatsapp_group_sender.send_recent_pdfs_to_group
        print("✅ Found WhatsApp function: whatsapp_group_sender.send_recent_pdfs_to_group()")
    elif hasattr(whatsapp_group_sender, "main"):
        send_to_whatsapp = whatsapp_group_sender.main
        print("✅ Found WhatsApp function: whatsapp_group_sender.main() (fallback)")
except Exception as e:
    print("⚠️ Could not import whatsapp_group_sender properly:", e)

# Initialize Flask app
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Store execution history
execution_history = []

# ============================================================
# ROUTES
# ============================================================

@app.route('/')
def index():
    """Serve the web UI homepage"""
    return render_template('index.html')

@app.route('/api/info')
def api_info():
    """Show API information"""
    return jsonify({
        "message": "Anantnag Tender Scraper API",
        "status": "active",
        "version": "1.0",
        "endpoints": {
            "web_ui": "GET /",
            "scrape": "POST /api/scrape-tenders",
            "status": "GET /api/status",
            "health": "GET /api/health",
            "info": "GET /api/info",
            "whatsapp_groups": "GET /api/whatsapp/groups"
        }
    }), 200

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/api/whatsapp/groups', methods=['GET'])
def list_whatsapp_groups():
    """
    Return curated list of available WhatsApp groups from environment.
    """
    groups_raw = os.getenv("AVAILABLE_GROUPS", "")
    if not groups_raw:
        return jsonify({"groups": [], "message": "No configured groups"}), 200
    groups = [g.strip() for g in groups_raw.split("|") if g.strip()]
    return jsonify({"groups": groups}), 200

@app.route('/pdfs/<path:filename>', methods=['GET'])
def serve_pdf(filename):
    """Serve a downloaded PDF from DOWNLOAD_DIR"""
    download_dir = os.getenv("DOWNLOAD_DIR", "pdfs")
    try:
        safe_path = safe_join(download_dir, filename)
    except Exception:
        return abort(404)
    if not safe_path or not os.path.exists(safe_path):
        return abort(404)
    return send_from_directory(download_dir, filename, as_attachment=False)

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get execution status and history"""
    try:
        if not execution_history:
            return jsonify({
                "status": "no_executions_yet",
                "message": "No tenders have been scraped yet",
                "total_executions": 0
            }), 200

        last_execution = execution_history[-1]
        return jsonify({
            "status": "success",
            "last_execution": last_execution,
            "total_executions": len(execution_history),
            "recent_executions": execution_history[-5:]
        }), 200

    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/scrape-tenders', methods=['POST'])
def scrape_tenders():
    """
    Main scraping endpoint

    POST /api/scrape-tenders
    Body: {
        "location": "anantnag",
        "num_tenders": 10,
        "whatsapp_group": "Group Name (optional)"
    }
    """
    start_time = datetime.now()

    try:
        data = request.get_json() or {}
        location = data.get('location', 'anantnag')
        num_tenders = int(data.get('num_tenders', 10))
        whatsapp_group = data.get('whatsapp_group')  # may be None or empty string

        logger.info("=" * 60)
        logger.info("Starting tender scraping")
        logger.info("=" * 60)
        logger.info(f"Location: {location}")
        logger.info(f"Number of tenders requested: {num_tenders}")
        logger.info(f"Whatsapp group requested: {repr(whatsapp_group)}")

        if num_tenders < 1 or num_tenders > 100:
            return jsonify({
                "status": "error",
                "message": "num_tenders must be between 1 and 100"
            }), 400

        if scrape_anantnag_tenders is None:
            return jsonify({
                "status": "error",
                "message": "Scraping function not found. Check main.py"
            }), 500

        if send_to_whatsapp is None:
            logger.warning("WhatsApp sender function not found. Skipping WhatsApp send.")
            whatsapp_result = {"skipped": True, "reason": "whatsapp sender not available"}
        else:
            # Update MAX_PDFS for runtime (so main.main honors it)
            os.environ['MAX_PDFS'] = str(num_tenders)
            logger.info(f"Updated MAX_PDFS to {num_tenders}")

            # STEP 1: Scrape tenders
            logger.info("Step 1: Scraping tenders from website...")
            # call the scraping function (this is blocking)
            scrape_anantnag_tenders()
            logger.info("Step 1 completed: Scraping finished")

            # STEP: collect found pdfs
            pdf_dir = os.getenv("DOWNLOAD_DIR", "pdfs")
            if not os.path.exists(pdf_dir):
                logger.warning("PDF directory does not exist")
                tender_files = []
            else:
                tender_files = sorted([f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')])
                logger.info(f"Found {len(tender_files)} PDFs in {pdf_dir}")

            if not tender_files:
                logger.warning("No tenders were downloaded")
                execution_record = {
                    "timestamp": start_time.isoformat(),
                    "status": "no_tenders",
                    "tenders_count": 0,
                    "duration_seconds": (datetime.now() - start_time).total_seconds()
                }
                execution_history.append(execution_record)
                return jsonify({
                    "status": "warning",
                    "message": "No new tenders found for Anantnag",
                    "tenders_count": 0,
                    "execution_time": execution_record["duration_seconds"]
                }), 200

            # STEP 2: Send to WhatsApp
            logger.info("Step 2: Sending tenders to WhatsApp...")
            try:
                # send_to_whatsapp is expected to be whatsapp_group_sender.send_recent_pdfs_to_group
                # signature: (group_name, limit) -> dict
                if whatsapp_group:
                    whatsapp_result = send_to_whatsapp(whatsapp_group, limit=num_tenders)
                else:
                    # if no group provided, call with None (function should fall back to env default)
                    whatsapp_result = send_to_whatsapp(None, limit=num_tenders)
                logger.info("Step 2 completed: WhatsApp sending finished")
            except Exception as e:
                logger.exception("WhatsApp send failed")
                whatsapp_result = {"error": str(e)}

        # Record successful execution
        execution_record = {
            "timestamp": start_time.isoformat(),
            "status": "success",
            "tenders_count": len(tender_files),
            "tender_files": tender_files,
            "whatsapp_result": whatsapp_result,
            "duration_seconds": (datetime.now() - start_time).total_seconds()
        }
        execution_history.append(execution_record)

        if len(execution_history) > 50:
            execution_history.pop(0)

        logger.info("=" * 60)
        logger.info("Tender scraping completed successfully")
        logger.info("=" * 60)

        return jsonify({
            "status": "success",
            "message": f"Successfully processed {len(tender_files)} tenders and sent to WhatsApp",
            "tenders_count": len(tender_files),
            "tender_files": tender_files,
            "whatsapp_result": whatsapp_result,
            "execution_time": execution_record["duration_seconds"]
        }), 200

    except Exception as e:
        error_msg = str(e)
        error_trace = traceback.format_exc()
        logger.error("=" * 60)
        logger.error(f"ERROR in scraping: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        logger.error("=" * 60)

        execution_record = {
            "timestamp": start_time.isoformat(),
            "status": "error",
            "error": error_msg,
            "duration_seconds": (datetime.now() - start_time).total_seconds()
        }
        execution_history.append(execution_record)

        return jsonify({
            "status": "error",
            "message": f"Error occurred: {error_msg}",
            "error_details": error_trace
        }), 500

# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "message": "Endpoint not found",
        "code": 404
    }), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({
        "status": "error",
        "message": "Internal server error",
        "code": 500
    }), 500

# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 ANANTNAG TENDER SCRAPER API")
    print("="*60)
    print("API is starting...")
    print("\nAccess points:")
    print("  Web UI: http://localhost:5000")
    print("  API Info: http://localhost:5000/api/info")
    print("  Health Check: http://localhost:5000/api/health")
    print("\nStarting on all interfaces (0.0.0.0) on port 5000")
    print("="*60 + "\n")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
