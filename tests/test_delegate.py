from tests.conftest import *


def test_staking_block_number():
    staking_block_number = aide.delegate._staking_block_number
    assert isinstance(staking_block_number, int)


def test_delegate():
    # todo: 委托地址不被允许委托，待解决
    account = aide.platon.account.create()
    address = account.address
    transfer_result = aide.transfer.transfer(to_address=address, amount=aide.delegate._economic.staking_limit)
    private_key = account.privateKey.hex()[2:]
    result = aide.delegate.delegate(private_key=private_key)
    delegate_info = aide.delegate.get_delegate_info()


def test_withdrew_delegate():
    pass

def test_get_delegate_info():
    pass

def test_get_delegate_list():
    pass

def test_withdraw_delegate_reward():
    pass

def test_get_delegate_reward():
    pass