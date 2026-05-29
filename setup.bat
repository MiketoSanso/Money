@echo off
title PhotoStudio Setup
echo ========================================
echo   PhotoStudio - Установка и запуск
echo ========================================
echo.

REM Проверяем Docker
echo [1/4] Проверка Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] Docker Desktop не установлен!
    pause
    exit /b 1
)
echo   OK

docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] Docker Desktop не запущен!
    pause
    exit /b 1
)
echo.

REM Проверяем, есть ли уже собранный образ
echo [2/4] Проверка образа...
docker image inspect moneyprojectr-app >nul 2>&1
if %errorlevel% equ 0 (
    echo   Образ найден, пересборка не требуется
    set BUILD_FLAG=
) else (
    echo   Образ не найден, выполняем сборку...
    set BUILD_FLAG=--build
)
echo.

REM Запускаем контейнеры
echo [3/4] Запуск контейнеров...
docker-compose up -d %BUILD_FLAG%
if %errorlevel% neq 0 (
    echo [ОШИБКА] Не удалось запустить контейнеры!
    pause
    exit /b 1
)
echo.

REM Ждём готовность
echo [4/4] Ожидание сервера...
timeout /t 5 /nobreak >nul

start http://localhost:5000

echo.
echo ========================================
echo   ГОТОВО!
echo   http://localhost:5000
echo   admin / admin123
echo ========================================
echo.
echo Для остановки нажми любую клавишу...
pause >nul

docker-compose down
echo Контейнеры остановлены.
pause