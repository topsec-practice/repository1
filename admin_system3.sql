/*==============================================================*/
/* DBMS name:      MySQL 5.0                                    */
/* Created on:     2025/6/6 17:02:07                            */
/*==============================================================*/


drop table if exists admin;

drop table if exists files;

drop table if exists matches;

drop table if exists policy;

drop table if exists rules;

drop table if exists user;

/*==============================================================*/
/* Table: admin                                                 */
/*==============================================================*/
create table admin
(
   admin_id             varchar(100) not null,
   admin_name           varchar(100),
   admin_key            varchar(100),
   primary key (admin_id)
);

/*==============================================================*/
/* Table: files                                                 */
/*==============================================================*/
create table files
(
   md5                  varchar(100),
   file_name            varchar(100),
   discovery_time       datetime,
   file_id              varchar(100) not null,
   user_id              varchar(100) not null,
   count				int(100) not null,
   primary key (file_id, user_id)
);

/*==============================================================*/
/* Table: matches                                               */
/*==============================================================*/
create table matches
(
   policy_id            varchar(100) not null,
   file_id              varchar(100) not null,
   user_id              varchar(100) not null,
   rule_id              varchar(100),
   primary key (rule_id, file_id, user_id)
);

/*==============================================================*/
/* Table: policy                                                */
/*==============================================================*/
create table policy
(
   policy_id            varchar(100) not null,
   policy_description   varchar(100),
   primary key (policy_id)
);

/*==============================================================*/
/* Table: rules                                                 */
/*==============================================================*/
create table rules
(
   rule_id              varchar(100) not null,
   policy_id            varchar(100) not null,
   rule_description     varchar(100),
   primary key (rule_id, policy_id)
);

/*==============================================================*/
/* Table: user                                                  */
/*==============================================================*/
create table user
(
   user_id              varchar(100) not null,
   admin_id             varchar(100),
   user_name            varchar(100),
   user_key             varchar(100),
   status               varchar(100),
   LastEchoTime		    datetime,
   LastScanTime         datetime,
   IP					varchar(20),
   primary key (user_id)
);

alter table files add constraint FK_upload foreign key (user_id)
      references user (user_id) on delete restrict on update restrict;

alter table matches add constraint FK_matches2 foreign key (file_id, user_id)
      references files (file_id, user_id) on delete restrict on update restrict;

alter table matches add constraint FK_need foreign key (rule_id, policy_id)
      references rules (rule_id, policy_id) on delete restrict on update restrict;

alter table rules add constraint FK_has foreign key (policy_id)
      references policy (policy_id) on delete restrict on update restrict;

alter table user add constraint FK_managed foreign key (admin_id)
      references admin (admin_id) on delete restrict on update restrict;

