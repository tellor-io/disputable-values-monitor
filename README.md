# Tellor Disputables
console dashboard & text alerts for disputable values reported to Tellor oracles

## to do:
### 1. add more tests
### 2. clean up & refactor functions
### 3. make key functionality modular
### 4. add type hinting

## next steps:
### 1. extensive user testing by Tellor team/community

## nice-to-have improvement:
- gif using cli tool in README
- parse timestamp into ET, until then use [this](https://www.unixtimestamp.com/index.php) to get local time

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
