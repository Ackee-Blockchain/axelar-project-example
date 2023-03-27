Install dependencies using npm:
```shell
npm install
```

Install [Woke](https://ackeeblockchain.com/woke/docs):
```shell
pip3 install woke -U
```

To run tests:
1. `woke init pytypes`
2. `woke test`

To view tests coverage:
1. Install [VS Code](https://code.visualstudio.com/)
2. Install the [Tools for Solidity](https://marketplace.visualstudio.com/items?itemName=AckeeBlockchain.tools-for-solidity) extension into VS Code
3. `woke test --coverage`
4. Use the `Tools for Solidity: Show Coverage` command in VS Code
5. Select `woke-coverage.cov`