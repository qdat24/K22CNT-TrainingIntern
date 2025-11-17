# ============================================
# WEB3 PAYMENT BACKEND - COMPLETE VERSION
# Flask Routes for USDT Payment Processing
# ============================================

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta
import json
import hashlib
import secrets

# Optional: Web3 integration (uncomment when ready to use)
# from web3 import Web3
# from decimal import Decimal

# Create blueprint
web3_bp = Blueprint('web3', __name__)

# ============================================
# CONFIGURATION
# ============================================

# Store transactions in memory (use Redis/Database in production)
web3_transactions = {}
pending_payments = {}

# USDT Rate (update from API in production)
USDT_RATE = 25000  # 1 USDT = 25,000 VND

# Supported Networks
SUPPORTED_NETWORKS = {
    1: {
        'name': 'Ethereum Mainnet',
        'rpc': 'https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY',
        'usdt_address': '0xdac17f958d2ee523a2206206994597c13d831ec7',
        'explorer': 'https://etherscan.io',
        'gas_price': 'high'
    },
    56: {
        'name': 'BNB Smart Chain',
        'rpc': 'https://bsc-dataseed.binance.org',
        'usdt_address': '0x55d398326f99059fF775485246999027B3197955',
        'explorer': 'https://bscscan.com',
        'gas_price': 'low'
    },
    137: {
        'name': 'Polygon',
        'rpc': 'https://polygon-rpc.com',
        'usdt_address': '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
        'explorer': 'https://polygonscan.com',
        'gas_price': 'low'
    },
    5: {
        'name': 'Goerli Testnet',
        'rpc': 'https://goerli.infura.io/v3/YOUR_API_KEY',
        'usdt_address': '0x509Ee0d083DdF8AC028f2a56731412edD63223B9',
        'explorer': 'https://goerli.etherscan.io',
        'gas_price': 'low'
    },
    97: {
        'name': 'BSC Testnet',
        'rpc': 'https://data-seed-prebsc-1-s1.binance.org:8545',
        'usdt_address': '0x337610d27c682E347C9cD60BD4b3b107C9d34dDd',
        'explorer': 'https://testnet.bscscan.com',
        'gas_price': 'low'
    },
    80001: {
        'name': 'Mumbai Testnet',
        'rpc': 'https://rpc-mumbai.maticvigil.com',
        'usdt_address': '0x3813e82e6f7098b9583FC0F33a962D02018B6803',
        'explorer': 'https://mumbai.polygonscan.com',
        'gas_price': 'low'
    }
}

# Recipient Wallet Address (YOUR WALLET - CHANGE THIS!)
RECIPIENT_WALLET = '0x3fd86c3728b38cb6b09fa7d4914888dcfef1518c'

# Payment timeout (15 minutes)
PAYMENT_TIMEOUT = 15 * 60  # seconds

# ============================================
# MAIN ROUTES
# ============================================

@web3_bp.route('/usdt-payment')
def usdt_payment_page():
    """
    Render USDT payment page
    URL: /usdt-payment?order_id=XXX&amount=YYY
    """
    # Get order info from query params or session
    order_id = request.args.get('order_id', session.get('pending_order_id'))
    total_amount = request.args.get('amount', session.get('cart_total', 0))
    
    if not order_id:
        return redirect(url_for('checkout'))
    
    # Convert to int
    try:
        total_amount = int(total_amount)
    except (ValueError, TypeError):
        total_amount = 0
    
    # Calculate USDT amount
    usdt_amount = round(total_amount / USDT_RATE, 2)
    
    # Create payment session
    payment_id = create_payment_session(order_id, total_amount, usdt_amount)
    
    return render_template('usdt-payment.html',
                         order_id=order_id,
                         amount=total_amount,
                         payment_id=payment_id)


@web3_bp.route('/payment-success')
def payment_success():
    """Payment success page"""
    order_id = request.args.get('order_id')
    tx_hash = request.args.get('tx_hash')
    
    return render_template('payment-success.html',
                         order_id=order_id,
                         tx_hash=tx_hash)


# ============================================
# API ENDPOINTS
# ============================================

@web3_bp.route('/api/web3/payment-info', methods=['GET'])
def get_payment_info():
    """
    Get payment information for order
    
    GET /api/web3/payment-info?order_id=XXX
    
    Response:
    {
        "success": true,
        "order_id": "ORD123",
        "amount_vnd": 15000000,
        "amount_usdt": "600.00",
        "usdt_rate": 25000,
        "recipient_wallet": "0x...",
        "supported_networks": {...},
        "payment_id": "pay_xxx",
        "expires_at": "2025-01-15T12:00:00"
    }
    """
    order_id = request.args.get('order_id')
    
    if not order_id:
        return jsonify({'success': False, 'error': 'Order ID required'}), 400
    
    # Get order from database (example with mock data)
    # In production: order = db.orders.find_one({'id': order_id})
    order = {
        'id': order_id,
        'total': int(request.args.get('amount', 15000000)),
        'status': 'pending_payment'
    }
    
    # Calculate USDT amount
    usdt_amount = round(order['total'] / USDT_RATE, 2)
    
    # Create or get existing payment session
    payment_id = create_payment_session(order_id, order['total'], usdt_amount)
    payment = pending_payments.get(payment_id, {})
    
    return jsonify({
        'success': True,
        'order_id': order_id,
        'amount_vnd': order['total'],
        'amount_usdt': str(usdt_amount),
        'usdt_rate': USDT_RATE,
        'recipient_wallet': RECIPIENT_WALLET,
        'supported_networks': {
            str(k): v['name'] for k, v in SUPPORTED_NETWORKS.items()
        },
        'payment_id': payment_id,
        'expires_at': payment.get('expires_at', ''),
        'timeout_seconds': PAYMENT_TIMEOUT
    })


@web3_bp.route('/api/web3/submit-payment', methods=['POST'])
def submit_payment():
    """
    Submit Web3 payment transaction
    
    POST /api/web3/submit-payment
    Body:
    {
        "order_id": "ORD123",
        "tx_hash": "0x...",
        "chain_id": 56,
        "from_address": "0x...",
        "amount_usdt": "600.00"
    }
    
    Response:
    {
        "success": true,
        "message": "Payment submitted successfully",
        "transaction": {...}
    }
    """
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['order_id', 'tx_hash', 'chain_id', 'from_address', 'amount_usdt']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        order_id = data['order_id']
        tx_hash = data['tx_hash']
        chain_id = int(data['chain_id'])
        from_address = data['from_address']
        amount_usdt = data['amount_usdt']
        
        # Validate chain ID
        if chain_id not in SUPPORTED_NETWORKS:
            return jsonify({
                'success': False,
                'error': f'Unsupported network: {chain_id}'
            }), 400
        
        # Validate transaction hash format
        if not tx_hash.startswith('0x') or len(tx_hash) != 66:
            return jsonify({
                'success': False,
                'error': 'Invalid transaction hash format'
            }), 400
        
        # Check if transaction already exists
        if tx_hash in web3_transactions:
            return jsonify({
                'success': False,
                'error': 'Transaction already submitted'
            }), 400
        
        # Create transaction record
        transaction = {
            'order_id': order_id,
            'tx_hash': tx_hash,
            'chain_id': chain_id,
            'network_name': SUPPORTED_NETWORKS[chain_id]['name'],
            'from_address': from_address.lower(),
            'to_address': RECIPIENT_WALLET.lower(),
            'amount_usdt': amount_usdt,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending',
            'confirmed': False,
            'confirmations': 0
        }
        
        # Store transaction
        web3_transactions[tx_hash] = transaction
        
        # Update order payment info (in production, update database)
        # db.orders.update_one(
        #     {'id': order_id},
        #     {'$set': {
        #         'payment_method': 'USDT',
        #         'payment_status': 'pending_confirmation',
        #         'tx_hash': tx_hash,
        #         'chain_id': chain_id,
        #         'updated_at': datetime.now()
        #     }}
        # )
        
        print(f"✅ USDT Payment submitted:")
        print(f"   Order: {order_id}")
        print(f"   TX Hash: {tx_hash}")
        print(f"   Network: {SUPPORTED_NETWORKS[chain_id]['name']}")
        print(f"   Amount: {amount_usdt} USDT")
        print(f"   From: {from_address}")
        
        # Start verification process (optional)
        # verify_transaction_async(tx_hash, chain_id)
        
        return jsonify({
            'success': True,
            'message': 'Payment submitted successfully. We will verify your transaction on the blockchain.',
            'transaction': transaction,
            'explorer_url': f"{SUPPORTED_NETWORKS[chain_id]['explorer']}/tx/{tx_hash}"
        })
        
    except Exception as e:
        print(f"❌ Error submitting payment: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@web3_bp.route('/api/web3/verify-payment', methods=['POST'])
def verify_payment():
    """
    Manually verify a payment transaction
    
    POST /api/web3/verify-payment
    Body:
    {
        "tx_hash": "0x...",
        "chain_id": 56
    }
    """
    try:
        data = request.json
        tx_hash = data.get('tx_hash')
        chain_id = int(data.get('chain_id', 0))
        
        if not tx_hash or not chain_id:
            return jsonify({
                'success': False,
                'error': 'Missing parameters'
            }), 400
        
        # Get transaction from storage
        transaction = web3_transactions.get(tx_hash)
        
        if not transaction:
            return jsonify({
                'success': False,
                'error': 'Transaction not found'
            }), 404
        
        # In production: Verify with Web3
        # verified, confirmations = verify_transaction_on_chain(tx_hash, chain_id)
        
        # Mock verification for now
        verified = True
        confirmations = 12
        
        if verified:
            # Update transaction status
            transaction['status'] = 'confirmed'
            transaction['confirmed'] = True
            transaction['confirmations'] = confirmations
            transaction['confirmed_at'] = datetime.now().isoformat()
            
            web3_transactions[tx_hash] = transaction
            
            # Update order status
            order_id = transaction['order_id']
            # db.orders.update_one(
            #     {'id': order_id},
            #     {'$set': {
            #         'payment_status': 'confirmed',
            #         'status': 'processing',
            #         'confirmed_at': datetime.now()
            #     }}
            # )
            
            print(f"✅ Payment verified: {tx_hash}")
            print(f"   Confirmations: {confirmations}")
            
            return jsonify({
                'success': True,
                'verified': True,
                'confirmations': confirmations,
                'transaction': transaction
            })
        else:
            return jsonify({
                'success': False,
                'verified': False,
                'message': 'Transaction not found on blockchain'
            })
        
    except Exception as e:
        print(f"❌ Error verifying payment: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@web3_bp.route('/api/web3/check-status/<tx_hash>')
def check_payment_status(tx_hash):
    """
    Check payment status by transaction hash
    
    GET /api/web3/check-status/0x...
    
    Response:
    {
        "success": true,
        "status": "confirmed",
        "transaction": {...}
    }
    """
    transaction = web3_transactions.get(tx_hash)
    
    if not transaction:
        return jsonify({
            'success': False,
            'error': 'Transaction not found'
        }), 404
    
    return jsonify({
        'success': True,
        'status': transaction['status'],
        'confirmed': transaction['confirmed'],
        'confirmations': transaction.get('confirmations', 0),
        'transaction': transaction
    })


@web3_bp.route('/api/web3/usdt-rate')
def get_usdt_rate():
    """
    Get current USDT/VND exchange rate
    
    GET /api/web3/usdt-rate
    
    Response:
    {
        "success": true,
        "rate": 25000,
        "currency": "VND",
        "updated_at": "2025-01-15T10:00:00"
    }
    """
    # In production: Fetch real-time rate from API
    # import requests
    # response = requests.get('https://api.coingecko.com/api/v3/simple/price',
    #                        params={'ids': 'tether', 'vs_currencies': 'vnd'})
    # rate = response.json()['tether']['vnd']
    
    return jsonify({
        'success': True,
        'rate': USDT_RATE,
        'currency': 'VND',
        'updated_at': datetime.now().isoformat()
    })


@web3_bp.route('/api/web3/network-info/<int:chain_id>')
def get_network_info(chain_id):
    """
    Get network information
    
    GET /api/web3/network-info/56
    """
    network = SUPPORTED_NETWORKS.get(chain_id)
    
    if not network:
        return jsonify({
            'success': False,
            'error': 'Network not supported'
        }), 404
    
    return jsonify({
        'success': True,
        'chain_id': chain_id,
        'network': network
    })


# ============================================
# HELPER FUNCTIONS
# ============================================

def create_payment_session(order_id, amount_vnd, amount_usdt):
    """Create a payment session with timeout"""
    payment_id = f"pay_{secrets.token_urlsafe(16)}"
    
    expires_at = datetime.now() + timedelta(seconds=PAYMENT_TIMEOUT)
    
    payment = {
        'payment_id': payment_id,
        'order_id': order_id,
        'amount_vnd': amount_vnd,
        'amount_usdt': amount_usdt,
        'created_at': datetime.now().isoformat(),
        'expires_at': expires_at.isoformat(),
        'status': 'pending'
    }
    
    pending_payments[payment_id] = payment
    
    return payment_id


def verify_transaction_on_chain(tx_hash, chain_id):
    """
    Verify transaction on blockchain using Web3
    
    Returns: (verified: bool, confirmations: int)
    """
    # Uncomment when ready to use Web3
    """
    try:
        network = SUPPORTED_NETWORKS.get(chain_id)
        if not network:
            return False, 0
        
        # Connect to blockchain
        w3 = Web3(Web3.HTTPProvider(network['rpc']))
        
        if not w3.is_connected():
            print(f"❌ Failed to connect to {network['name']}")
            return False, 0
        
        # Get transaction receipt
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        
        if not receipt:
            return False, 0
        
        # Check if transaction was successful
        if receipt['status'] != 1:
            return False, 0
        
        # Get transaction details
        tx = w3.eth.get_transaction(tx_hash)
        
        # Verify recipient address
        if tx['to'].lower() != RECIPIENT_WALLET.lower():
            print(f"❌ Wrong recipient: {tx['to']}")
            return False, 0
        
        # Calculate confirmations
        current_block = w3.eth.block_number
        tx_block = receipt['blockNumber']
        confirmations = current_block - tx_block
        
        print(f"✅ Transaction verified on {network['name']}")
        print(f"   Confirmations: {confirmations}")
        
        return True, confirmations
        
    except Exception as e:
        print(f"❌ Error verifying transaction: {e}")
        return False, 0
    """
    
    # Mock for now
    return True, 12


def format_currency(amount):
    """Format VND currency"""
    return f"{amount:,.0f}₫".replace(',', '.')


# ============================================
# WEBHOOK (Optional - for blockchain monitoring)
# ============================================

@web3_bp.route('/webhook/payment-notification', methods=['POST'])
def payment_webhook():
    """
    Webhook endpoint for payment notifications
    from blockchain monitoring services like Alchemy, QuickNode, etc.
    """
    try:
        # Verify webhook signature (IMPORTANT!)
        signature = request.headers.get('X-Signature')
        # if not verify_webhook_signature(request.data, signature):
        #     return jsonify({'error': 'Invalid signature'}), 401
        
        data = request.json
        
        tx_hash = data.get('transaction', {}).get('hash')
        status = data.get('status')
        
        if tx_hash and tx_hash in web3_transactions:
            transaction = web3_transactions[tx_hash]
            
            if status == 'confirmed':
                transaction['status'] = 'confirmed'
                transaction['confirmed'] = True
                transaction['webhook_received'] = True
                transaction['confirmed_at'] = datetime.now().isoformat()
                
                # Update order
                order_id = transaction['order_id']
                print(f"✅ Webhook: Payment confirmed for order {order_id}")
                
                # Update database
                # db.orders.update_one(
                #     {'id': order_id},
                #     {'$set': {'payment_status': 'confirmed'}}
                # )
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================
# INITIALIZATION
# ============================================

def init_web3_payment(app):
    """Initialize Web3 payment system"""
    app.register_blueprint(web3_bp)
    
    # Add Jinja2 filters
    app.jinja_env.filters['format_currency'] = format_currency
    
    print("=" * 50)
    print("💰 Web3 Payment System Initialized")
    print("=" * 50)
    print(f"Recipient Wallet: {RECIPIENT_WALLET}")
    print(f"USDT Rate: 1 USDT = {USDT_RATE:,} VND")
    print(f"Supported Networks: {len(SUPPORTED_NETWORKS)}")
    for chain_id, network in SUPPORTED_NETWORKS.items():
        print(f"  - {network['name']} (Chain ID: {chain_id})")
    print(f"Payment Timeout: {PAYMENT_TIMEOUT // 60} minutes")
    print("=" * 50)


if __name__ == '__main__':
    print("Web3 Payment Backend Module")
    print("Import this module in your Flask app:")
    print("  from web3_payment import init_web3_payment")
    print("  init_web3_payment(app)")