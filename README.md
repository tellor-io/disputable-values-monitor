# Tellor Disputables
console dashboard & text alerts for disputable values reported to Tellor oracles

![](demo.gif)

## requirements:
- Python >= 3.10
- install [poetry](https://github.com/python-poetry/poetry)
- get [twilio things](https://www.twilio.com/docs/sms/quickstart/python), [infura key](https://infura.io), edit `vars.example.sh`, and export environment variables:
```
source vars.example.sh
```

## usage:
```
poetry run cli
```

## dev setup/help:
run tests:
```
poetry run pytest
```
generate requirements.txt:
```
poetry export -f requirements.txt --output requirements.txt --without-hashes
```
