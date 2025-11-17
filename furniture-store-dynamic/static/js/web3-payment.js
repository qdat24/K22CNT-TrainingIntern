// ============================================
// WEB3 USDT PAYMENT SYSTEM
// Supports: Ethereum, BSC, Polygon
// ============================================

// USDT Contract Addresses
const USDT_CONTRACTS = {
    1: '0xdac17f958d2ee523a2206206994597c13d831ec7',      // Ethereum Mainnet
    56: '0x55d398326f99059fF775485246999027B3197955',     // BSC Mainnet
    137: '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',    // Polygon Mainnet
    5: '0x509Ee0d083DdF8AC028f2a56731412edD63223B9',      // Goerli Testnet
    97: '0x337610d27c682E347C9cD60BD4b3b107C9d34dDd',     // BSC Testnet
    80001: '0x3813e82e6f7098b9583FC0F33a962D02018B6803' // Mumbai Testnet
};

// Network Configuration
const NETWORKS = {
    1: {
        name: 'Ethereum Mainnet',
        symbol: 'ETH',
        rpc: 'https://eth.llamarpc.com',
        explorer: 'https://etherscan.io',
        icon: '⟠'
    },
    56: {
        name: 'BNB Smart Chain',
        symbol: 'BNB',
        rpc: 'https://bsc-dataseed.binance.org',
        explorer: 'https://bscscan.com',
        icon: '🔶'
    },
    137: {
        name: 'Polygon',
        symbol: 'MATIC',
        rpc: 'https://polygon-rpc.com',
        explorer: 'https://polygonscan.com',
        icon: '🟣'
    },
    5: {
        name: 'Goerli Testnet',
        symbol: 'ETH',
        rpc: 'https://goerli.infura.io/v3/',
        explorer: 'https://goerli.etherscan.io',
        icon: '🧪'
    },
    97: {
        name: 'BSC Testnet',
        symbol: 'tBNB',
        rpc: 'https://data-seed-prebsc-1-s1.binance.org:8545',
        explorer: 'https://testnet.bscscan.com',
        icon: '🧪'
    },
    80001: {
        name: 'Mumbai Testnet',
        symbol: 'MATIC',
        rpc: 'https://rpc-mumbai.maticvigil.com',
        explorer: 'https://mumbai.polygonscan.com',
        icon: '🧪'
    }
};

// USDT ABI (ERC20 Standard)
const USDT_ABI = [
    {
        "constant": true,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": false,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": false,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
];

class Web3PaymentSystem {
    constructor() {
        this.web3 = null;
        this.account = null;
        this.chainId = null;
        this.usdtContract = null;
        this.recipientAddress = '0x3fd86c3728b38cb6b09fa7d4914888dcfef1518c'; // YOUR WALLET - CHANGE THIS!
        this.usdRate = 25000; // 1 USD = 25,000 VND (update from API)
    }

    // Initialize Web3
    async init() {
        if (typeof window.ethereum !== 'undefined') {
            try {
                this.web3 = new Web3(window.ethereum);
                console.log('✅ Web3 initialized');
                return true;
            } catch (error) {
                console.error('❌ Web3 initialization failed:', error);
                return false;
            }
        } else {
            console.error('❌ MetaMask not detected');
            this.showInstallMetaMask();
            return false;
        }
    }

    // Connect Wallet
    async connectWallet() {
        try {
            const accounts = await window.ethereum.request({
                method: 'eth_requestAccounts'
            });
            
            this.account = accounts[0];
            this.chainId = await window.ethereum.request({ method: 'eth_chainId' });
            this.chainId = parseInt(this.chainId, 16);

            console.log('✅ Wallet connected:', this.account);
            console.log('🔗 Chain ID:', this.chainId);

            // Initialize USDT contract
            await this.initUSDTContract();

            // Listen for account changes
            this.setupListeners();

            return {
                success: true,
                account: this.account,
                chainId: this.chainId,
                network: NETWORKS[this.chainId]?.name || 'Unknown Network'
            };
        } catch (error) {
            console.error('❌ Wallet connection failed:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    // Initialize USDT Contract
    async initUSDTContract() {
        const usdtAddress = USDT_CONTRACTS[this.chainId];
        
        if (!usdtAddress) {
            throw new Error('USDT not supported on this network');
        }

        this.usdtContract = new this.web3.eth.Contract(USDT_ABI, usdtAddress);
        console.log('✅ USDT Contract initialized:', usdtAddress);
    }

    // Get USDT Balance
    async getUSDTBalance() {
        try {
            const balance = await this.usdtContract.methods.balanceOf(this.account).call();
            const decimals = await this.usdtContract.methods.decimals().call();
            const formattedBalance = balance / Math.pow(10, decimals);
            
            console.log('💰 USDT Balance:', formattedBalance);
            return formattedBalance;
        } catch (error) {
            console.error('❌ Failed to get USDT balance:', error);
            return 0;
        }
    }

    // Convert VND to USDT
    vndToUsdt(vndAmount) {
        return (vndAmount / this.usdRate).toFixed(2);
    }

    // Send USDT Payment
    async sendPayment(amountVND, orderId) {
        try {
            // Convert VND to USDT
            const usdtAmount = this.vndToUsdt(amountVND);
            const decimals = await this.usdtContract.methods.decimals().call();
            const amountInWei = this.web3.utils.toBN(Math.floor(usdtAmount * Math.pow(10, decimals)));

            console.log('💸 Sending payment:', {
                vnd: amountVND,
                usdt: usdtAmount,
                orderId: orderId,
                amountInWei: amountInWei.toString()
            });

            // Check balance
            const balance = await this.getUSDTBalance();
            if (balance < parseFloat(usdtAmount)) {
                throw new Error(`Insufficient USDT balance. Required: ${usdtAmount} USDT, Available: ${balance} USDT`);
            }

            // Estimate gas
            let gasEstimate;
            try {
                gasEstimate = await this.usdtContract.methods
                    .transfer(this.recipientAddress, amountInWei.toString())
                    .estimateGas({ from: this.account });
                
                gasEstimate = Math.floor(gasEstimate * 1.2); // Add 20% buffer
            } catch (error) {
                console.warn('⚠️ Gas estimation failed, using default:', error.message);
                gasEstimate = 100000;
            }

            console.log('⛽ Gas estimate:', gasEstimate);

            // Send transaction
            const tx = await this.usdtContract.methods
                .transfer(this.recipientAddress, amountInWei.toString())
                .send({
                    from: this.account,
                    gas: gasEstimate
                });

            console.log('✅ Payment successful:', tx.transactionHash);

            return {
                success: true,
                txHash: tx.transactionHash,
                amount: usdtAmount,
                orderId: orderId,
                explorer: `${NETWORKS[this.chainId].explorer}/tx/${tx.transactionHash}`
            };

        } catch (error) {
            console.error('❌ Payment failed:', error);
            
            // Parse error message
            let errorMessage = error.message;
            if (error.message.includes('insufficient funds')) {
                errorMessage = 'Insufficient funds for gas fee';
            } else if (error.message.includes('User denied')) {
                errorMessage = 'Transaction rejected by user';
            } else if (error.message.includes('execution reverted')) {
                errorMessage = 'Transaction failed. Please check your balance and allowance.';
            }
            
            return {
                success: false,
                error: errorMessage
            };
        }
    }

    // Switch Network
    async switchNetwork(chainId) {
        try {
            await window.ethereum.request({
                method: 'wallet_switchEthereumChain',
                params: [{ chainId: this.web3.utils.toHex(chainId) }]
            });
            
            this.chainId = chainId;
            await this.initUSDTContract();
            
            console.log('✅ Network switched to:', NETWORKS[chainId].name);
            return true;
        } catch (error) {
            // If network not added, try to add it
            if (error.code === 4902) {
                return await this.addNetwork(chainId);
            }
            console.error('❌ Failed to switch network:', error);
            return false;
        }
    }

    // Add Network to MetaMask
    async addNetwork(chainId) {
        const network = NETWORKS[chainId];
        
        try {
            await window.ethereum.request({
                method: 'wallet_addEthereumChain',
                params: [{
                    chainId: this.web3.utils.toHex(chainId),
                    chainName: network.name,
                    nativeCurrency: {
                        name: network.symbol,
                        symbol: network.symbol,
                        decimals: 18
                    },
                    rpcUrls: [network.rpc],
                    blockExplorerUrls: [network.explorer]
                }]
            });
            
            console.log('✅ Network added:', network.name);
            return true;
        } catch (error) {
            console.error('❌ Failed to add network:', error);
            return false;
        }
    }

    // Setup Event Listeners
    setupListeners() {
        if (window.ethereum) {
            // Account changed
            window.ethereum.on('accountsChanged', (accounts) => {
                if (accounts.length === 0) {
                    console.log('🔌 Wallet disconnected');
                    this.account = null;
                    this.onDisconnect();
                } else {
                    this.account = accounts[0];
                    console.log('🔄 Account changed:', this.account);
                    this.onAccountChanged(this.account);
                }
            });

            // Chain changed
            window.ethereum.on('chainChanged', (chainId) => {
                this.chainId = parseInt(chainId, 16);
                console.log('🔄 Chain changed:', this.chainId);
                this.onChainChanged(this.chainId);
                window.location.reload(); // Reload to reinitialize
            });
        }
    }

    // Show Install MetaMask Message
    showInstallMetaMask() {
        const message = `
            <div style="padding: 20px; text-align: center;">
                <h3>🦊 MetaMask Required</h3>
                <p>Please install MetaMask to use Web3 payment</p>
                <a href="https://metamask.io/download/" target="_blank" 
                   style="display: inline-block; margin-top: 15px; padding: 12px 30px; 
                          background: #f6851b; color: white; text-decoration: none; 
                          border-radius: 8px; font-weight: 600;">
                    Install MetaMask
                </a>
            </div>
        `;
        
        alert('Please install MetaMask to use Web3 payment\n\nVisit: https://metamask.io/download/');
    }

    // Event Callbacks (override these in your app)
    onAccountChanged(account) {
        // Update UI with new account
        console.log('Account changed callback:', account);
    }

    onChainChanged(chainId) {
        // Update UI with new network
        console.log('Chain changed callback:', chainId);
    }

    onDisconnect() {
        // Handle disconnect
        console.log('Disconnect callback');
    }

    // Get Current Network Info
    getNetworkInfo() {
        return {
            chainId: this.chainId,
            network: NETWORKS[this.chainId] || null,
            account: this.account,
            usdtContract: USDT_CONTRACTS[this.chainId] || null
        };
    }

    // Disconnect Wallet
    disconnect() {
        this.account = null;
        this.chainId = null;
        this.usdtContract = null;
        console.log('🔌 Wallet disconnected');
    }

    // Get Gas Price
    async getGasPrice() {
        try {
            const gasPrice = await this.web3.eth.getGasPrice();
            return this.web3.utils.fromWei(gasPrice, 'gwei');
        } catch (error) {
            console.error('❌ Failed to get gas price:', error);
            return 0;
        }
    }

    // Format Address (short version)
    formatAddress(address) {
        if (!address) return '';
        return `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
    }
}

// Export for use
if (typeof window !== 'undefined') {
    window.Web3PaymentSystem = Web3PaymentSystem;
    window.NETWORKS = NETWORKS;
    window.USDT_CONTRACTS = USDT_CONTRACTS;
    console.log('✅ Web3 Payment System loaded');
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { Web3PaymentSystem, NETWORKS, USDT_CONTRACTS };
}