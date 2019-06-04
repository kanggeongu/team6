create table if not exists user (
  user_num integer primary key autoincrement,
  user_id string not null,
  user_pw_hash string not null
);

create table if not exists subscribe(
  sub_num integer primary key autoincrement,
  sub_link string not null,
  sub_image string not null,
  sub_title string not null,
  sub_user_id string not null
);