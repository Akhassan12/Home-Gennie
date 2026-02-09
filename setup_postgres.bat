@echo off
REM Setup PostgreSQL for AR Interior Dashboard

echo ================================================
echo PostgreSQL Setup for AR Interior Dashboard
echo ================================================
echo.
echo This script will help you install PostgreSQL
echo and set up the database for your application.
echo.
echo Please follow these steps:
echo.
echo 1. Download PostgreSQL from:
echo    https://www.postgresql.org/download/windows/
echo.
echo 2. Run the installer with these settings:
echo    - Password: 123456
echo    - Port: 5432
echo    - Database name: ar_interior_db
echo.
echo 3. After installation, run these commands
echo    in pgAdmin or psql:
echo.
echo    CREATE DATABASE ar_interior_db;
echo.
echo 4. Then run the migration script:
echo    python migrate_to_postgres.py
echo.
echo ================================================

REM Check if PostgreSQL is already installed
where psql >nul 2>&1
if %errorlevel% equ 0 (
    echo PostgreSQL is already installed!
    echo.
    echo Creating database...
    psql -U postgres -c "CREATE DATABASE ar_interior_db;" 2>nul
    if %errorlevel% equ 0 (
        echo Database created successfully!
    ) else (
        echo Database may already exist. Trying to continue...
    )
    echo.
    echo Running migration...
    python migrate_to_postgres.py
) else (
    echo Please install PostgreSQL first.
)

pause
