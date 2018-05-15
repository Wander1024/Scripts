from dns import resolver

import requests, re, sys, logging, time

logger = logging.getLogger('')
logger.setLevel(logging.INFO)
fh = logging.FileHandler('./updateCerts.log')
fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(fh)

token = ''
name, _, value = sys.argv[1:]
rrhost = '_acme-challenge'

def tryResolve(rrs, rrt, flag=0):
    try:
        if flag == 0:
            result = resolver.query(rrs, rrt)
        else:
            MyResolver = resolver.Resolver()
            MyResolver.nameservers = ['173.254.242.221', '104.225.253.5']
            result = MyResolver.query(rrs, rrt)
        return {'txtvalue': result.rrset.to_text().split(' ')[-1].replace('"','')}
    except resolver.NXDOMAIN:
        return getRRid()

def getRRid():
    url = 'https://www.namesilo.com/api/dnsListRecords?version=1&type=xml&key={token}&domain={name}'.format(token=token, name=name)
    result = requests.post(url).content
    b = re.search('.*id>(.*?)</record_id><type>TXT.*?_acme-challenge.{domain}.*'.format(domain=name), str(result), re.S)
    if b:
        return {'rrid': b.group(1), 'txtvalue': 0}
    else:
        return
        

def addRR(rrs, rrt, value, token):
    url = 'https://www.namesilo.com/api/dnsAddRecord?version=1&type=xml&key={token}&domain={name}&rrtype={rrt}&rrhost={rrs}&rrvalue={value}&rrttl=7207'.format(name=name, token=token, rrt=rrt, rrs=rrs, value=value)
    print(url)
    try:
        result = requests.post(url)
        if re.search('success', str(result.content)):
            logger.info('add record successful')
        else:
            print(result.content)
            raise Exception('failed to add record')
    except Exception as e:
        logger.error("%s %s" % (addRR.__name__, e))
        exit(1)


def updateRR(rrs, rrt, rrid, value, token):
    url = 'https://www.namesilo.com/api/dnsUpdateRecord?version=1&type=xml&key={token}&domain={domain}&rrid={rrid}&rrhost={rrs}&rrvalue={value}&rrttl=7207'.format(value=value, token=token, rrid=rrid, rrs=rrhost, domain=name)
    try:
        result = requests.post(url)
        print(str(result.content))
        print(url)
        if re.search('success', str(result.content)):
            logger.info('update record successful')
        else:
            raise Exception('failed to update record')
    except Exception as e:
        logger.error("%s %s" % (updateRR.__name__, e))
        exit(1)


def _main():
    url = 'https://www.namesilo.com/api/dnsListRecords?version=1&type=xml&key={token}&domain={name}'.format(token=token, name=name)
    result = tryResolve('_acme-challenge.{domain}'.format(domain=name), 'txt', flag=1)
    if result: 
        print('update')
        rrid = result['rrid'] if 'rrid' in result.keys() else getRRid()['rrid']
        print(rrid)
        updateRR(rrhost, 'TXT', rrid, value, token)
            
    else:
        print('add')
        addRR(rrhost, 'TXT', value, token)

    while True:
        if tryResolve('_acme-challenge.{domain}'.format(domain=name), 'txt')['txtvalue'] == value:
            break
        else:
            time.sleep(100)

if __name__ == '__main__':
    _main()

