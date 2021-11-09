import functools
import time

from platon import Web3, HTTPProvider, WebsocketProvider, IPCProvider
from platon.middleware import gplaton_poa_middleware

from economic import gas
from govern import Govern
from solidity import Solidity
from staking import Staking
from transfer import Transfer
from utils import send_transaction, ec_recover
from wasm import Wasm


def get_web3(uri, chain_id=None, hrp=None):
    """ 通过rpc uri，获取web3对象。可以兼容历史platon版本
    """
    if uri.startswith('http'):
        provider = HTTPProvider
    elif uri.startswith('ws'):
        provider = WebsocketProvider
    elif uri.startswith('ipc'):
        provider = IPCProvider
    else:
        raise ValueError(f'unidentifiable uri {uri}')

    return Web3(provider(uri), chain_id=chain_id, hrp=hrp)


def custom_return(func):
    """
    包装类，用于在调用Module及其子类的方法时，自定义要返回的结果
    可以返回未发送的交易dict、交易hash、交易回执
    """

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        txn = kwargs['txn']
        private_key = kwargs['private_key'] or self.default_account.private_key

        txn = func(*args, **kwargs).build_transaction(txn)
        if self.returns == 'txn':
            return txn
        return self.send_transaction(txn, private_key, self.returns)

    return wrapper


class Module:
    address: None

    def __init__(self, web3: Web3):
        self.web3 = web3
        self.default_account = None
        self.returns = 'receipt'  # 包含：txn, hash, receipt

    def _get_node_info(self):
        node_info = self.web3.node.admin.node_info()
        self.node_id = node_info['id']
        self.bls_pubkey = node_info['blsPubKey']
        self.bls_proof = self.web3.node.admin.get_schnorr_NIZK_prove()
        version_info = self.web3.node.admin.get_program_version()
        self.version = version_info['Version']
        self.version_sign = version_info['Sign']

    def send_transaction(self, txn, private_key, returns='receipt'):
        return send_transaction(self.web3, txn, private_key, returns)

    def set_default_account(self, account):
        self.default_account = account

    def set_returns(self, returns):
        if returns in ('txn', 'hash', 'receipt'):
            self.returns = returns
        else:
            raise ValueError('Unrecognized value')


class PlatonAide:
    """ 主类，platon各个子模块的集合体，同时支持创建账户、解码等非交易类的操作
    """

    def __init__(self, uri: str, chain_id: int = None, hrp: str = None):
        self.uri = uri
        self.web3 = get_web3(uri, chain_id, hrp)
        self.web3.middleware_onion.inject(gplaton_poa_middleware, layer=0)
        super().__init__(self.web3)
        self.hrp = hrp or self.web3.hrp
        self.chain_id = chain_id or self.web3.platon.chain_id
        # 加入接口和模块
        self.platon = self.web3.platon
        self.admin = self.web3.node.admin
        self.personal = self.web3.node.personal
        self.txpool = self.web3.node.txpool
        self.debug = self.web3.debug
        self.economic = gas
        self.transfer = Transfer(self.web3)
        self.staking = Staking(self.web3)
        self.govern = Govern(self.web3)
        self.solidity = Solidity(self.web3)
        self.wasm = Wasm(self.web3)

    def create_account(self):
        """ 创建账户
        """
        account = self.platon.account.create(hrp=self.hrp)
        address = account.address
        private_key = account.privateKey.hex()[2:]
        return address, private_key

    def create_hd_account(self):
        """ 创建HD账户
        """
        # todo: coding
        pass

    def send_transaction(self, txn, private_key, returns='receipt'):
        """ 签名交易并发送
        """
        return send_transaction(self.web3, txn, private_key, returns)

    def wait_block(self, to_block=None, interval=3):
        """ 等待块高
        """
        current_block = self.platon.block_number
        while current_block < to_block:
            time.sleep(interval)
            current_block = self.platon.block_number

    def ec_recover(self, block_identifier):
        """ 获取出块节点公钥
        """
        block = self.web3.platon.get_block(block_identifier)
        return ec_recover(block)
