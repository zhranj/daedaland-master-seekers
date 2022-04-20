from brownie import accounts, config, network

LOCAL_ENVIRONMENTS = ["development", "ganache", "mainnet-fork"]


def get_deployer_account(id=None):
    if network.show_active() in LOCAL_ENVIRONMENTS:
        return accounts[0]
    if id:
        return accounts.load(id)
    return accounts.add(config["wallets"]["deployer"])


def get_user_account(id=None):
    if network.show_active() in LOCAL_ENVIRONMENTS:
        return accounts[1]
    if id:
        return accounts.load(id)
    return accounts.add(config["wallets"]["user"])
