# Tellor Disputables
dashboard & text alerts for disputable values reported to Tellor oracles

### plan:
- poll for new events from Tellor oracle contracts every N seconds
- filter events for `submitValue` transactions.
- parse the `queryId` and value submitted for each tx.
- fetch values for that `queryId`.
- compare event data value and fetched value.
- update dashboard & sends alert if event value is disputable.

### run dashboard:
`poetry run streamlit run app.py`