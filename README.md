# Tellor Disputables
A CLI dashboard & text alerts app for disputable values reported to Tellor oracles.

![](demo.gif)

## Prerequisites:
- Install Python >= 3.10
- Install [Poetry](https://github.com/python-poetry/poetry)
- Create an account on [twilio](https://www.twilio.com/docs/sms/quickstart/python)

## Requirements:
- Clone repo
- Install dependencies with [Poetry](https://github.com/python-poetry/poetry):

```
poetry env use 3.10
poetry install
```

### Update environment variables:
Edit `vars.example.sh`:
- List phone numbers you want alerts sent to (`ALERT_RECIPIENTS`).
- From [twilio](https://www.twilio.com/docs/sms/quickstart/python), specify the phone number that will send messages (`TWILIO_FROM`), your `TWILIO_ACCOUNT_SID`, and access key (`TWILIO_AUTH_TOKEN`).
- Add an [infura key](https://infura.io) (`INFURA_API_KEY`). **note** the Infura key must have polygon support enabled!
- Export environment variables:
```
source vars.example.sh
```

## Edit the chains you want to monitor
Update the list of chains you want to monitor and the confidence threshold for disputable values in `/src/tellor_disputables/__init__.py`:
```
ETHEREUM_CHAIN_ID = 4
POLYGON_CHAIN_ID = 80001
CONFIDENCE_THRESHOLD = 0.50
```

The monitor currently supports these networks:
* Ethereum mainnet:         ETHEREUM_CHAIN_ID = 1
* Ethereum Rinkeby testnet: ETHEREUM_CHAIN_ID = 4
* Polygon mainnet: POLYGON_CHAIN_ID = 137
* Polygon testnet Mumbai: POLYGON_CHAIN_ID = 80001



## Usage:
```
poetry run cli
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
