# Aku Aku Bot
<img src="https://img.shields.io/badge/Outlaw's Fortress-purple"> <img src="https://img.shields.io/badge/Yoru--blue">\
Bot multipropósito enfocado en ofrecer mini-juegos para la comunidad. **Proyecto creado para Outlaw's Fortress.**

> Puedes clonar este proyecto y usarlo para tus servidores, o agregar al [bot oficial](https://discord.com/api/oauth2/authorize?client_id=1104270054792638525&permissions=51539607552&scope=applications.commands%20bot):

Permisos recomendados:\
`Gestionar Hilos`

## Features
___

- Juegos interactivos
- Comandos Divertidos
- Economía
- Scoreboard para cada juego
- Música
- Muy mucho si muy

| Juegos | Disponibilidad |
| --- | --- |
| Economia | ❌
| Blackjack | ✅
| UNO! | ✅
| Batalla Naval | ❌
| Ludo | ❌
| Jackpot | ❌
| Lotería | ❌
| No Thanks! | ❌
| PK Showdown | ❌

## Dependencias
___
1. [Python](https://www.python.org/): 3.10+
2. [Poetry](https://python-poetry.org/)
3. [Conexión a internet 🤓](https://i.ytimg.com/vi/OjrZ_HVj48c/maxresdefault.jpg)

## ¿Cómo instalarlo?
___
1. Crear un archivo `.env` en base al `.env.template`: `cp .env.template .env`
1. Configurar `DISCORD_API_TOKEN`, `MONGO_URI` y `TEST_GUILD_IDS`:

```bash
DISCORD_API_TOKEN="Inserta tu token aquí"
MONGO_URI="Inserta tu URI aquí"
TEST_GUILD_IDS="ID_GUILD_1,ID_GUILD_2,ID_GUILD_3"
```

3. Instalar las dependencias (*Requisito: tener instalado Poetry y una versión de Python>=3.10*):

```bash
poetry install
```

4. Iniciar el cliente:

```bash
poetry run python main.py
```

## Code Style
___
Este proyecto usa las siguientes herramientas para formatear el código y asegurar las mejores prácticas:
- [isort](https://pycqa.github.io/isort/)
- [black](https://black.readthedocs.io/en/stable/)
- [ruff](https://beta.ruff.rs/docs/)

Estas herramientas analizarán el código mediante [Github Actions](https://docs.github.com/en/actions)
cada vez que subas el código y verás los resultados [aquí](https://github.com/n-ull/aku/actions).


### Autohooks
Usando git hooks, puedes correr estas herramientas cada vez que hagas un commit desde tu entorno de
desarrollo local y asegurarte así de que todo esté en orden.

Este proyecto usa [autohooks](https://github.com/greenbone/autohooks).
Para configurarlo, debes correr los siguientes comandos (una única vez):

```bash
# Si no lo has hecho antes:
poetry install

poetry run autohooks activate --mode poetry
# El orden de los plugins importa
poetry run autohooks plugins add autohooks.plugins.isort autohooks.plugins.black autohooks.plugins.ruff
```
