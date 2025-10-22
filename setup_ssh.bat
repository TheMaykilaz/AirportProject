@echo off
echo Creating SSH keys for Airport Project...
echo.

REM Check if SSH directory exists
if not exist "%USERPROFILE%\.ssh" (
    mkdir "%USERPROFILE%\.ssh"
)

REM Generate SSH key
ssh-keygen -t rsa -b 4096 -C "airport-project-key" -f "%USERPROFILE%\.ssh\id_rsa" -q

REM Display the public key
echo.
echo Your SSH public key (copy this to GitHub):
echo =========================================
type "%USERPROFILE%\.ssh\id_rsa.pub"
echo.
echo =========================================
echo.

echo Add this key to GitHub at: https://github.com/settings/ssh
echo Then run: git remote set-url origin git@github.com:TheMaykilaz/AirportProject.git
echo.

pause
