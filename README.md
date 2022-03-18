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
- make explorer link column into hyperlink: [source](https://discuss.streamlit.io/t/make-streamlit-table-results-hyperlinks-or-add-radio-buttons-to-table/7883)


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
poetry run streamlit run app.py
```
generate requirements.txt for heroku:
```
poetry export -f requirements.txt --output requirements.txt --without-hashes
```
[heroku setup help](https://towardsdatascience.com/quickly-build-and-deploy-an-application-with-streamlit-988ca08c7e83)

[twilio setup help](https://www.twilio.com/docs/sms/quickstart/python)

