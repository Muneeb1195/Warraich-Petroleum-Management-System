import configparser
from pathlib import Path

SETTINGS_PATH = Path(__file__).resolve().parent.parent / "settings.ini"


class Settings:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = configparser.ConfigParser()
            cls._instance._config.read(SETTINGS_PATH)
        return cls._instance

    def get(self, section, key, fallback=None):
        return self._config.get(section, key, fallback=fallback)

    def getfloat(self, section, key, fallback=0.0):
        try:
            return self._config.getfloat(section, key)
        except (ValueError, configparser.NoOptionError, configparser.NoSectionError):
            return fallback

    def set(self, section, key, value):
        if not self._config.has_section(section):
            self._config.add_section(section)
        self._config.set(section, key, str(value))

    def save(self):
        with open(SETTINGS_PATH, "w") as f:
            self._config.write(f)

    def business_name(self):
        return self.get("Business", "name", "Warraich Petroleum")

    def gstin(self):
        return self.get("Business", "gstin", "")

    def business_address(self):
        return self.get("Business", "address", "")

    def business_phone(self):
        return self.get("Business", "phone", "")

    def default_gst_rate(self):
        return self.getfloat("GST", "default_rate", 18)

    def hsn_code(self, fuel_or_lube):
        key = f"hsn_{fuel_or_lube.lower()}"
        return self.get("GST", key, "")

    def fuel_rate(self, fuel_name):
        return self.getfloat("Fuel", f"{fuel_name.lower()}_rate", 0)

    def set_fuel_rate(self, fuel_name, rate):
        self.set("Fuel", f"{fuel_name.lower()}_rate", str(rate))
        self.save()

    def set_business_info(self, name, address, phone, gstin):
        self.set("Business", "name", name)
        self.set("Business", "address", address)
        self.set("Business", "phone", phone)
        self.set("Business", "gstin", gstin)
        self.save()

    def backup_interval_days(self):
        return int(self.get("Backup", "auto_backup_interval_days", "7"))

    def shift_names(self):
        raw = self.get("Shift", "names", "Morning,Evening,Night")
        return [s.strip() for s in raw.split(",")]

    def currency_symbol(self):
        return self.get("Regional", "currency_symbol", "Rs.")

    def date_format(self):
        return self.get("Regional", "date_format", "DD/MM/YYYY")


settings = Settings()
