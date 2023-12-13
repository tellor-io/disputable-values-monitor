# Auto-disputer
A CLI dashboard & text alerts app for disputing bad values reported to Tellor oracles.

![](demo.gif)

## Introduction

The Disputable Values Monitor is a tool that anyone can use to:
- Monitor / view data submitted to Tellor oracle contracts
- Send Discord alerts for unusual data submissions
- Automatically dispute wildly inaccurate values

## Setup

### Prerequisites:
- A discord server where you can create a channel and a bot for recieving alerts sent by the Disputable Values Monitor via webhook. See the "Making a Webhook" section of the Discord documentation [here](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks/).
- Install Python 3.9 and/or verify that it is the current version:
```bash
python -V
```
The output should be:
```bash
Python 3.9.XX
```
**Note:**
*Other versions (e.g. Python 3.8 or 3.10) are not compatible with the Disputable Values Monitor.*

- Clone the repo and change directory:
```bash
git clone https://github.com/tellor-io/disputable-values-monitor
cd disputable-values-monitor
```
- Create a python environment for installation:
```bash
python3 -m venv env
```
- Install
```bash
poetry install
```

### Update environment variables:
```bash
mv venv/lib/python3.9/site-packages/vars.example.sh vars.sh
```
- Edit `vars.sh` with your favorite text editor replacing the dummy url with the url for your Discord bot's webhook.
- Export environment variables:
```bash
source vars.sh
```

### Set the chains you want to monitor

- Initialize telliot configuration:
```bash
`poetry run telliot config init`
```
You should now have a `telliot` folder in your home directory.

- Open `~/telliot/endpoints.yaml` with your favorite text editor. The Disputable-Values-Monitor will check reports on each chain that is configured in this list. Remove the networks that you don't want to monitor, and provide and endpoint url for those that you do. For example, if you want to monitor reports on Ethereum Mainnet and Sepolia testnet, your endpoints.yaml file should look like this:
```
type: EndpointList
endpoints:
- type: RPCEndpoint
  chain_id: 1
  network: mainnet
  provider: Infura
  url: https://YOUR_MAINNET_ENDPOINT
  explorer: https://etherscan.io
- type: RPCEndpoint
  chain_id: 11155111
  network: sepolia
  provider: Infura
  url: https://YOUR_SEPOLIA_ENDPOINT
  explorer: https://sepolia.etherscan.io/
```

### Run the DVM for Alerts Only

- Start the Disputable-Values-Monitor for Alerts only:
```bash
cli
```
Enter `y` to confirm alerts only.

### Options / Flags

`-c` or `--confidence-threshold`: to specify a percentage threshold for recieving alerts (unavailable if -d is used). The default is 10% or `-c 0.1`

`-w` or `--wait`: The wait time (in seconds) between event checks to reduce calls to the RPC endpoint. The default is seven seconds or `-w 7`

`-av`: to get an alert for all `NewReport` events (regardless of whether they are disputable or not).

### Run the DVM for Automatic Disputes

**Disclaimer:**
*Disputing Tellor values requires staking TRB tokens that can be lost if the community votes in favor of the reporter. There is no guarantee that this software will correctly identify bad values. Use this auto-disputing functionality at your own risk. Experimenting on a testnet before using any real funds is HIGHLY recommended.

1) Create a telliot account using the private key for the address that holds your TRB to be used for dispute fees and gas (ETH, or other) for network fees:
```bash
telliot account add AccountName 0xYOUR_PRIVATE_KEY 1 10 137 11155111
```
Where `1 10 137 11155111` are the network IDs for the networks you want to be able to use with this account.

2) Edit `dipsuter-config.yaml`. Each spot price query must be configured here for auto-disputing. ETH/USD Spot price and EVM call query type are included by default. Different spot price feeds can be added  by providing the `query_id`, `threshold` `type` and `amount`.

The provided configuation is for auto-disputing any ETH/USD value that is 75% different from the value calculated by the DVM:
```yaml
# AutoDisputer configuration file
feeds: # please reference https://github.com/tellor-io/dataSpecs/tree/main/types for examples of QueryTypes w/ Query Parameters
  - query_id: "0x83a7f3d48786ac2667503a61e8c415438ed2922eb86a2906e4ee66d9a2ce4992"
    threshold:
      type: Percentage
      amount: 0.75 # 75%
```
3) Start the Disputable-Values-Monitor with the Auto-Disputer enabled:
```bash
cli -d -a AccountName
```
*Note: If the `-c` and `-d` are used at the same time, the confidence-threshold for alerts only will be ignored. Alternate configuations may require a seperate instance of the DVM.*

### Options / Flags

`-w` or `--wait`: The wait time (in seconds) between event checks to reduce calls to the RPC endpoint. The default is seven seconds or `-w 7`

`-av`: to get an alert for all `NewReport` events (regardless of whether they are disputable or not).

## How it works / Advanced Configuration

The Auto-disputer is a complex event listener for any EVM chain, but specifically it listens for NewReport events on the Tellor network(s) the user wants to monitor.

When the Auto-disputer receives new NewReport events, it parses the reported value from the log, then compares the reported value to the trusted value from the Tellor reporter reference implementation, telliot.

In order to auto-dispute, users need to define what a "disputable value" is. To do this, users can set "thresholds" for feeds they want to monitor. Thresholds in the auto-disputer serve to set cutoffs between a healthy value and a disputable value. Users can pick from three types of thresholds: **range, percentage, and equality**.

### Range
**Range** -- if the difference between the reported value and the telliot value is greater than or equal to a set amount, dispute!

Ex. If the reported value is 250, and the telliot value is 1000, and the monitoring threshold is a range of 500, then the difference is 750 (it is >= to the range amount of 500), and the value is disputable! Therefore, a reported value of 501, in this case, would **not** be disputable. The smaller the range, the more strict the threshold.

### Percentage
**Percentage** -- if the difference between the telliot value and the reported value is greater than or equal to a set percentage of the telliot value, dispute! The smaller the percentage, the more strict the threshold.

Ex. If the reported value is 250, and the telliot value is 1000, and the percentage threshold is 0.50 (50%), then the percent difference is 75% of the telliot value (1000), and the value is disputable! Therefore, a reported value of 750, in this case, would **not** be disputable.

### Equality
**Equality** -- if there is any difference between the reported value and the telliot value, send a dispute!

Ex. If the reported value is "abc123", and the telliot value is "abc1234", then the value is disputable! However, to prevent false disputes due to checksummed addresses, the equality threshold sees "0xABC" and "0xabc" as equal.

## Considerations

**Range** thresholds best monitor high variance price feeds where the percent difference in price between sources is an unreliable indicator of a bad value. They are incompatibale, however, with non-numeric data feeds.

**Percentage** thresholds best monitor standard price feeds. The percentage is measured relative to the telliot value, not the reported value. In other words, if the telliot value is 1000, a 25% difference is 25% of 1000. Like range thresholds, percentage thresholds are incompatibable with non-numeric data feeds.

**Equality** thresholds best monitor data feeds where there is only one right answer. For example, `EVMCall` requests should be exactly equal to their expected telliot response. They aren't very useful for price feeds, though.

## Contributing:

- Install Python 3.9
- Install [Poetry](https://github.com/python-poetry/poetry)

Clone repo:
```bash
git clone https://github.com/tellor-io/disputable-values-monitor.git
```
Change directory:
```bash
cd disputable-values-monitor
```
Install dependencies with [Poetry](https://github.com/python-poetry/poetry):

```
poetry env use 3.9
poetry install
```

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
1. Ensure all tests are passing on `main` branch.
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
17. Change the package version in **pyproject.toml** to be the next development version. For example, if you just released version 0.0.5, change **version** to be "0.0.6dev0".
