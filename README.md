# Tellor Disputables
dashboard & text alerts for disputable values reported to Tellor oracles

[SEE THE APP](https://tellor-disputables.herokuapp.com/)

## to do:
### 1. getting/displaying events
- parse the `queryId` and value submitted for each NewReport event.
- check new events every loop to update dashboard
- filter out duplicate events
- add unique events as new rows to dashboard

### 2. display updates
- add time submitted column
- parse timestamp into ET

- check if disputable
- fetch values for that `queryId`.
- compare event data value and fetched value.
- update dashboard & sends alert if event value is disputable.

### 3. tests
- add unit tests for all funcs

### 4. app deployment
- fix env vars not being found by heroku deployed app
- move deployed app to paid team heroku (so doesn't shut down when not used)

### 5. move code to team org
- create tellor-disputes-monitor repo in tellor github org
- move code to tellor repo

## nice-to-have improvement:
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

