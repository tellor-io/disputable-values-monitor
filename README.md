# Tellor Disputables
dashboard & text alerts for disputable values reported to Tellor oracles

[SEE THE APP](https://tellor-disputables.herokuapp.com/)

## plan:
- poll for new events from Tellor oracle contracts every N seconds
- filter events for `submitValue` transactions.
- parse the `queryId` and value submitted for each tx.
- fetch values for that `queryId`.
- compare event data value and fetched value.
- update dashboard & sends alert if event value is disputable.

## todo:
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

