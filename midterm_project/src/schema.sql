create table if not exists page(
  page_url string not null,
  data_noun string not null,
  data_count integer
);

create table if not exists result(
  result_id integer primary key autoincrement,
  result_url string not null,
  result_ret string not null
);