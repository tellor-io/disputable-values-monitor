# Tellor Disputables
A CLI dashboard & text alerts app for disputable values reported to Tellor oracles.

![](demo.gif)

## Prerequisites:
- Install Python 3.9
- Install [Poetry](https://github.com/python-poetry/poetry)
- Create an account on [twilio](https://www.twilio.com/docs/sms/quickstart/python)

## Requirements:
- Clone repo:
```bash
git clone https://github.com/tellor-io/disputable-values-monitor.git
```
- Change directory:
```bash
cd disputable-values-monitor
```
- Install dependencies with [Poetry](https://github.com/python-poetry/poetry):

```
poetry env use 3.9
poetry install
```

### Update environment variables:
```bash
mv vars.example.sh vars.sh
```
Edit `vars.sh`:
- List phone numbers you want alerts sent to (`ALERT_RECIPIENTS`).
- From [twilio](https://www.twilio.com/docs/sms/quickstart/python), specify the phone number that will send messages (`TWILIO_FROM`), your `TWILIO_ACCOUNT_SID`, and access key (`TWILIO_AUTH_TOKEN`).
- Export environment variables:
```
source vars.sh
```

## Edit the chains you want to monitor

To edit the chains you want to monitor:
1. Initialize telliot configuration
Run `poetry run telliot config init`
** Note **: You may see an error with this command, such as `Could not connect to RPC endpoint...`. This is expected, and you can ignore it.

This will create a file called `~/telliot/endpoints.yaml`, where you can list and configure the chains and endpoints you want to monitor.
You will need a chain_id, network name, provider name, and a url for an endpoint. You must at least enter a mainnet endpoint, along with any other chains you want to monitor. You also must delete any chains you do not want to monitor.
Here is an example.
```
- type: RPCEndpoint # do not edit this line
  chain_id: 1
  network: mainnet # name of network
  provider: infura # name of provider
  url: myinfuraurl... # url for your endpoint
```

You can list as many chains as you'd like.

After editing `endpoints.yaml`, you are ready to begin monitoring!

## Usage:
```
poetry run cli
```
### Reducing RPC calls
You can update the wait time between event checks to reduce calls to the RPC endpoint. The default is seven seconds.
Use the `--wait` flag to specify a different wait time in seconds.
```
poetry run cli --wait 120
```

### Viewing all NewReport events
You can configure the disputable-values-monitor to alert you on ALL NewReport events. This is useful for monitoring uncommon but important data types.
Use the `-a` or `--all-values` flag to specify that you want to monitor and receive alerts for all values.
```
poetry run cli -a
```

### Monitoring a single queryId
You can set the disputable-values-monitor to alert you on a single queryId. Use `-f` to enter `filter` mode, where you can select a Query Type and enter the Query Parameters to build a queryId to monitor.

### Setting the confidence threshold
You can set the confidence threshold of the disputable-values-monitor to a float between 0 and 1. The confidence thresholds represents the percent difference between the reported value and the expected value required to send an alert to dispute. For setting the confidence threshold, use the `-c` flag. For example, run `poetry run cli -c 0.25` to receive alerts if there's a 25% difference between the reported value and the expected value.


## Dev setup/help:
Run tests:
```
poetry run pytest
```
Format/lint code:
```
poetry run pre-commit run --all-files
```
Check type hinting:
```
poetry run mypy --strict src --implicit-reexport --ignore-missing-imports --disable-error-code misc
```
Generate requirements.txt:
```
poetry export -f requirements.txt --output requirements.txt --without-hashes
```
