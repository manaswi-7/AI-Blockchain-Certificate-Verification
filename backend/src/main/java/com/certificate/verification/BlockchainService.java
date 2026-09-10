package com.certificate.verification;

import java.math.BigInteger;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.web3j.abi.FunctionEncoder;
import org.web3j.abi.FunctionReturnDecoder;
import org.web3j.abi.TypeReference;
import org.web3j.abi.datatypes.Address;
import org.web3j.abi.datatypes.Bool;
import org.web3j.abi.datatypes.Function;
import org.web3j.abi.datatypes.Type;
import org.web3j.abi.datatypes.generated.Bytes32;
import org.web3j.protocol.Web3j;
import org.web3j.protocol.core.DefaultBlockParameterName;
import org.web3j.protocol.core.methods.request.Transaction;
import org.web3j.protocol.http.HttpService;
import org.web3j.crypto.Credentials;
import org.web3j.tx.RawTransactionManager;
import org.web3j.tx.gas.StaticGasProvider;
import org.web3j.utils.Convert;

@Service
public class BlockchainService {
  private final String rpcUrl;
  private final String privateKey;
  private final String contractAddress;
  private final long chainId;

  public BlockchainService(@Value("${app.blockchain-rpc-url:}") String rpcUrl,
      @Value("${app.blockchain-private-key:}") String privateKey,
      @Value("${app.blockchain-contract-address:}") String contractAddress,
      @Value("${app.blockchain-chain-id:80002}") long chainId) {
    this.rpcUrl=rpcUrl; this.privateKey=privateKey; this.contractAddress=contractAddress; this.chainId=chainId;
  }

  public boolean configured() { return !rpcUrl.isBlank() && !privateKey.isBlank() && !contractAddress.isBlank(); }

  private Web3j web3() { return Web3j.build(new HttpService(rpcUrl)); }
  private byte[] bytes32(String hex) { String h=hex.startsWith("0x")?hex.substring(2):hex; return org.web3j.utils.Numeric.hexStringToByteArray(h); }

  public String anchor(String certificateIdHash, String documentHash) throws Exception {
    if (!configured()) throw new IllegalStateException("Blockchain is not configured. Set POLYGON_AMOY_RPC_URL, BLOCKCHAIN_PRIVATE_KEY and BLOCKCHAIN_CONTRACT_ADDRESS.");
    Web3j w=web3(); Credentials c=Credentials.create(privateKey);
    Function f=new Function("anchorCertificate",
        java.util.List.of(new Bytes32(bytes32(certificateIdHash)),new Bytes32(bytes32(documentHash))),
        java.util.List.of());
    RawTransactionManager tm=new RawTransactionManager(w,c,chainId);
    var receipt=tm.sendTransaction(Convert.toWei("0",Convert.Unit.ETHER).toBigInteger(), BigInteger.valueOf(3_000_000_000L), contractAddress, FunctionEncoder.encode(f), BigInteger.ZERO);
    if (!receipt.isStatusOK()) throw new IllegalStateException("Blockchain transaction failed: "+receipt.getTransactionHash());
    return receipt.getTransactionHash();
  }

  public boolean verify(String certificateIdHash, String documentHash) throws Exception {
    if (!configured()) throw new IllegalStateException("Blockchain is not configured.");
    Web3j w=web3();
    Function f=new Function("verifyCertificate",
        java.util.List.of(new Bytes32(bytes32(certificateIdHash)),new Bytes32(bytes32(documentHash))),
        java.util.List.of(new TypeReference<Bool>(){}));
    var response=w.ethCall(Transaction.createEthCallTransaction(null,contractAddress,FunctionEncoder.encode(f)),DefaultBlockParameterName.LATEST).send();
    var decoded=FunctionReturnDecoder.decode(response.getValue(),f.getOutputParameters());
    return !decoded.isEmpty() && (Boolean)((Bool)decoded.get(0)).getValue();
  }
}
