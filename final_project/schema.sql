create table if not exists user (
  user_num integer primary key autoincrement,
  user_id string not null,
  user_pw_hash string not null
);

create table if not exists subcribe( 
  sub_num string not null,
  sub_user_id string not null
);