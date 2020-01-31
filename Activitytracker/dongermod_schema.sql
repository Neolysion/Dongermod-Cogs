PRAGMA foreign_keys = 1;

CREATE TABLE IF NOT EXISTS server (
  server_discord_id         INTEGER PRIMARY KEY NOT NULL,
  server_configuration_json TEXT                NOT NULL,
  queue_fk                  INTEGER             NOT NULL REFERENCES queue (id) ON UPDATE RESTRICT,
  queue_cooldown            DATE,
  ban_list_json             TEXT,
  invite_list_json          TEXT,
  accept_list_json          TEXT,
  last_invite_info_json     TEXT
);

CREATE TABLE IF NOT EXISTS queue (
  id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL
);

CREATE TABLE IF NOT EXISTS member_queue (
  queue_fk  INTEGER   NOT NULL REFERENCES queue (id) ON UPDATE RESTRICT,
  member_fk INTEGER   NOT NULL REFERENCES member (discord_id) ON UPDATE RESTRICT,
  join_date TIMESTAMP NOT NULL
);
CREATE TABLE IF NOT EXISTS member (
  discord_id     INTEGER PRIMARY KEY NOT NULL,
  do_not_invite  BOOLEAN             NOT NULL DEFAULT 0,
  steam_id       TEXT,
  veryfied_steam BOOLEAN                      DEFAULT 0
);

CREATE TABLE IF NOT EXISTS dota_matches (
  match_id     INTEGER PRIMARY KEY NOT NULL,
  content_json TEXT                NOT NULL
);

CREATE TABLE IF NOT EXISTS member_stats (
  member_fk  INTEGER NOT NULL REFERENCES member (discord_id) ON UPDATE RESTRICT,
  server_fk  INTEGER NOT NULL REFERENCES server (server_discord_id) ON UPDATE RESTRICT,
  stats_json TEXT    NOT NULL
);

