-- Create database user
CREATE USER olympus_user WITH PASSWORD 'olympus_password';

-- Create database
CREATE DATABASE olympus_bot OWNER olympus_user;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE olympus_bot TO olympus_user;

-- Connect to the database
\c olympus_bot

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO olympus_user;
