from flask import Flask, request, jsonify, render_template
import requests
import re
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import time

app = Flask(__name__)

class FacebookProfileDownloader:
    def __init__(self, api_url="https://tools.xrespond.com/api/facebook/all-details"):
        self.api_url = api_url
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504, 429]
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01"
        }

    def get_profile_data(self, profile_url):
        start_time = time.time()
        payload = {"url": profile_url}
        try:
            response = self.session.post(self.api_url, data=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success" and not data["data"].get("error"):
                download_urls = {}
                profile_info = {}
                for entry in data["data"]["data"]:
                    if "result" in entry and "data" in entry["result"] and "user" in entry["result"]["data"]:
                        user_data = entry["result"]["data"]["user"]
                        if "profile_header_renderer" in user_data:
                            renderer = user_data["profile_header_renderer"]
                            if "user" in renderer:
                                user = renderer["user"]
                                download_urls = {
                                    "large": user.get("profilePicLarge", {}).get("uri"),
                                    "medium": user.get("profilePicMedium", {}).get("uri"),
                                    "small": user.get("profilePicSmall", {}).get("uri")
                                }
                                profile_info = {
                                    "name": user.get("name"),
                                    "joined": next((f["value"] for f in renderer.get("profile_directory_authenticity_modal", {}).get("header_fields", []) if f.get("profile_field_type") == "PROFILE_JOIN_DATE"), None),
                                    "updated": next((f["value"] for f in renderer.get("profile_directory_authenticity_modal", {}).get("header_fields", []) if f.get("profile_field_type") == "PROFILE_UPDATED_SINCE"), None),
                                    "locked": renderer.get("feed_banner", {}).get("title", {}).get("text", {}).get("text")
                                }
                                break
                time_taken = time.time() - start_time
                return {
                    "status": "success",
                    "data": {
                        "download_urls": download_urls,
                        "profile_info": profile_info,
                        "api_dev": "@ISmartCoder",
                        "updates_channel": "t.me/TheSmartDev",
                        "time_taken": f"{time_taken:.3f} seconds"
                    }
                }
            else:
                time_taken = time.time() - start_time
                return {
                    "status": "error",
                    "message": "Unable to retrieve profile data",
                    "api_dev": "@ISmartCoder",
                    "updates_channel": "t.me/TheSmartDev",
                    "time_taken": f"{time_taken:.3f} seconds"
                }
        except requests.exceptions.RequestException as e:
            time_taken = time.time() - start_time
            return {
                "status": "error",
                "message": str(e),
                "api_dev": "@ISmartCoder",
                "updates_channel": "t.me/TheSmartDev",
                "time_taken": f"{time_taken:.3f} seconds"
            }

def get_graph_api_profile_pic(profile_id):
    start_time = time.time()
    access_token = "6628568379|c1e620fa708a1d5696fb991c1bde5662"
    url = f"https://graph.facebook.com/{profile_id}/picture"
    params = {
        "redirect": "0",
        "height": "4000",
        "width": "4000",
        "type": "normal",
        "access_token": access_token
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        content_type = response.headers.get('content-type', '')
        if 'application/json' in content_type:
            data = response.json()
            if isinstance(data, dict) and 'data' in data and 'url' in data['data']:
                time_taken = time.time() - start_time
                return {
                    "status": "success",
                    "data": {
                        "download_url": data['data']['url'],
                        "api_dev": "@ISmartCoder",
                        "updates_channel": "t.me/TheSmartDev",
                        "time_taken": f"{time_taken:.3f} seconds"
                    }
                }
        image_url = response.text.strip().strip('"').replace('\\/', '/')
        if image_url.startswith('http'):
            time_taken = time.time() - start_time
            return {
                "status": "success",
                "data": {
                    "download_url": image_url,
                    "api_dev": "@ISmartCoder",
                    "updates_channel": "t.me/TheSmartDev",
                    "time_taken": f"{time_taken:.3f} seconds"
                }
            }
        time_taken = time.time() - start_time
        return {
            "status": "error",
            "message": "Invalid response format from Graph API",
            "api_dev": "@ISmartCoder",
            "updates_channel": "t.me/TheSmartDev",
            "time_taken": f"{time_taken:.3f} seconds"
        }
    except requests.exceptions.RequestException as e:
        time_taken = time.time() - start_time
        return {
            "status": "error",
            "message": f"Graph API request failed: {str(e)}",
            "api_dev": "@ISmartCoder",
            "updates_channel": "t.me/TheSmartDev",
            "time_taken": f"{time_taken:.3f} seconds"
        }

@app.route('/', methods=['GET'])
def welcome():
    return render_template('status.html')

@app.route('/dl', methods=['GET'])
def download_profile():
    profile_url = request.args.get('url')
    if not profile_url:
        return jsonify({
            "status": "error",
            "message": "Missing 'url' parameter",
            "api_dev": "@ISmartCoder",
            "updates_channel": "t.me/TheSmartDev"
        }), 400
    match = re.search(r"profile\.php\?id=(\d+)", profile_url)
    if match:
        profile_id = match.group(1)
        return jsonify(get_graph_api_profile_pic(profile_id))
    else:
        downloader = FacebookProfileDownloader()
        return jsonify(downloader.get_profile_data(profile_url))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
