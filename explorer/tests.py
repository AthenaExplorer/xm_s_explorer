import json

from django.test import TestCase
from django.test.client import Client

from xm_s_common import consts
from xm_s_common.cache import Cache

from explorer.interface import ExplorerBase


class ExplorerTestCase(TestCase):

    def setUp(self):
        self.app_id = 'app_id'
        self.client = Client(HTTP_APPID=self.app_id)
        self.miner_id = "f3v3s6efqcb3p4tcola5rr2xitwrwudqg3eqzk4zvqt5u3o65iv4kw2woe3baz3vip6fyzvqcqwuoud5basozq"
        self.miner_address = "f3v3s6efqcb3p4tcola5rr2xitwrwudqg3eqzk4zvqt5u3o65iv4kw2woe3baz3vip6fyzvqcqwuoud5basozq"
        self.high = "285724"
        self.block_id = "bafy2bzacec5axmyqleaihxm5blvv7lna33ekxexwpeag5yygr5ugucekgltkq"
        self.message_id = "bafy2bzacebd3okwik4didnddpqecbsfdszr3asdwkyddkxzhwz53byvnozbpe"
        self.peer = "12D3KooW9wkyBdSHNhpXGromgREmEUR79Wvp2HqrQLiREDu8eXPS"

    def test_get_block_chart(self):
        result = self.client.post(
            '/explorer/api/get_block_chart', {
            }
        ).json()
        print("爆块信息统计")
        print(result)

    def test_get_overview(self):
        result = self.client.post(
            '/explorer/api/get_overview', {
            }
        ).json()
        print("概览")
        print(result)

    def test_get_hashrate_ranking(self):
        result = self.client.post(
            '/explorer/api/get_hashrate_ranking', {
            }
        ).json()
        print("算力走势-有效算力")
        print(result)

    def test_get_power_valid(self):
        result = self.client.post(
            '/explorer/api/get_power_valid', {
            }
        ).json()
        print("矿工排行榜-有效算力")
        print(result)

    def test_get_blocks(self):
        result = self.client.post(
            '/explorer/api/get_blocks', {
            }
        ).json()
        print("矿工排行榜-出块数")
        print(result)

    def test_get_power_growth(self):
        result = self.client.post(
            '/explorer/api/get_power_growth', {
            }
        ).json()
        print("矿工排行榜-算力增速")
        print(result)

    def test_get_tipset(self):
        result = self.client.post(
            '/explorer/api/get_tipset', {
            }
        ).json()
        print("最新区块列表")
        print(result)

    def test_get_message_list(self):
        result = self.client.post(
            '/explorer/api/get_message_list', {
            }
        ).json()
        print("消息列表")
        print(result)

    def test_get_block_statistics(self):
        result = self.client.post(
            '/explorer/api/get_block_statistics', {
            }
        ).json()
        print("出块统计")
        print(result)

    # 搜索相关
    def test_address_overview(self):
        result = self.client.post(
            '/explorer/api/address/{}/overview'.format(self.miner_id), {
            }
        ).json()
        print("账户信息_概览")
        print(result)

    def test_address_balance(self):
        result = self.client.post(
            '/explorer/api/address/{}/balance'.format(self.miner_id), {
            }
        ).json()
        print("账户信息_账户钱包变化")
        print(result)

    def test_power_stats(self):
        result = self.client.post(
            '/explorer/api/address/{}/power-stats'.format(self.miner_id), {
            }
        ).json()
        print("账户信息_消息列表")
        print(result)

    def test_message(self):
        result = self.client.post(
            '/explorer/api/address/{}/message'.format(self.miner_id), {
            }
        ).json()
        print("账户信息_消息列表")
        print(result)

    def test_block_high_info(self):
        result = self.client.post(
            '/explorer/api/block_high/{}/block_high_info'.format(self.high), {
            }
        ).json()
        print("账户信息_消息列表")
        print(result)

    def test_block_info(self):
        result = self.client.post(
            '/explorer/api/block/{}/block_high_info'.format(self.block_id), {
            }
        )
        print("账户信息_消息列表")
        print(result)

    def test_block_message_list(self):
        result = self.client.post(
            '/explorer/api/block/{}/block_high_info'.format(self.block_id), {
            }
        )
        print('------------------------------', result)
        print("账户信息_消息列表")
        print(result)

    def test_message_info(self):
        result = self.client.post(
            '/explorer/api/block/{}/block_high_info'.format(self.message_id), {
            }
        )
        print('------------------------------', result)
        print("账户信息_消息列表")
        print(result)

    def test_peer_info(self):
        result = self.client.post(
            '/explorer/api/block/{}/block_high_info'.format(self.peer), {
            }
        )
        print('------------------------------', result)
        print("账户信息_消息列表")
        print(result)


    def test_get_block_distribution(self):
        result = self.client.post(
            '/explorer/api/get_block_distribution'.format(self.peer), {
            }
        )
        print(result)
    def test_get_mining_earnings(self):
        result = self.client.post(
            '/explorer/api/get_mining_earnings'.format(self.peer), {
            }
        ).json()
        print(result)
    def test_get_sector_pledge(self):
        result = self.client.post(
            '/explorer/api/get_sector_pledge'.format(self.peer), {
            }
        ).json()
        print(result)
    def test_get_miner_power_increment_tendency(self):
        result = self.client.post(
            '/explorer/api/get_miner_power_increment_tendency'.format(self.peer), {
            }
        ).json()
        print(result)
    def test_get_gas_tendency(self):
        result = self.client.post(
            '/explorer/api/get_gas_tendency'.format(self.peer), {
            }
        ).json()
        print(result)
    def test_get_gas_data_24h(self):
        result = self.client.post(
            '/explorer/api/get_gas_data_24h'.format(self.peer), {
            }
        ).json()
        print(result)
