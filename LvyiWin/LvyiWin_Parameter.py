# -*- coding: utf-8 -*-
'''
策略参数设置
'''
#参数设置
strategyName='LvyiWin'
exchange_id = 'SHFE'
sec_id='RB'
K_MIN = 600
startdate='2016-01-01'
enddate = '2018-03-31'
parasetname = 'ParameterOptSet1.csv'

#=============止损控制开关===================
calcDsl_close=True
calcOwnl_close=False
calcDslOwnl_close=False
#dsl参数
dslStep_close=-0.002
dslTargetStart_close=-0.022
dslTargetEnd_close = -0.024
#ownl参数
ownlStep_close=0.001
ownlTargetStart_close = 0.009
ownltargetEnd_close = 0.010
nolossThreshhold_close = 3
#=============推进控制开关===================
nextMonthName='Apr-18'
forwardWinStart=1
forwardWinEnd=12

#止损类型开关
common_forward=False #普通回测结果推进
calcDsl_forward=False
calcOwnl_forward=False
calcDslOwnl_forward=False
#dsl参数
dslStep_forward=-0.002
dslTargetStart_forward=-0.010
dslTargetEnd_forward = -0.042
#ownl参数
ownlStep_forward=0.001
ownlTargetStart_forward = 0.005
ownltargetEnd_forward = 0.010
#dsl_ownl set:dsl在前，ownl在后
dsl_ownl_set=[[-0.022,0.009]]

#===============多品种多周期优化参数=============================
#多品种多周期优化开关，打开后代码会从下面标识的文件中导入参数
symbol_KMIN_opt_swtich=False

#1.品种和周期组合文件
symbol_KMIN_set_filename=strategyName+'_symbol_KMIN_set.xlsx'
#2.第一步的结果中挑出满足要求的项，做成双止损组合文件
stoploss_set_filename=strategyName+'_stoploss_set.xlsx'
#4.从第二、第三步的结果中挑出满足要求的项，做推进
forward_set_filename=strategyName+'_forward_set.xlsx'

#====================系统参数==================================
folderLevel = 2
resultFolderName = '\\Results\\'