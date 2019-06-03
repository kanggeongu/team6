create table if not exists user (
  user_num integer primary key autoincrement,
  user_id string not null,
  user_pw_hash string not null
);