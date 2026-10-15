@echo off
title AnnaSetu - Zero Food Waste Engine
echo ======================================================================
echo  🌾 AnnaSetu: Autonomous Surplus Meal Rescue & Redistribution Engine
echo  Hyperlocal Bhubaneswar Network
echo ======================================================================
echo.
echo Installing dependencies if needed...
call npm install --no-audit --no-fund
echo.
echo Starting backend server on http://localhost:3000/dashboard ...
start http://localhost:3000/dashboard
call npm start
pause
