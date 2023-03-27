// SPDX-License-Identifier: MIT
pragma solidity ^0.8.4;

import "@axelar-network/axelar-gmp-sdk-solidity/contracts/upgradable/Proxy.sol";

contract MyContractProxy is Proxy {
    bytes32 constant private CONTRACT_ID = keccak256("my-project-my-contract");

    constructor(address implementationAddress_, address owner_, bytes memory setupParams_) Proxy(implementationAddress_, owner_, setupParams_) {

    }

    function contractId() internal pure override returns(bytes32) {
        return CONTRACT_ID;
    }
}