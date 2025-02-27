import json
import os
from datetime import datetime

class Database:
    def __init__(self):
        self.users_file = "data/users.json"
        self.signals_file = "data/signals.json"
        self.licenses_file = "data/licenses.json"
        self._initialize_files()

    def _initialize_files(self):
        os.makedirs("data", exist_ok=True)

        for file_path in [self.users_file, self.signals_file, self.licenses_file]:
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    json.dump({}, f)

    def _load_data(self, file_path):
        with open(file_path, 'r') as f:
            return json.load(f)

    def _save_data(self, data, file_path):
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

    def get_user(self, user_id):
        users = self._load_data(self.users_file)
        return users.get(str(user_id))

    def save_user(self, user_id, user_data):
        users = self._load_data(self.users_file)
        users[str(user_id)] = user_data
        self._save_data(users, self.users_file)

    def create_user(self, user_id, username):
        user_data = {
            "user_id": user_id,
            "username": username,
            "is_premium": False,
            "signals_used": 0,
            "daily_signals": 0,
            "last_signal_date": datetime.now().strftime("%Y-%m-%d"),
            "join_date": datetime.now().isoformat(),
            "license_key": None
        }
        self.save_user(user_id, user_data)
        return user_data

    def add_signal_use(self, user_id):
        user = self.get_user(user_id)
        if user:
            # Për përdoruesit premium, resetojmë numëruesin ditor nëse është ditë e re
            if user["is_premium"]:
                current_date = datetime.now().strftime("%Y-%m-%d")
                if user.get('last_signal_date') != current_date:
                    user['daily_signals'] = 0
                    user['last_signal_date'] = current_date

            # Rrisim numëruesit përkatës
            user['signals_used'] += 1
            if user["is_premium"]:
                user['daily_signals'] += 1

            self.save_user(user_id, user)
            return user['signals_used']
        return 0

    def get_daily_signals(self, user_id):
        user = self.get_user(user_id)
        if user:
            # Për përdoruesit falas, kontrollojmë totalin e sinjaleve të përdorura
            if not user["is_premium"]:
                return user.get('signals_used', 0)

            # Për përdoruesit premium, kontrollojmë vetëm sinjalet ditore
            current_date = datetime.now().strftime("%Y-%m-%d")
            if user.get('last_signal_date') != current_date:
                user['daily_signals'] = 0
                user['last_signal_date'] = current_date
                self.save_user(user_id, user)
            return user['daily_signals']
        return 0

    def create_license(self, key, duration_days):
        licenses = self._load_data(self.licenses_file)
        licenses[key] = {
            "key": key,
            "duration_days": duration_days,
            "created_at": datetime.now().isoformat(),
            "used": False
        }
        self._save_data(licenses, self.licenses_file)

    def activate_license(self, user_id, license_key):
        licenses = self._load_data(self.licenses_file)
        if license_key in licenses and not licenses[license_key]["used"]:
            user = self.get_user(user_id)
            if user:
                user["is_premium"] = True
                user["license_key"] = license_key
                licenses[license_key]["used"] = True
                self._save_data(licenses, self.licenses_file)
                self.save_user(user_id, user)
                return True
        return False

    def save_signal(self, signal_data):
        signals = self._load_data(self.signals_file)
        signal_id = str(len(signals) + 1)
        signals[signal_id] = {
            **signal_data,
            "created_at": datetime.now().isoformat()
        }
        self._save_data(signals, self.signals_file)

    def remove_user_license(self, user_id):
        """Remove license from a user"""
        user = self.get_user(user_id)
        if user and user["is_premium"]:
            # Get the current license key
            license_key = user["license_key"]

            # Update user data
            user["is_premium"] = False
            user["license_key"] = None
            self.save_user(user_id, user)

            # Mark license as unused so it can be used again
            if license_key:
                licenses = self._load_data(self.licenses_file)
                if license_key in licenses:
                    licenses[license_key]["used"] = False
                    self._save_data(licenses, self.licenses_file)

            return True
        return False