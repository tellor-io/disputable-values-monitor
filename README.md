# Tellor Disputables
A CLI dashboard & text alerts app for disputable values reported to Tellor oracles.

![](demo.gif)

## Requirements:
- Python >= 3.10
- Install dependencies with [Poetry](https://github.com/python-poetry/poetry):
```
poetry env use 3.10
poetry install
```
### Update environment variables:
In `vars.example.sh`:
- List phone numbers you want alerts sent to (`ALERT_RECIPIENTS`).
- From [twilio](https://www.twilio.com/docs/sms/quickstart/python), specify the phone number that will send messages (`TWILIO_FROM`), your `TWILIO_ACCOUNT_SID`, and access key (`TWILIO_AUTH_TOKEN`).
- Add an [infura key](https://infura.io) (`INFURA_API_KEY`). **note** the Infura key must have polygon support enabled!
- Export environment variables:
```
source vars.example.sh
```

## Usage:
```
poetry run cli
```

## Configuration
Update chains you want to monitor and the confidence threshold for disputable values in `/tellor_disputables/__init__.py`:
```
ETHEREUM_CHAIN_ID = 4
POLYGON_CHAIN_ID = 80001
CONFIDENCE_THRESHOLD = 0.50
```

## Dev setup/help:
Run tests:
```
poetry run pytest
```
Format/lint code:
```
poetry run pre-commit run --all-files
```
Check type hinting:
```
poetry run mypy --strict src --implicit-reexport --ignore-missing-imports --disable-error-code misc
```
Generate requirements.txt:
```
poetry export -f requirements.txt --output requirements.txt --without-hashes
```
