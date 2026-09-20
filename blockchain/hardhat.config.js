require('@nomicfoundation/hardhat-ethers');
require('dotenv').config();

const rpcUrl = process.env.POLYGON_AMOY_RPC_URL || '';
const privateKey = process.env.DEPLOYER_PRIVATE_KEY || '';

module.exports = {
  solidity: '0.8.24',
  networks: {
    hardhat: {},
    amoy: {
      url: rpcUrl,
      accounts: privateKey ? [privateKey] : []
    }
  }
};
