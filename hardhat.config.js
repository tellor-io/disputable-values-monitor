require("dotenv").config();

const MAINNET_URL = process.env.MAINNET_URL;
if (!MAINNET_URL || !MAINNET_URL.startsWith('http')) {
  console.error('Invalid or missing MAINNET_URL. Must be an absolute URL starting with http:// or https://');
  process.exit(1);
}

module.exports = {
  networks: {
    hardhat: {
      chainId: 1337,
      forking: {
        url: MAINNET_URL,
        blockNumber: 22026011
      },
      accounts: {
        accountsToImpersonate: ["0x39E419bA25196794B595B2a595Ea8E527ddC9856"]
      }
    }
  },
};
