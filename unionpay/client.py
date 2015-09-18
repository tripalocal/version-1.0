import datetime
import requests
from unionpay import error
from unionpay.signer import Signer
from unionpay.util.helper import make_submit_form
from urllib.parse import urlencode

class TradeType(object):
    pay = '01'
    query = '00'
    revoke = '31'
    refund = '04'
    auth = '02'
    auth_revoke = '32'
    auth_complete = '03'
    auth_complete_revoke = '33'
    get_balance = '71'


class ChannelType(object):

    Desktop = '07'
    Mobile = '08'


class UnionpayClient(object):

    version = "5.0.0"
    encoding = 'UTF-8'
    signMethod = "01"

    def __init__(self, config, timeout=30, verify=False, **kwargs):
        '''
        @config:    the unionpay config object
        @timeout:   request timeout seconds
        @verify:    should verify ssl certification pem
        '''
        self.config = config
        self.timeout = timeout
        self.verify = verify
        self.signer = Signer.getSigner(config)

    @staticmethod
    def get_txn_time():
        return datetime.datetime.now().strftime('%Y%m%d%H%M%S')

    @staticmethod
    def get_timeout(self, trade_time=None, expire_minutes=10):
        '''
        @trade_time:        trade time
        @expire_minutes:    order expire minutes
        '''
        cur_trade_time = trade_time or datetime.datetime.now()
        cur_trade_time += datetime.timedelta(minutes=expire_minutes)
        return cur_trade_time.strftime('%Y%m%d%H%M%S')

    def post(self, addr, data, **kwargs):
        if type(data['signature']) is bytes:
            data.update(signature=data['signature'].decode("utf-8"))
        #request_data = Signer.simple_urlencode(data)
        response = requests.post(addr, data=data, timeout=self.timeout, verify=self.verify)
        if response.status_code != requests.codes.ok:
            msg = "[UPACP]request error: %s, reason: %s" \
                % (response.status_code, response.reason)
            raise error.UnionpayError(msg)
        return response.content.decode("utf-8")

    def async_post(self, addr, data, **kwargs):
        pass

    def send_packet(self, addr, data, **kwargs):
        raw_content = self.post(addr, data)
        data = self.signer.parse_arguments(raw_content)
        if data['respCode'] != '00':
            msg = '[UPACP]respCode: %s orderid: %s' % (
                data['respCode'], data['orderId'])
            raise error.UnionpayError(msg)
        self.signer.validate(data)
        return data

    def pay(self, txnamt, order_id, currency_code='156', biz_type="000201", channel_type='07', front_url=None, **kwargs):
        '''
        @txnamt:            trade money amount
        @order_id:          trade order id
        @currency_code:     currency code: 156-RMB
        @biz_type:          idk
        @channel_type:      trade channel: 07-DESKTOP, 08-MOBILE
        @front_url:         browser jump url
        '''
        order_time = kwargs.get('order_time')
        expire_minutes = kwargs.get('expire_minutes')
        data = {
            'version': self.version,
            'encoding': self.encoding,
            'signMethod': self.signMethod,
            'txnType': TradeType.pay,
            'txnSubType': '01',
            'bizType': biz_type,
            'channelType': channel_type,
            'backUrl': self.config.backend_url_payment,
            'accessType': '0',
            'merId': self.config.merchant_id,
            'orderId': order_id,
            'txnTime': self.get_txn_time(),
            'txnAmt': txnamt,
            'currencyCode': currency_code,
            'payTimeout': self.get_timeout(order_time, expire_minutes),
            'customerIp': kwargs.get('customer_ip'),
            'orderDesc': kwargs.get('order_desc')
        }

        if channel_type == ChannelType.Desktop:
            if not front_url:
                raise error.UnionpayError(
                    'must set front_url when desktop')
            data.update(frontUrl=front_url)
            data = self.signer.filter_params(data)
            sign_result = self.signer.sign(data)
            return make_submit_form(data, self.config.front_trans_url)

        data = self.signer.filter_params(data)
        sign_result = self.signer.sign(data)
        if not sign_result:
            raise error.UnionpayError('Sign data error')
        return self.send_packet(self.config.app_trans_url, data)

    def query(self):
        pass

    def revoke(self):
        pass

    def refund(self, txnamt, orderId, origQryId, biz_type="000201", channel_type='07', **kwargs):
        '''
        @txnamt:            trade money amount
        @orderId:           trade id
        @origQryId:         original trade query id
        @biz_type:          idk
        @channel_type:      trade channel: 07-DESKTOP, 08-MOBILE
        @front_url:         browser jump url
        '''
        data = {
            'version': self.version,
            'encoding': self.encoding,
            'signMethod': self.signMethod,
            'txnType': TradeType.refund,
            'txnSubType': '00',
            'bizType': biz_type,
            'channelType': channel_type,
            'backUrl': self.config.backend_url_refund,
            'accessType': '0',
            'merId': self.config.merchant_id,
            'origQryId': origQryId,
            'orderId': orderId,
            'txnTime': self.get_txn_time(),
            'txnAmt': txnamt
        }

        data = self.signer.filter_params(data)
        sign_result = self.signer.sign(data)
        if not sign_result:
            raise error.UnionpayError('Sign data error')
        return self.send_packet(self.config.back_trans_url, data)

    def auth(self):
        pass

    def auth_revoke(self):
        pass

    def auth_complete(self):
        pass

    def auth_complete_revoke(self):
        pass

    def guarantee_pay(self):
        pass

    def file_transfer(self):
        pass
