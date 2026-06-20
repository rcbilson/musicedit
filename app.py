#!/usr/bin/env python3
import os
import json
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory

CHOIR_ROOT = os.environ.get("CHOIR_ROOT", os.path.expanduser("~/choir"))

app = Flask(__name__, static_folder="static")


def get_root():
    return Path(CHOIR_ROOT).expanduser().resolve()


def file_tree(root: Path, base: Path):
    entries = []
    try:
        for child in sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            rel = str(child.relative_to(base))
            if child.is_dir():
                entries.append({
                    "name": child.name,
                    "path": rel,
                    "type": "dir",
                    "children": file_tree(child, base),
                })
            else:
                entries.append({
                    "name": child.name,
                    "path": rel,
                    "type": "file",
                })
    except PermissionError:
        pass
    return entries


def safe_path(rel: str) -> Path:
    root = get_root()
    target = (root / rel).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        raise ValueError("Path escape attempt")
    return target


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/files")
def list_files():
    root = get_root()
    return jsonify(file_tree(root, root))


@app.route("/api/file", methods=["GET"])
def read_file():
    path = request.args.get("path", "")
    if not path:
        return jsonify({"error": "missing path"}), 400
    try:
        target = safe_path(path)
        content = target.read_text(errors="replace")
        return jsonify({"content": content})
    except (ValueError, FileNotFoundError) as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/file", methods=["POST"])
def write_file():
    data = request.get_json()
    if not data or "path" not in data or "content" not in data:
        return jsonify({"error": "missing path or content"}), 400
    try:
        target = safe_path(data["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(data["content"])
        return jsonify({"ok": True})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/file/create", methods=["POST"])
def create_file():
    data = request.get_json()
    if not data or "path" not in data:
        return jsonify({"error": "missing path"}), 400
    try:
        target = safe_path(data["path"])
        if target.exists():
            return jsonify({"error": "file already exists"}), 409
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(data.get("content", ""))
        return jsonify({"ok": True})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/dir/create", methods=["POST"])
def create_dir():
    data = request.get_json()
    if not data or "path" not in data:
        return jsonify({"error": "missing path"}), 400
    try:
        target = safe_path(data["path"])
        if target.exists():
            return jsonify({"error": "directory already exists"}), 409
        target.mkdir(parents=True)
        return jsonify({"ok": True})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
