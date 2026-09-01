import json
import os
import uuid
import logging
import threading
import urllib.request
import urllib.error
from datetime import datetime

TRACKER_URL = ""
DATA_DIR = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'PhotoClear')
USAGE_FILE = os.path.join(DATA_DIR, 'usage.json')


class UsageTracker:
    def __init__(self, version="0.0.1"):
        self.version = version
        self._ensure_dir()
        self.install_id = self._get_or_create_id()
        self.data = self._load()

    def _ensure_dir(self):
        os.makedirs(DATA_DIR, exist_ok=True)

    def _get_or_create_id(self):
        if os.path.exists(USAGE_FILE):
            try:
                with open(USAGE_FILE, 'r', encoding='utf-8') as f:
                    d = json.load(f)
                    if 'install_id' in d:
                        return d['install_id']
            except Exception:
                pass
        return str(uuid.uuid4())

    def _load(self):
        if os.path.exists(USAGE_FILE):
            try:
                with open(USAGE_FILE, 'r', encoding='utf-8') as f:
                    d = json.load(f)
                    d.setdefault('install_id', self.install_id)
                    d.setdefault('launch_count', 0)
                    d.setdefault('total_images', 0)
                    d.setdefault('batches', 0)
                    return d
            except Exception:
                pass
        return {
            'install_id': self.install_id,
            'launch_count': 0,
            'total_images': 0,
            'batches': 0,
            'first_launch': datetime.now().isoformat(),
            'last_launch': None,
        }

    def _save(self):
        try:
            with open(USAGE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _send_remote(self, event, extra):
        if not TRACKER_URL:
            return
        payload = {
            'install_id': self.install_id,
            'event': event,
            'version': self.version,
            'timestamp': datetime.now().isoformat(),
            **extra,
        }

        def _post():
            try:
                req = urllib.request.Request(
                    TRACKER_URL,
                    data=json.dumps(payload).encode('utf-8'),
                    headers={'Content-Type': 'application/json'},
                    method='POST',
                )
                urllib.request.urlopen(req, timeout=5)
            except Exception:
                pass

        t = threading.Thread(target=_post, daemon=True)
        t.start()

    def track_launch(self):
        self.data['launch_count'] += 1
        self.data['last_launch'] = datetime.now().isoformat()
        self.data['version'] = self.version
        self._save()
        self._send_remote('launch', {'launch_count': self.data['launch_count']})
        logging.info(f"使用统计: 第 {self.data['launch_count']} 次启动")

    def track_process(self, image_count):
        self.data['total_images'] += image_count
        self.data['batches'] += 1
        self._save()
        self._send_remote('process', {
            'image_count': image_count,
            'total_images': self.data['total_images'],
        })
        logging.info(f"使用统计: 处理 {image_count} 张, 累计 {self.data['total_images']} 张")

    def get_stats(self):
        return {
            'launch_count': self.data.get('launch_count', 0),
            'total_images': self.data.get('total_images', 0),
            'batches': self.data.get('batches', 0),
        }
