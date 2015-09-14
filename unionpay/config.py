# -*- coding: utf-8

''' 关于银联支付的若干配置 '''

# 基本信息
version = '1.0.0'
charset = 'UTF-8'

# 请求url
trade_url = 'https://101.231.204.80:5000/gateway/api/frontTransReq.do'
query_url = 'https://101.231.204.80:5000/gateway/api/cardTransReq.do'

# 商户信息

# 商户ID
mer_id = '777290058118399'
# 回调地址
mer_backend_url = 'https://www.tripalocal.com/unionpay_callback/'

# 签名相关
pfx_filepath = 'pem/700000000000001_acp.p12'
password = '000000'
x509_filepath = 'pem/verify_sign_acp.cer'
# digest method
digest_method = 'sha1'

sign_method = 'MD5'

field_signature = 'signature'
field_sign_method = 'signMethod'
