# Tellor Disputables
dashboard & text alerts for disputable values reported to Tellor oracles

[SEE THE APP](https://tellor-disputables.herokuapp.com/)

## to do:
### 1. display updates
- fix removing older txs from table:
```
disputable-values-monitor/tellor_disputables/dashboard.py", line 108, in dashboard
    displayed_events.remove(display_rows[0][0])
KeyError: '0x096c46968983f84f0b6e89c070b074169eee93e7168f1098936cf7dab7d26155'
```
- fetch new value for given event `queryId`.
- compare event data value and fetched value (check if disputable)

### 2. tests
- add unit tests for all funcs

### 3. app deployment
- fix env vars not being found by heroku deployed app
- move deployed app to paid team heroku (so doesn't shut down when not used)

### 4. make modular
- make it easy to use things from this repo in reporter software, or at least easy to move them over there

## nice-to-have improvement:
- parse timestamp into ET
- make explorer link column into hyperlink: [source](https://discuss.streamlit.io/t/make-streamlit-table-results-hyperlinks-or-add-radio-buttons-to-table/7883)


## dev setup/help/usage:
edit `vars.example.sh` and export the needed environment variables:
```
source vars.example.sh
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

