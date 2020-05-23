CREATE TABLE "users" (
	"id"	INTEGER NOT NULL UNIQUE,
	"muted"	INTEGER DEFAULT 0,
	"mutelift" TEXT,
	PRIMARY KEY("id")
) WITHOUT ROWID;


CREATE TABLE "infractions" (
	"guid"		TEXT NOT NULL UNIQUE,
	"userID"	INTEGER NOT NULL,
	"measure"	INTEGER NOT NULL,
	"reason"	TEXT,
	"authorID"	INTEGER NOT NULL,
	"epoch"		INTEGER NOT NULL,
	PRIMARY KEY("guid")
);

