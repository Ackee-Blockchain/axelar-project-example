from woke.testing import *
from woke.testing.fuzzing import *
from pytypes.axelarnetwork.axelargmpsdksolidity.contracts.interfaces.IAxelarExecutable import IAxelarExecutable
from pytypes.axelarnetwork.axelarcgpsolidity.contracts.interfaces.IERC20 import IERC20
from pytypes.axelarnetwork.axelargmpsdksolidity.contracts.deploy.Create3Deployer import Create3Deployer
from pytypes.axelarnetwork.axelarcgpsolidity.contracts.AxelarGateway import AxelarGateway
from pytypes.axelarnetwork.axelarcgpsolidity.contracts.TokenDeployer import TokenDeployer
from pytypes.contracts.tests.AuthModuleMock import AuthModuleMock
from pytypes.contracts.MyContract import MyContract
from pytypes.contracts.MyContractProxy import MyContractProxy


chain1 = Chain()
chain2 = Chain()

gw1: AxelarGateway
gw2: AxelarGateway

my_contract1: MyContract
my_contract2: MyContract


def on_revert(f):
    def wrapper(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except TransactionRevertedError as e:
            if e.tx is not None:
                print (e.tx.call_trace)
            raise

    return wrapper


def relay(tx: TransactionAbc) -> None:
    for i, event in enumerate(tx.events):
        if isinstance(event, AxelarGateway.ContractCall):
            if event.destinationChain == "chain1":
                source_chain_str = "chain2"
                source_address_str = str(my_contract2.address)
                destination_chain = chain1
                destination_gw = gw1
            else:
                source_chain_str = "chain1"
                source_address_str = str(my_contract1.address)
                destination_chain = chain2
                destination_gw = gw2
            
            # approve contract call on destination gateway
            command_id = random_bytes(32)
            approve_contract_call_params = Abi.encode(
                ["string", "string", "address", "bytes32", "bytes32", "uint256"],
                [source_chain_str, source_address_str, event.destinationContractAddress, event.payloadHash, bytes.fromhex(tx.tx_hash[2:]), i]
            )
            data = Abi.encode(
                ["uint256", "bytes32[]", "string[]", "bytes[]"],
                [destination_gw.chain.chain_id, [command_id], ["approveContractCall"], [approve_contract_call_params]]
            )
            proof = b""  # not needed because of mocked auth module
            destination_gw.execute(Abi.encode(["bytes", "bytes"], [data, proof]))

            # execute contract call on destination chain
            executable = IAxelarExecutable(event.destinationContractAddress, chain=destination_chain)
            executable.execute(command_id, source_chain_str, source_address_str, event.payload)
        elif isinstance(event, AxelarGateway.ContractCallWithToken):
            if event.destinationChain == "chain1":
                source_chain_str = "chain2"
                source_address_str = str(my_contract2.address)
                destination_chain = chain1
                destination_gw = gw1
            else:
                source_chain_str = "chain1"
                source_address_str = str(my_contract1.address)
                destination_chain = chain2
                destination_gw = gw2
            
            # approve contract call with token on destination gateway
            command_id = random_bytes(32)
            approve_contract_call_with_token_params = Abi.encode(
                ["string", "string", "address", "bytes32", "string", "uint256", "bytes32", "uint256"],
                [source_chain_str, source_address_str, event.destinationContractAddress, event.payloadHash, event.symbol, event.amount, bytes.fromhex(tx.tx_hash[2:]), i]
            )
            data = Abi.encode(
                ["uint256", "bytes32[]", "string[]", "bytes[]"],
                [destination_gw.chain.chain_id, [command_id], ["approveContractCallWithMint"], [approve_contract_call_with_token_params]]
            )
            proof = b""  # not needed because of mocked auth module
            destination_gw.execute(Abi.encode(["bytes", "bytes"], [data, proof]))
            
            # execute contract call with token on destination chain
            executable = IAxelarExecutable(event.destinationContractAddress, chain=destination_chain)
            executable.executeWithToken(command_id, source_chain_str, source_address_str, event.payload, event.symbol, event.amount)
        elif isinstance(event, (
            MyContract.PayloadReceived,
            MyContract.PayloadWithTokenReceived,
        )):
            print(event)


def deploy_token(
    gw: AxelarGateway,
    name: str,
    symbol: str,
    decimals: uint8,
    cap: uint256,
    mint_limit: uint256,
    token_address: Optional[Address] = None,
) -> Address:
    command_id = random_bytes(32)
    deploy_token_params = Abi.encode(
        ["string", "string", "uint8", "uint256", "address", "uint256"],
        [name, symbol, decimals, cap, Address(0) if token_address is None else token_address, mint_limit]
    )

    data = Abi.encode(
        ["uint256", "bytes32[]", "string[]", "bytes[]"],
        [gw.chain.chain_id, [command_id], ["deployToken"], [deploy_token_params]]
    )
    proof = b""
    tx = gw.execute(Abi.encode(["bytes", "bytes"], [data, proof]))
    deploy_events = [e for e in tx.events if isinstance(e, AxelarGateway.TokenDeployed)]
    assert len(deploy_events) == 1
    return deploy_events[0].tokenAddresses


def mint(
    gw: AxelarGateway,
    symbol: str,
    recipient: Address,
    amount: uint256,
):
    command_id = random_bytes(32)
    mint_token_params = Abi.encode(
        ["string", "address", "uint256"],
        [symbol, recipient, amount]
    )

    data = Abi.encode(
        ["uint256", "bytes32[]", "string[]", "bytes[]"],
        [gw.chain.chain_id, [command_id], ["mintToken"], [mint_token_params]]
    )
    proof = b""
    gw.execute(Abi.encode(["bytes", "bytes"], [data, proof]))


@chain1.connect()
@chain2.connect()
@on_revert
def test_default():
    global gw1, gw2, my_contract1, my_contract2

    chain1.set_default_accounts(chain1.accounts[0])
    chain2.set_default_accounts(chain2.accounts[0])

    chain1.tx_callback = relay
    chain2.tx_callback = relay

    # check that client-owned accounts are the same on both chains
    assert chain1.accounts[1].address == chain2.accounts[1].address
    owner = chain1.accounts[1].address

    am1 = AuthModuleMock.deploy(chain=chain1)
    am2 = AuthModuleMock.deploy(chain=chain2)

    td1 = TokenDeployer.deploy(chain=chain1)
    td2 = TokenDeployer.deploy(chain=chain2)

    gw1 = AxelarGateway.deploy(am1, td1, chain=chain1)
    gw2 = AxelarGateway.deploy(am2, td2, chain=chain2)

    token1 = IERC20(deploy_token(gw1, "My Token", "MTK", 18, 2**256-1, 2**256-1), chain=chain1)
    token2 = IERC20(deploy_token(gw2, "My Token", "MTK", 18, 2**256-1, 2**256-1), chain=chain2)

    deployer1 = Create3Deployer.deploy(chain=chain1)
    deployer2 = Create3Deployer.deploy(chain=chain2)

    # deploy implementation contracts with create3 to achieve the same address on both chains
    salt = random_bytes(32)
    my_contract1 = MyContract(
        deployer1.deploy_(MyContract.get_creation_code() + Abi.encode(["address"], [gw1.address]), salt).return_value,
        chain=chain1
    )
    my_contract2 = MyContract(
        deployer2.deploy_(MyContract.get_creation_code() + Abi.encode(["address"], [gw2.address]), salt).return_value,
        chain=chain2
    )
    assert my_contract1.address == my_contract2.address

    # deploy proxy contracts with create3 to achieve the same address on both chains
    salt = random_bytes(32)
    tmp1_proxy = MyContractProxy(
        deployer1.deploy_(MyContractProxy.get_creation_code() + Abi.encode(["address", "address", "bytes"], [my_contract1.address, owner, b""]), salt).return_value,
        chain=chain1
    )
    tmp2_proxy = MyContractProxy(
        deployer2.deploy_(MyContractProxy.get_creation_code() + Abi.encode(["address", "address", "bytes"], [my_contract2.address, owner, b""]), salt).return_value,
        chain=chain2
    )
    assert tmp1_proxy.address == tmp2_proxy.address

    # typing trick, send all requests to proxy contracts
    my_contract1 = MyContract(tmp1_proxy.address, chain=chain1)
    my_contract2 = MyContract(tmp2_proxy.address, chain=chain2)

    my_contract1.sendPayload("chain2", b"hello")
    my_contract2.sendPayload("chain1", b"world")

    # mint 100 tokens on chain1 and send them to my_contract1
    mint(gw1, "MTK", my_contract1.address, 100)
    assert token1.balanceOf(my_contract1) == 100

    # send 100 tokens from my_contract1 to my_contract2
    my_contract1.sendPayloadWithToken("chain2", b"hello", "MTK", 100)
    assert token1.balanceOf(my_contract1) == 0
    assert token2.balanceOf(my_contract2) == 100

    # send tokens back
    my_contract2.sendPayloadWithToken("chain1", b"world", "MTK", 100)
    assert token1.balanceOf(my_contract1) == 100
    assert token2.balanceOf(my_contract2) == 0
