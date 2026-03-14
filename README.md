# BDS Updater

Automatic updater for Minecraft Bedrock Dedicated Server.

![Release](https://img.shields.io/github/v/release/Takkunlego0916/BDS-Updater)
![Downloads](https://img.shields.io/github/downloads/Takkunlego0916/BDS-Updater/total)

## Features

* GUI updater
* Update check
* Download progress bar
* Server stop → update → restart
* Player notification before restart
* Exclude files/folders from overwrite
* Custom exclude support
* Console viewer
* Command sender

## Default excluded files

```
behavior_packs
resource_packs
worlds
config
allowlist.json
permissions.json
server.properties
```

## How to use

1. Download `BDSUpdater.exe`
2. Select your Bedrock server folder
3. Click **Start Server**
4. Click **Check Update**
5. Click **Update Server**

## Build from source

Install dependencies:

```
pip install -r requirements.txt
```

Run:

```
python src/bds_updater.py
```

Build exe:

```
pip install pyinstaller
pyinstaller --onefile --windowed src/bds_updater.py
```

## License

MIT
