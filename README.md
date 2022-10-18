# Tellor Disputables
A CLI dashboard & text alerts app for disputable values reported to Tellor oracles.

![](demo.gif)

## Prerequisites:
- Install Python 3.9
- Install [Poetry](https://github.com/python-poetry/poetry)
- Create an account on [twilio](https://www.twilio.com/docs/sms/quickstart/python)

## Requirements:
- Clone repo
- Install dependencies with [Poetry](https://github.com/python-poetry/poetry):

```
poetry env use 3.9
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

To edit the chains you want to monitor:
1. Add/remove chains to the list of chains you want to monitor and the confidence threshold for disputable values in `/src/tellor_disputables/__init__.py`
```
ETHEREUM_CHAIN_ID = 4
POLYGON_CHAIN_ID = 80001
CONFIDENCE_THRESHOLD = 0.50
```
2. Add/remove urls to the list of RPC urls in `src/tellor_disputables/data.py`.

...The monitor currently supports these networks...
* Ethereum mainnet:         ETHEREUM_CHAIN_ID = 1
* Ethereum Rinkeby testnet: ETHEREUM_CHAIN_ID = 4
* Polygon mainnet: POLYGON_CHAIN_ID = 137
* Polygon testnet Mumbai: POLYGON_CHAIN_ID = 80001

3. Import new Chain IDs into `src/tellor_disputables/cli.py`. If deleting a chain ID, remove the import.


## Usage:
```
poetry run cli
```
You can also update the wait time between event checks to reduce calls to the RPC endpoint. The default is seven seconds.
Use the `--wait` flag to specify a different wait time in seconds.
```
poetry run cli --wait 120
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
