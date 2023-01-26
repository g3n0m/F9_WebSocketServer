import os
from aiohttp import web
import asyncio
from asyncio import Queue
import time
import aiohttp

# Создание пути к файлу index.html
WS_FILE = os.path.join(os.path.dirname(__file__), "index.html")


# Асинхронная функция, которая обрабатывает подключения к веб-сокетам.
async def wshandler(request: web.Request):
    # Создание объекта WebSocketResponse с тактом 5 секунд
    resp = web.WebSocketResponse(heartbeat=5)
    # Проверка возможности подготовки ответа
    available = resp.can_prepare(request)
    # Если ответ не может быть подготовлен, обслуживание файла index.html
    if not available:
        with open(WS_FILE, "rb") as fp:
            return web.Response(body=fp.read(), content_type="text/html")
    # Подготовка соединения
    await resp.prepare(request)
    # Отправка сообщения вновь подключенному клиенту
    await resp.send_str("Вы успешно подключились к чату!")

    try:
        # Вывести сообщение на консоль
        print("Новый пользователь подключился")
        # Широковещательное сообщение всем другим подключенным клиентам
        for ws in request.app["sockets"]:
            await ws.send_str("Новый пользователь подключился")
        # Добавление нового соединения в список активных сокетов
        request.app["sockets"].append(resp)

        # Ожидание входящих сообщений
        async for msg in resp:
            if msg.type == web.WSMsgType.TEXT:
                if msg.data == "ping":
                    await resp.send_str("pong")
                else:
                    # Широковещательное сообщение всем другим подключенным клиентам
                    for ws in request.app["sockets"]:
                        if ws is not resp:
                            await ws.send_str(msg.data)
            else:
                return resp
        return resp

    finally:
        # Удаление отключенного клиента из списка активных сокетов
        request.app["sockets"].remove(resp)
        # Print message to the console
        print("Пользователь покинул чат")
        # Широковещательное сообщение всем другим подключенным клиентам
        for ws in request.app["sockets"]:
            await ws.send_str("Пользователь покинул чат")


# Асинхронная функция, которая вызывается при завершении работы приложения.
async def on_shutdown(app: web.Application):
    # Закрытие всех активных подключений к веб-сокетам
    for ws in app["sockets"]:
        await ws.close()


# Инициализация веб-приложения
def init():
    app = web.Application()
    # Инициализация пустого списка для хранения активных подключений к веб-сокетам
    app["sockets"] = []
    # Добавление маршрута для сервера веб-сокетов
    app.router.add_get("/news", wshandler)
    # Добавление функции on_shutdown, которая будет вызываться при завершении работы приложения.
    app.on_shutdown.append(on_shutdown)
    return app


# Запуск веб-приложения
web.run_app(init())
