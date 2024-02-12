create table if not exists urls (
    id serial primary key,
    name varchar(255) not null unique,
    created_at timestamp not null
);

create table if not exists url_check (
    id serial primary key,
    url_id integer,
    status_code integer,
    h1 text,
    title text,
    description text,
    created_at timestamp not null,
    foreign key (url_id) references urls (id)
);