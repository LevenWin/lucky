# -*- coding: utf-8 -*-
# Author: leven

import scrapy
from scrapy_redis.spiders import RedisSpider

import json
import xml.etree.ElementTree as ET
from lucky import xml2json
from lucky.items import LuckyItem
from scrapy.http import Request
from urllib import parse

class shishicai1Spider(scrapy.Spider):
    name = "shishicai1"
    allowed_domain = ['http://apicloud.mob.com']
    totalRecords = []
    allRecords = []

    totalMoney = 12000
    maxLose = 4000
    maxBetMoney = 2000
    minBetMoney = 88
    minBetCount = 400
    skip = 0

    betsRecord = {} # 下注记录
    winRecord = [] #赢局记录
    failedRecord = [] #输局记录
    moneyRecord = []  # 剩余金钱记录


    spiderCount = 20
    start_urls = ['http://api.caipiao.163.com/queryAwardByCond.html?count=20&gameEn=ssc&period=180831025']

    def parse(self, response):
        msgs = self.xml_to_dic(response.text)
        self.spiderCount-=1
        if len(msgs) > 0:
            self.allRecords = self.allRecords + msgs
            lastId = msgs[-1]['periodName']
            if self.spiderCount > 0:
                yield Request(url = ('http://api.caipiao.163.com/queryAwardByCond.html?count=20&gameEn=ssc&period=' + lastId), callback=self.parse)
            else:
                self.normalBet()
        else:
            self.normalBet()


    # def sliceBet(self):
    #     self.logToFile('          记录\n',True)
    #     for i in range(0, len(self.allRecords)):
    #
    #         if i == len(self.allRecords) - 1:
    #             self.logToFile('  \n\n\n ****** 最后一天:%d ****** \n' % (len(self.allRecords) / 30 + 1))
    #             self.luckyDog()
    #         else:
    #             if i%30 == 0 and i > 0:
    #                 self.logToFile('   \n\n\n****** 第%d天 ****** \n' % (i / 30 ))
    #                 self.luckyDog()
    #             else:
    #                 self.totalRecords.append(self.allRecords[i])

    def normalBet(self):
        self.totalRecords = self.allRecords
        self.luckyDog()

    def luckyDog(self):
        # self.winRecord = []
        # self.skip = 0
        # self.betsRecord = {}  # 下注记录
        # self.winRecord = []  # 赢局记录
        # self.failedRecord = []  # 输局记录
        # self.moneyRecord = []  # 剩余金钱记录
        self.logToFile('          记录\n', True)
        self.totalRecords = self.totalRecords[::-1]
        count = 0
        winSkip = 0
        for item in self.totalRecords:
            if winSkip > 0:
                winSkip-=1
                continue
            if count > 1000000:
                break
            version = int(item['periodName'])
            self.logToFile('*******************************\n')
            self.logToFile('第'+ item['periodName']+'期开奖号码：'+ item['awardNo'])
            num1 = int(item['awardNo'][0])
            attr1 = '大' if(self.isBig(num1)) else '小'
            attr2 = '偶' if (self.isEvent(num1)) else '奇'
            self.logToFile ('第一位：'+ str(num1) + ' '+ attr1 +' ' + attr2)
            count = count + 1
            #开奖！
            self.openBet(num1,0, version)

            if self.totalMoney < 0:
                self.logToFile ('你输光啦!!!')
                break
            elif self.totalMoney >= 12000 * 2:
                winSkip = 3
                self.minBetMoney = 100
            else:
                # 再下注！
                bets = self.betPolicy1(num1, 0, version)
                if len(bets) >0:
                    self.logToFile ('下注: ')
                    for bet in bets:
                        self.luckyBet(bet['money'], bet['type'], 0, version)
                else:
                    self.logToFile ('本期不下注')
        self.pretyOutResult()
    def betPolicy1(self, num = 0 , index = 0, version = 000):
        lastVersionNum = version
        lastBetInfo = self.betInfor(index,lastVersionNum)
        bets = []
        if self.skip > 0:
            self.skip -= 1
            return []
        if len(lastBetInfo) > 0:
            for bet in lastBetInfo:
                if self.checkBet(index, bet['type'], lastVersionNum):
                    betMoney = self.minBetMoney
                    if int(bet['money']) > 800:
                        betMoney = int(self.minBetMoney * 0.5)
                    bets.append({'money':str(betMoney),'type':bet['type']})
                    self.minBetMoney = 100
                    # self.logToFile('111')
                else:
                    backCount = -3
                    betMoney = int(bet['money']) * 2 if int(bet['money']) * 2 < self.maxBetMoney else self.maxBetMoney
                    if self.isWinOrLose(False, index, version, bet['type'], backCount, True) :
                        self.skip = 3
                        self.minBetMoney = 400
                        return []
                        # if self.isWinOrLose(False, index, version, bet['type'], backCount -1, True):
                        #     self.logToFile('已经连输 4 局啦，初始化')
                        #     bets.append({'money': str(self.minBetMoney), 'type': self.reverseBetType(bet['type'])})
                        #     self.logToFile('222')
                        # else :
                        #     self.logToFile('已经连输 3 局啦，换个策略！')
                        #     bets.append({'money': str(betMoney), 'type': bet['type']})
                    else:
                        bets.append({'money': str(betMoney), 'type': self.reverseBetType(bet['type'])})
                        self.logToFile('333')
        else:
            if self.isItemOdd(index, lastVersionNum):
                bets.append({'money': str(self.minBetMoney), 'type':'奇'})
                # self.logToFile('444')
            else:
                bets.append({'money': str(self.minBetMoney), 'type': '偶'})
                # self.logToFile('555')
            if self.isItemBig(index, lastVersionNum):
                bets.append({'money': str(self.minBetMoney), 'type':'大'})
                # self.logToFile('666')
            else:
                bets.append({'money': str(self.minBetMoney), 'type': '小'})
                # self.logToFile('777')
        return bets


    def betPolicy2(self, num=0, index=0, version=000):
        lastVersionNum = version
        lastBetInfo = self.betInfor(index, lastVersionNum)
        bets = []
        if len(lastBetInfo) > 0:
            for bet in lastBetInfo:
                if self.checkBet(index, bet['type'], lastVersionNum):

                    if self.isItemBig(index, lastVersionNum) == True and self.isItemBig(index, lastVersionNum,
                                                                                        -1) == True and self.isItemBig(
                            index, lastVersionNum, -2) == True:
                        bets.append({'money': str(self.minBetMoney), 'type': '小'})
                        # self.logToFile ('11a')
                    if self.isItemBig(index, lastVersionNum) == False and self.isItemBig(index, lastVersionNum,
                                                                                         -1) == False and self.isItemBig(
                            index, lastVersionNum, -2) == False:
                        bets.append({'money': str(self.minBetMoney), 'type': '大'})
                        # self.logToFile ('11b')
                    if self.isItemOdd(index, lastVersionNum) == False and self.isItemOdd(index, lastVersionNum,
                                                                                         -1) == False and self.isItemOdd(
                            index, lastVersionNum, -2) == False:
                        bets.append({'money': str(self.minBetMoney), 'type': '奇'})
                        # self.logToFile ('11c')
                    if self.isItemOdd(index, lastVersionNum) == True and self.isItemOdd(index, lastVersionNum,
                                                                                        -1) == True and self.isItemOdd(
                            index, lastVersionNum, -2) == True:
                        bets.append({'money': str(self.minBetMoney), 'type': '偶'})
                        # self.logToFile ('11d')
                else:
                    # self.logToFile ('00')
                    bets.append({'money': str(int(bet['money']) * 2), 'type': bet['type']})

        else:
            if self.isItemBig(index, lastVersionNum) == True:
                bets.append({'money': str(self.minBetMoney), 'type': '小'})
                # self.logToFile ('22a')
            if self.isItemBig(index, lastVersionNum) == False and self.isItemBig(index, lastVersionNum,
                                                                                 -1) == False and self.isItemBig(index,
                                                                                                                 lastVersionNum,
                                                                                                                 -2) == False:
                bets.append({'money': str(self.minBetMoney), 'type': '大'})
                # self.logToFile ('22b')
            if self.isItemOdd(index, lastVersionNum) == False and self.isItemOdd(index, lastVersionNum,
                                                                                 -1) == False and self.isItemOdd(index,
                                                                                                                 lastVersionNum,
                                                                                                                 -2) == False:
                bets.append({'money': str(self.minBetMoney), 'type': '奇'})
                # self.logToFile ('22c')
            if self.isItemOdd(index, lastVersionNum) == True and self.isItemOdd(index, lastVersionNum,
                                                                                -1) == True and self.isItemOdd(index,
                                                                                                               lastVersionNum,
                                                                                                               -2) == True:
                bets.append({'money': str(self.minBetMoney), 'type': '偶'})
                # self.logToFile ('22d')
        return bets


    def isItemBig(self, index = 0 , version = 000, sub = 0, all = False):
        versions = []
        if all:
            for i in range(version, version + sub):
                versions.append(i)
        else:
            versions.append(version)
        isSuccess = True
        for realVersion in  versions:
            for item in self.totalRecords:
                tempversion = int(item['periodName'])
                if tempversion == realVersion:
                    num1 = int(item['awardNo'][index * 2])
                    if self.isBig(num1):
                        continue
                    else:
                        return False
        return True
    def isItemOdd(self, index = 0 , version = 000, sub = 0, all = False):
        versions = []
        if all:
            for i in range(version, version + sub):
                versions.append(i)
        else:
            versions.append(version+sub)
        for realVersion in versions:
            for item in self.totalRecords:
                tempversion = int(item['periodName'])
                if tempversion == realVersion:
                    num1 = int(item['awardNo'][index * 2])
                    if self.isOdd(num1):
                        continue
                    else:
                        return False

        return True



    def betInfor(self, index = 0, version = 000):
        versionBet = self.betsRecord[str(version)] if str(version) in self.betsRecord else {}
        versionBet = versionBet if isinstance(versionBet, dict) else {}
        indexBet = versionBet[str(index)] if str(index) in versionBet else []
        indexBet = indexBet if isinstance(indexBet, list) else []
        return indexBet

    def checkBet(self, index, type, version ,sub = 0, all = False):
        versions = []
        if all:
            for i in range(version, version + sub):
                versions.append(i)
        else:
            versions.append(version+sub)
        for realVersion in versions:
            for item in self.totalRecords:
                if item['periodName'] == str(realVersion):
                    num1 = int(item['awardNo'][0 + index*2])
                    attr1 = '大' if (self.isBig(num1)) else '小'
                    attr2 = '偶' if (self.isEvent(num1)) else '奇'
                    if type == attr1 or type == attr2:
                        continue
                    else:
                        return False
        return True
    def luckyBet(self, money = 0, type = '大', index = 0, version = 000):
        version = int(version) + 1
        money = int(money)
        if money >= self.totalMoney:
            money = self.totalMoney
        self.totalMoney -= money
        self.logToFile('    第 %s 期，第%s位数，压%s %s 块钱, 剩余%d' % (str(version), str(index+1), type, str(money),self.totalMoney))
        bet = {'money':str(money),'type':type, 'index':str(index), 'version':str(version)}
        versionBet = self.betsRecord[str(version)] if str(version) in self.betsRecord else {}
        indexBet = versionBet[str(index)] if str(index) in versionBet else []
        indexBet.append(bet)
        versionBet[str(index)] = indexBet
        self.betsRecord[str(version)] = versionBet

    def openBet(self, num = -1, index = -1, version = -1):
        attr1 = '大' if (self.isBig(num)) else '小'
        attr2 = '偶' if (self.isEvent(num)) else '奇'
        error = False
        self.logToFile ('开奖: 😊')
        if str(version) in self.betsRecord:
            versionBet = self.betsRecord[str(version)]
            if isinstance(versionBet, dict):
                indexBet =  versionBet[str(index)] if str(index) in versionBet else []
                if isinstance(indexBet, list):
                    for bet in indexBet:
                        if bet['type'] == attr1 or bet['type'] == attr2:
                            # 你赢钱了
                            self.totalMoney += int(bet['money'])*2*0.95
                            self.addWinBet(bet, index, num, version)
                        else:
                            # 你输钱了
                            self.addFailedBet(bet, index, num, version)
                        self.moneyRecord.append(self.totalMoney)
                else:
                    error = True
        else :
           error = True
        self.logToFile ('    第' + str(version) + '期没有投注！') if error else ''

    def addWinBet(self, bet, numIndex, openNum, version):
        bet['betIndex'] = numIndex
        bet['openNum'] = openNum
        bet['version'] =version
        self.logToFile ('    下注第'+str(numIndex+1)+'位数开:'+bet['type']+',  赢了'+bet['money'] + ' 还剩:'+str(self.totalMoney))
        self.winRecord.append(bet)


    def addFailedBet(self, bet, numIndex, openNum, version):
        bet['betIndex'] = numIndex
        bet['openNum'] = openNum
        bet['version'] =version
        self.logToFile ('    下注第'+str(numIndex+1)+'位数开:'+bet['type']+',  输了'+bet['money'] +  ' 还剩:'+ str(self.totalMoney))
        self.failedRecord.append(bet)
    def reverseBetType(self, type):
        if type == '奇':
            return '偶'
        if type == '偶':
            return '奇'
        if type == '大':
            return '小'
        if type == '小':
            return '大'

    def isWinOrLose(self, winOrLose = True, index = 0,  version = 000, type = '偶', sub = 0, all = False):
        versions = []
        bets = self.winRecord if winOrLose else self.failedRecord
        if all:
            for i in range(version+sub + 1, version):
                versions.append(i)
        else:
            versions.append(version+sub)
        if len(versions) == 0:
            return False
        for tempVersion in versions:
            find = False
            versionExit = False
            for bet in bets:
                if str(bet['version']) == str(tempVersion):
                    versionExit = True
                    if bet['index'] == str(index) and (bet['type'] == type or self.reverseBetType(bet['type']) == type) :
                        find = True
                        break

            if versionExit and not find :
                # self.logToFile('11 versions: %s, index:%s,  record: %s' %(str(versions), str(index), str(bets)))
                return False
            if not versionExit:
                # self.logToFile('22 versions: %s, index:%s, record: %s' %(str(versions), str(index), str(bets)))
                return False

        # self.logToFile('33 versions: %s, index:%s, record: %s' % (str(versions), str(index), str(bets)))
        return True


    def pretyOutResult(self):
        self.logToFile('''你共下了%d局,  赢%d局，输%d局，
        单局最多赢%d块钱,单局最多输%d块钱。
        剩余金额最大为%d块钱，最少为%d块钱，最后剩余%d块钱
        ''' % (len(self.failedRecord) + len(self.winRecord), len(self.winRecord), len(self.failedRecord),
                        self.maxSingleWin(), self.maxSingleLose(),
                        self.maxLeftMoney(), self.minLeftMoney(), self.totalMoney))
    def maxSingleWin(self):
        maxwin = 0
        for bet in self.winRecord:
            if maxwin < int(bet['money']):
                maxwin = int(bet['money'])
        return maxwin
    def maxSingleLose(self):
        maxLose = 0
        for bet in self.failedRecord:
            if maxLose < int(bet['money']):
                maxLose = int(bet['money'])
        return maxLose
    def maxLeftMoney(self):
        money = 0
        for m in self.moneyRecord:
            if money < m:
                money = m
        return money
    def minLeftMoney(self):
        money = - 1
        for m in self.moneyRecord:
            if money == -1 and m > 0:
                money = m
            if money > m:
                money = m
        return money

    def isEvent(self, num):
        return num%2 == 0
    def isOdd(self, num):
        return num%2 == 1
    def isBig(self, num):
        return num > 4
    def isSmall(self, num):
        return num < 5

           # def __getattribute__(self, item):
        #     if item == 'minBetMoney':
        #         return self.minBetMoney
        #         minBet = int(self.totalMoney / 240)
        #         if minBet > self.maxBetMoney:
        #             return self.maxBetMoney
        #         else:
        #             return minBet
        #     else:
        #         return super(shishicai1Spider, self).__getattribute__(item)

    def xml_to_dic(self, xml_str):
        msgs = []
        root_elem = ET.fromstring(xml_str)
        if root_elem.tag == 'lottery':
            for ch in root_elem:
               for preiod in ch:
                   if preiod:
                       msg = {}
                       for ele in preiod:
                           msg[ele.tag] = ele.text
                       msgs.append(msg)
        return msgs
    def logToFile(self,log, cover = False):
        if not cover:
            with open('log.text', 'a+') as f:
                f.write('\n')
                f.write(log)
        else:
            with open('log.text', 'w+') as f:
                f.write('\n')
                f.write(log)

    def get_FileSize(filePath):
        filePath = unicode(filePath, 'utf8')
        fsize = os.path.getsize(filePath)
        fsize = fsize
        return round(fsize, 2)









