// SPDX-License-Identifier: MIT
pragma solidity ^0.8.4;

import "@axelar-network/axelar-gmp-sdk-solidity/contracts/executable/AxelarExecutable.sol";
import "@axelar-network/axelar-gmp-sdk-solidity/contracts/upgradable/Upgradable.sol";
import "@axelar-network/axelar-gmp-sdk-solidity/contracts/utils/AddressString.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract MyContract is AxelarExecutable, Upgradable {
    using AddressToString for address;
    using SafeERC20 for IERC20;

    bytes32 constant CONTRACT_ID = keccak256("my-project-my-contract");

    event PayloadReceived(string sourceChain, string sourceAddress, bytes payload);

    event PayloadWithTokenReceived(
        string sourceChain,
        string sourceAddress,
        bytes payload,
        string tokenSymbol,
        uint256 amount
    );

    constructor(address gateway_) AxelarExecutable(gateway_) {

    }

    function contractId() external pure returns (bytes32) {
        return CONTRACT_ID;
    }

    function _execute(
        string calldata sourceChain,
        string calldata sourceAddress,
        bytes calldata payload
    ) internal override {
        emit PayloadReceived(sourceChain, sourceAddress, payload);
    }

    function _executeWithToken(
        string calldata sourceChain,
        string calldata sourceAddress,
        bytes calldata payload,
        string calldata tokenSymbol,
        uint256 amount
    ) internal override {
        emit PayloadWithTokenReceived(sourceChain, sourceAddress, payload, tokenSymbol, amount);
    }

    function sendPayload(
        string calldata destinationChain,
        bytes calldata payload
    ) external {
        gateway.callContract(destinationChain, address(this).toString(), payload);
    }

    function sendPayloadWithToken(
        string calldata destinationChain,
        bytes calldata payload,
        string calldata tokenSymbol,
        uint256 amount
    ) external {
        IERC20 token = IERC20(gateway.tokenAddresses(tokenSymbol));
        token.safeApprove(address(gateway), amount);

        gateway.callContractWithToken(
            destinationChain,
            address(this).toString(),
            payload,
            tokenSymbol,
            amount
        );
    }
}