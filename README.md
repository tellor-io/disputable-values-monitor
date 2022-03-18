# Tellor Disputables
console dashboard & text alerts for disputable values reported to Tellor oracles

## to do:
### make cli print alerts & dashboard even if no twiliot keys provided
### 1. tests
- add unit tests for all funcs
### 2. clean up & refactor functions
- a lot of funcs are gross & messy
### 3. make modular
- make it easy to use things from this repo in reporter software, or at least easy to move them over there
### 4. add type hinting

## nice-to-have improvement:
- gif using cli tool in README
- parse timestamp into ET

## requirements:
- install [poetry]()
- to get alerts via text, [get twilio keys](https://www.twilio.com/docs/sms/quickstart/python), edit `vars.example.sh`, and export environment variables:
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
