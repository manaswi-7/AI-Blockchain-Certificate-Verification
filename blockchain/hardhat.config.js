require('@nomicfoundation/hardhat-ethers');
require('dotenv').config();

const rpcUrl = process.env.POLYGON_AMOY_RPC_URL || '';
const privateKey = process.env.DEPLOYER_PRIVATE_KEY || '';

module.exports = {
  solidity: '0.8.24',
  networks: {
    hardhat: {},
    localhost: {
      url: 'http://127.0.0.1:8545'
    },
    amoy: {
      url: rpcUrl,
      chainId: 80002,
      accounts: privateKey ? [privateKey] : []
    }
  }
};
