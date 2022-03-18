# Tellor Disputables
dashboard & text alerts for disputable values reported to Tellor oracles

[SEE THE APP](https://tellor-disputables.herokuapp.com/)

## to do:

### !!!~~~~~make it into cli tool...

### 1. tests
- add unit tests for all funcs

### 3. make modular
- make it easy to use things from this repo in reporter software, or at least easy to move them over there

## nice-to-have improvement:
- gif using cli tool in README
- parse timestamp into ET


## dev setup/help/usage:
edit `vars.example.sh` and export the needed environment variables:
```
source vars.example.sh
```
run tests:
```
poetry run pytest
```
run dashboard:
```
poetry run cli
```
generate requirements.txt:
```
poetry export -f requirements.txt --output requirements.txt --without-hashes
```
[twilio setup help](https://www.twilio.com/docs/sms/quickstart/python)

