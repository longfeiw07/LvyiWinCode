# -*- coding: utf-8 -*-
'''
有赚就不亏止损策略
按tick级别判断，盈利超过千3后，回撤达到3个pricetick的保护价就平仓
tick模拟：1min的high和low模拟1min内tick的最高和最低价
'''
import pandas as pd
import DATA_CONSTANTS as DC
import numpy as np
import os
import ResultStatistics as RS
import multiprocessing

def getLongNoLossByTick(bardf,openprice,winSwitch,nolossThreshhold):
    '''
    1.计算截至当前的最大盈利：maxEarnRate:expanding().max()/openprice
    2.取maxEarnRate大于winSwitch的数据，如果数据量大于0，表示触发了保护门限
    3.超过保护的数据中，取第1个价格小于或等于openprice+nolossThreshhold的，即为触发平仓时机
    4.返回平仓的参数：new_closeprice=openprice+nolossThreshhold,new_closeutc,new_closeindex,new_closetime
    '''
    df = pd.DataFrame({'high': bardf['longHigh'],'low':bardf['longLow'], 'strtime': bardf['strtime'], 'utc_time': bardf['utc_time'],
                       'timeindex': bardf['Unnamed: 0']})
    df['max2here']=df['high'].expanding().max()
    df['maxEarnRate']=df['max2here']/openprice-1
    df2=df.loc[df['maxEarnRate']>winSwitch]
    if df2.shape[0]>0:
        tempdf=df2.loc[df2['low']<=(openprice+nolossThreshhold)]
        if tempdf.shape[0]>0:
            temp=tempdf.iloc[0]
            newcloseprice = openprice+nolossThreshhold
            strtime = temp['strtime']
            utctime = temp['utc_time']
            timeindex = temp['timeindex']
            return newcloseprice,strtime,utctime,timeindex
    return 0,' ',0,0


def getShortNoLossByTick(bardf,openprice,winSwitch,nolossThreshhold):
    '''
    1.计算截至当前的最大盈利：maxEarnRate:expanding().max()/openprice
    2.取maxEarnRate大于winSwitch的数据，如果数据量大于0，表示触发了保护门限
    3.超过保护的数据中，取第1个价格小于或等于openprice+nolossThreshhold的，即为触发平仓时机
    4.返回平仓的参数：new_closeprice=openprice+nolossThreshhold,new_closeutc,new_closeindex,new_closetime
    '''
    df = pd.DataFrame({'high': bardf['shortHigh'],'low':bardf['shortLow'], 'strtime': bardf['strtime'], 'utc_time': bardf['utc_time'],
                       'timeindex': bardf['Unnamed: 0']})
    df['min2here']=df['low'].expanding().min()
    df['maxEarnRate']=1-df['min2here']/openprice
    df2=df.loc[df['maxEarnRate']>winSwitch]
    if df2.shape[0]>0:
        tempdf=df2.loc[df2['high']>=(openprice-nolossThreshhold)]
        if tempdf.shape[0]>0:
            temp=tempdf.iloc[0]
            newcloseprice = openprice-nolossThreshhold
            strtime = temp['strtime']
            utctime = temp['utc_time']
            timeindex = temp['timeindex']
            return newcloseprice,strtime,utctime,timeindex
    return 0,' ',0,0

def ownlCal(symbol,K_MIN,setname,bar1m,barxm,winSwitch,nolossThreshhold,slip,tofolder):
    print 'ownl;', str(winSwitch), ',setname:', setname
    oprdf = pd.read_csv(symbol + str(K_MIN) + ' ' + setname + ' result.csv')
    oprdf['new_closeprice'] = oprdf['closeprice']
    oprdf['new_closetime'] = oprdf['closetime']
    oprdf['new_closeindex'] = oprdf['closeindex']
    oprdf['new_closeutc'] = oprdf['closeutc']
    oprnum = oprdf.shape[0]
    worknum=0
    for i in range(oprnum):
        opr = oprdf.iloc[i]
        startutc = (barxm.loc[barxm['utc_time'] == opr.openutc]).iloc[0].utc_endtime - 60#从开仓的10m线结束后开始
        endutc = (barxm.loc[barxm['utc_time'] == opr.closeutc]).iloc[0].utc_endtime#一直到平仓的10m线结束
        oprtype = opr.tradetype
        openprice = opr.openprice
        data1m = bar1m.loc[(bar1m['utc_time'] > startutc) & (bar1m['utc_time'] < endutc)]
        if oprtype == 1:
            newcloseprice, strtime, utctime, timeindex = getLongNoLossByTick(data1m,openprice,winSwitch,nolossThreshhold)
            if newcloseprice !=0:
                oprdf.ix[i, 'new_closeprice'] = newcloseprice
                oprdf.ix[i, 'new_closetime'] = strtime
                oprdf.ix[i, 'new_closeindex'] = timeindex
                oprdf.ix[i, 'new_closeutc'] = utctime
                worknum+=1

        else:
            newcloseprice, strtime, utctime, timeindex = getShortNoLossByTick(data1m, openprice, winSwitch,nolossThreshhold)
            if newcloseprice != 0:
                oprdf.ix[i, 'new_closeprice'] = newcloseprice
                oprdf.ix[i, 'new_closetime'] = strtime
                oprdf.ix[i, 'new_closeindex'] = timeindex
                oprdf.ix[i, 'new_closeutc'] = utctime
                worknum+=1

    initial_cash = 20000
    margin_rate = 0.2
    commission_ratio = 0.00012
    firsttradecash = initial_cash / margin_rate
    # 2017-12-08:加入滑点
    oprdf['new_ret'] = ((oprdf['new_closeprice'] - oprdf['openprice']) * oprdf['tradetype']) - slip
    oprdf['new_ret_r'] = oprdf['new_ret'] / oprdf['openprice']
    oprdf['new_commission_fee'] = firsttradecash * commission_ratio * 2
    oprdf['new_per earn'] = 0  # 单笔盈亏
    oprdf['new_own cash'] = 0  # 自有资金线
    oprdf['new_trade money'] = 0  # 杠杆后的可交易资金线
    oprdf['new_retrace rate'] = 0  # 回撤率

    oprdf.ix[0, 'new_per earn'] = firsttradecash * oprdf.ix[0, 'new_ret_r']
    maxcash = initial_cash + oprdf.ix[0, 'new_per earn'] - oprdf.ix[0, 'new_commission_fee']
    oprdf.ix[0, 'new_own cash'] = maxcash
    oprdf.ix[0, 'new_trade money'] = oprdf.ix[0, 'new_own cash'] / margin_rate
    oprtimes = oprdf.shape[0]
    for i in np.arange(1, oprtimes):
        commission = oprdf.ix[i - 1, 'new_trade money'] * commission_ratio * 2
        perearn = oprdf.ix[i - 1, 'new_trade money'] * oprdf.ix[i, 'new_ret_r']
        owncash = oprdf.ix[i - 1, 'new_own cash'] + perearn - commission
        maxcash = max(maxcash, owncash)
        retrace_rate = (maxcash - owncash) / maxcash
        oprdf.ix[i, 'new_own cash'] = owncash
        oprdf.ix[i, 'new_commission_fee'] = commission
        oprdf.ix[i, 'new_per earn'] = perearn
        oprdf.ix[i, 'new_trade money'] = owncash / margin_rate
        oprdf.ix[i, 'new_retrace rate'] = retrace_rate
    #保存新的result文档
    oprdf.to_csv(tofolder+symbol + str(K_MIN) + ' ' + setname + ' resultOWNL_by_tick.csv')

    #计算统计结果
    oldendcash = oprdf.ix[oprnum - 1, 'own cash']
    oldAnnual = RS.annual_return(oprdf)
    oldSharpe = RS.sharpe_ratio(oprdf)
    oldDrawBack = RS.max_drawback(oprdf)[0]
    oldSR = RS.success_rate(oprdf)
    newendcash = oprdf.ix[oprnum - 1, 'new_own cash']
    newAnnual = RS.annual_return(oprdf,cash_col='new_own cash',closeutc_col='new_closeutc')
    newSharpe = RS.sharpe_ratio(oprdf,cash_col='new_own cash',closeutc_col='new_closeutc',retr_col='new_ret_r')
    newDrawBack = RS.max_drawback(oprdf,cash_col='new_own cash')[0]
    newSR = RS.success_rate(oprdf,ret_col='new_ret')
    max_single_loss_rate = abs(oprdf['new_ret_r'].min())
    max_retrace_rate = oprdf['new_retrace rate'].max()

    return [setname,winSwitch,worknum,oldendcash,oldAnnual,oldSharpe,oldDrawBack,oldSR,newendcash,newAnnual,newSharpe,newDrawBack,newSR,max_single_loss_rate,max_retrace_rate]


if __name__ == '__main__':
    #参数配置
    exchange_id = 'DCE'
    sec_id='I'
    symbol = '.'.join([exchange_id, sec_id])
    K_MIN = 600
    topN=50
    pricetick=DC.getPriceTick(symbol)
    slip=pricetick
    starttime='2016-01-01 00:00:00'
    endtime='2018-01-01 00:00:00'
    #优化参数
    stoplossStep=0.001
    winSwitchList = np.arange(0.003, 0.011, stoplossStep)
    nolossThreshhold=3*pricetick

    #文件路径
    upperpath=DC.getUpperPath(uppernume=2)
    resultpath=upperpath+"\\Results\\"
    foldername = ' '.join([exchange_id, sec_id, str(K_MIN)])
    oprresultpath=resultpath+foldername

    # 读取finalresult文件并排序，取前topN个
    finalresult=pd.read_csv(oprresultpath+"\\"+symbol+str(K_MIN)+" finanlresults.csv")
    finalresult=finalresult.sort_values(by='end_cash',ascending=False)
    totalnum=finalresult.shape[0]

    #原始数据处理
    bar1m=DC.getBarData(symbol=symbol,K_MIN=60,starttime=starttime,endtime=endtime)
    barxm=DC.getBarData(symbol=symbol,K_MIN=K_MIN,starttime=starttime,endtime=endtime)
    #bar1m计算longHigh,longLow,shortHigh,shortLow
    bar1m['longHigh']=bar1m['high']
    bar1m['shortHigh']=bar1m['high']
    bar1m['longLow']=bar1m['low']
    bar1m['shortLow']=bar1m['low']
    bar1m['highshift1']=bar1m['high'].shift(1).fillna(0)
    bar1m['lowshift1']=bar1m['low'].shift(1).fillna(0)
    bar1m.loc[bar1m['open']<bar1m['close'],'longHigh']=bar1m['highshift1']
    bar1m.loc[bar1m['open']>bar1m['close'],'shortLow']=bar1m['lowshift1']

    os.chdir(oprresultpath)
    allresultdf = pd.DataFrame(columns=['setname', 'winSwitch','worknum', 'old_endcash', 'old_Annual', 'old_Sharpe', 'old_Drawback',
                                     'old_SR',
                                     'new_endcash', 'new_Annual', 'new_Sharpe', 'new_Drawback', 'new_SR',
                                     'maxSingleLoss', 'maxSingleDrawBack'])
    allnum=0
    for winSwitch in winSwitchList:
        resultList = []
        ownlFolderName="OnceWinNoLoss" + str(winSwitch*1000)
        try:
            os.mkdir(ownlFolderName)#创建文件夹
        except:
            print "dir already exist!"
        print ("OnceWinNoLoss WinSwitch:%f"%winSwitch)

        pool = multiprocessing.Pool(multiprocessing.cpu_count())
        l = []

        for sn in range(0,topN):
            opr = finalresult.iloc[sn]
            setname = opr['Setname']
            l.append(pool.apply_async(ownlCal,
                                      (symbol,K_MIN,setname,bar1m,barxm,winSwitch,nolossThreshhold,slip,ownlFolderName + '\\')))
        pool.close()
        pool.join()

        resultdf=pd.DataFrame(columns=['setname','winSwitch','worknum','old_endcash','old_Annual','old_Sharpe','old_Drawback','old_SR',
                                                  'new_endcash','new_Annual','new_Sharpe','new_Drawback','new_SR','maxSingleLoss','maxSingleDrawBack'])
        i = 0
        for res in l:
            resultdf.loc[i]=res.get()
            allresultdf.loc[allnum]=resultdf.loc[i]
            i+=1
            allnum+=1
        resultdf['cashDelta']=resultdf['new_endcash']-resultdf['old_endcash']
        resultdf.to_csv(ownlFolderName+'\\'+symbol+str(K_MIN)+' finalresult_by_tick'+str(winSwitch)+'.csv')

    allresultdf['cashDelta'] = allresultdf['new_endcash'] - allresultdf['old_endcash']
    allresultdf.to_csv(symbol + str(K_MIN) + ' finalresult_ownl_by_tick.csv')