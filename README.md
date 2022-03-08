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

## dev help:
run dashboard:
```
poetry run streamlit run app.py
```
generate requirements.txt for heroku:
```
poetry export -f requirements.txt --output requirements.txt --without-hashes
```
[heroku setup help](https://towardsdatascience.com/quickly-build-and-deploy-an-application-with-streamlit-988ca08c7e83)

