module.exports = {
  networks: {
    hardhat: {
      chainId: 1337,
      forking: {
        url: process.env.MAINNET_URL,
        blockNumber: 22026011
      },
      accounts: {
        accountsToImpersonate: ["0x39E419bA25196794B595B2a595Ea8E527ddC9856"]
      }
    }
  },
};
