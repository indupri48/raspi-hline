
DROP TABLE IF EXISTS observations;

CREATE TABLE observations (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	observation_name TEXT NOT NULL,
	center_frequency REAL NOT NULL,
	bandwidth REAL NOT NULL,
	n_channels INT NOT NULL,
	n_bins INT NOT NULL,
	duration REAL NOT NULL,
	date_created UNIX_TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	csv_filename TEXT NOT NULL,
	img_filename TEXT NOT NULL
);
