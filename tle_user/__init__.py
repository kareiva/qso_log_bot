import sqlite3


class tle_user(object):

    user_id = 0
    qso_count = 0
    station_callsign = "N0CALL"
    band = "80m"
    mode = "SSB"
    srst = 59
    rrst = 59

    def __init__(self, user_id):
        self.user_id = user_id
        self._populate_user()
        self._get_qso_count()

    def _save_settings(self, key):
        value = getattr(self, key)
        qso_db = sqlite3.connect("qso.db")
        cursor = qso_db.cursor()
        cursor.execute(
            "REPLACE INTO settings (user_id, key, value) VALUES(:user_id, :setting, :value)",
            {"user_id": self.user_id, "setting": key, "value": value},
        )
        qso_db.commit()
        qso_db.close()

    def _populate_user(self):
        qso_db = sqlite3.connect("qso.db")
        cursor = qso_db.cursor()
        rows = cursor.execute(
            "SELECT key, value FROM settings WHERE user_id=:user_id",
            {"user_id": self.user_id},
        ).fetchall()
        qso_db.close()
        for row in rows:
            setattr(self, row[0], row[1])

    def _get_qso_count(self):
        qso_db = sqlite3.connect("qso.db")
        cursor = qso_db.cursor()
        rows = cursor.execute(
            "SELECT COUNT(*) FROM qso WHERE user_id=:user_id", {"user_id": self.user_id}
        ).fetchall()
        qso_db.close()
        self.qso_count = rows[0][0]
        return rows[0][0]

    def set_station_callsign(self, station_callsign):
        self.station_callsign = station_callsign
        self._save_settings("station_callsign")

    def set_band(self, band):
        self.band = band
        self._save_settings("band")

    def set_mode(self, mode):
        self.mode = mode
        self._save_settings("mode")

    def set_srst(self, srst):
        self.srst = srst
        self._save_settings("srst")

    def set_rrst(self, rrst):
        self.rrst = rrst
        self._save_settings("rrst")
