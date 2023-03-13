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
You may see an error with this command, such as `Could not connect to RPC endpoint...`. This is expected, and you can ignore it.

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

## Options
The available cli options are `-a`, `-f`, `-c`, and `-wait`. You can use these options in any combination.

Use `-a` to get an alert for ALL `NewReport` events (regardless of whether they are disputable or not).
```bash
poetry run cli -a
```

Use `-f` to enter `filter` mode, where you can select a Query Type and enter the Query Parameters to build a queryId to monitor.
```bash
poetry run cli -f
```

Use `-c` to set the confidence threshold. The default confidence threshold is 75%. The confidence threshold represents the percent difference between the reported value and the expected value required to send an alert to dispute. For example to receive alerts if there's a 25% difference between the reported value and the expected value, run the following command.
```bash
poetry run cli -c 0.25
```

Use `-wait` to set the wait time (in seconds) between event checks to reduce calls to the RPC endpoint. The default is seven seconds.
```bash
poetry run cli --wait 120
```


## Dev setup for contributing:
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
Generate requirements.txt in case you have installed new dependencies:
```
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

### Publishing a release
1. Ensure all tests are passing on `dvm-main` branch.
2. Remove "dev" from version in the `pyproject.toml` file. Example: version = "0.0.5dev" --> version = "0.0.5".
3. On github, go to "Releases" -> "Draft a new release" -> "Choose a tag".
4. Write in a new tag that corresponds with the version in `pyproject.toml` file. Example: v0.0.5
5. If the tag is v.0.0.5, the release title should be Release 0.0.5.
6. Click Auto-generate release notes.
7. Check the box for This is a pre-release.
8. Click Publish release.
9. Navigate to the Actions tab from the main page of the package on github and make sure the release workflow completes successfully.
10. Check to make sure the new version was released to test PyPI [here](https://test.pypi.org/project/tellor-disputables/).
11. Test downloading and using the new version of the package from test PyPI ([example](https://stackoverflow.com/questions/34514703/pip-install-from-pypi-works-but-from-testpypi-fails-cannot-find-requirements)).
12. Navigate back to the pre-release you just made and click edit (the pencil icon).
13. Uncheck the This is a pre-release box.
14. Publish the release.
15. Make sure the release github action goes through.
16. Download and test the new release on PyPI official [here](https://pypi.org/project/tellor-disputables/).
17. Change the package version in **pyproject.toml**.py to be the next development version. For example, if you just released version 0.0.5, change **version** to be "0.0.6dev0".