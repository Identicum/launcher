CREATE DATABASE launcherdb;
CREATE USER launcherusr WITH PASSWORD 'launcherpwd';
GRANT ALL PRIVILEGES ON DATABASE launcherdb TO launcherusr;

\c launcherdb;
GRANT ALL ON SCHEMA public TO launcherusr;