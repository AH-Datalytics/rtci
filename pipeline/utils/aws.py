"""
Local-only replacement for aws.py — reads existing data from S3 (public),
writes new data to local disk instead of S3.
"""
import json
import os
import pandas as pd
import requests

BUCKET = "rtci"  # stub for scrapers that import this constant
BUCKET_URL = "https://rtci.s3.us-east-1.amazonaws.com/"
LOCAL_ROOT = os.path.join(os.path.expanduser("~"), "rtci_local_data")


def get_s3_client():
    """Stub — PDF scrapers import this but we don't need real S3 locally."""
    raise RuntimeError("S3 client not available in local/test mode")


def list_directories(prefix=""):
    """
    List S3 'directories' via XML listing.
    Falls back to empty list if access denied.
    """
    try:
        url = f"{BUCKET_URL}?list-type=2&prefix={prefix}&delimiter=/"
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            return []
        import xml.etree.ElementTree as ET
        root = ET.fromstring(resp.text)
        ns = root.tag.split('}')[0] + '}' if '}' in root.tag else ''
        return [cp.find(f'{ns}Prefix').text for cp in root.findall(f'{ns}CommonPrefixes')]
    except Exception:
        return []


def list_files(prefix=""):
    """
    List S3 files via XML listing.
    Falls back to empty list if access denied.
    """
    try:
        url = f"{BUCKET_URL}?list-type=2&prefix={prefix}"
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            return []
        import xml.etree.ElementTree as ET
        root = ET.fromstring(resp.text)
        ns = root.tag.split('}')[0] + '}' if '}' in root.tag else ''
        return [c.find(f'{ns}Key').text for c in root.findall(f'{ns}Contents')]
    except Exception:
        return []


def snapshot_json(logger, json_data, path, timestamp=None, filename=None):
    """Write JSON to local disk instead of S3."""
    if timestamp and not filename:
        path += str(timestamp)
    elif filename and not timestamp:
        path += str(filename)
    else:
        path += f"{timestamp}/{filename}"

    local_path = os.path.join(LOCAL_ROOT, path + ".json")
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, "w") as f:
        json.dump(json_data, f, indent=2, default=str)
    logger.info(f"saved locally: {local_path} ({len(json_data)} records)")


def snapshot_df(logger, df, path, timestamp=None, filename=None):
    """Write CSV to local disk instead of S3."""
    if timestamp and not filename:
        path += str(timestamp)
    elif filename and not timestamp:
        path += str(filename)
    else:
        path += f"{timestamp}/{filename}"

    local_path = os.path.join(LOCAL_ROOT, path + ".csv")
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    df.to_csv(local_path, index=False)
    logger.info(f"saved locally: {local_path} ({len(df)} rows)")

    # Also copy to Downloads
    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads", os.path.basename(local_path))
    df.to_csv(downloads_path, index=False)
    logger.info(f"also saved to: {downloads_path}")


def snapshot_pdf(logger, src_filename, path, timestamp=None, filename=None):
    """Write PDF to local disk instead of S3."""
    if timestamp and not filename:
        path += str(timestamp)
    elif filename and not timestamp:
        path += str(filename)
    else:
        path += f"{timestamp}/{filename}"

    local_path = os.path.join(LOCAL_ROOT, path + ".pdf")
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    import shutil
    shutil.copy2(src_filename, local_path)
    logger.info(f"saved locally: {local_path}")


def snapshot_fig(logger, fig, path, timestamp=None, filename=None):
    """Write Plotly figure to local disk instead of S3."""
    if timestamp and not filename:
        path += str(timestamp)
    elif filename and not timestamp:
        path += str(filename)
    else:
        path += f"{timestamp}/{filename}"

    local_path = os.path.join(LOCAL_ROOT, path + ".html")
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    html = fig.to_html(full_html=False, include_plotlyjs="cdn")
    with open(local_path, "w") as f:
        f.write(html)
    logger.info(f"saved locally: {local_path}")
