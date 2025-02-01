import pandas as pd
from collections import OrderedDict
from datetime import datetime

from .entity import _CONTENTS, _STRUCTUER

import pandas as pd
import os
import sys
sys.path.insert( 0, os.path.dirname(__file__))
from cpl_kg import Court_determination_attributes

#################################################读取工具###############################################################
# 处理日期数据
def datetime_processor( data ):
    if isinstance(data, datetime):
        return data.strftime('%Y-%m-%d')
    else:
        return str(data)  # .dt


# 处理不同取值

def filter_value( value, field_name=None ):
    if pd.isna( value ):
        return "nan"
    if value == "1&2" and field_name!=None:
        ranges = Court_determination_attributes[field_name]
        value = ranges[0] + "&" + ranges[1]
    if "=" in value:
        value = value.split("=")[1]
        
    
    rm_de = [";", "；", "。"]
    for kkk in rm_de:
        if kkk in value:
            value = value.replace( kkk, "")
    return value


def _slot_reader( field, value ):
    ret=None
    if "日期" in field or "时间" in field or "表示日" in field or "哪一日" in field:
        ret = datetime_processor( value )
    else:
        ret = str(value)
    return ret

# 以不同主体的原文、取值入手
def _2read( row, table, entity_list, details ):
    ret = {}
    for entity in entity_list:
        col = details[entity][1]
        ret[entity] =  {
            _CONTENTS[0]: _slot_reader( table.iloc[row, 1], table.iloc[row, col]),
            _CONTENTS[1]: filter_value( _slot_reader( table.iloc[row, 1], table.iloc[row, col+1]), )
        }
    return ret

# 读取可迭代的动作/关系数据
def  _read_iterable( i, table, field, entity_list, details, profiles  ):
    '''
    param: i: 当前行号
    param: table: 全表
    param: lens: 可迭代对象长度
    param: field: 可迭代对象在常数字典中的名字（取自真实字段一部分）
    param: sub_fields: 可迭代对象的子字段列表

    return: ret, max(ind-i, 3*lens)
    '''
    ret = {}
    index = 1       # 可迭代对象的次数
    ind = i       # 可迭代对象总体平移
    sub_fields = list(profiles.keys())    # 当前迭代对象的子字段
    while True:
        spansss = 0                     # 当前可迭代对象内部平移
        topic = table.iloc[ind,1]       # 当前迭代次数的起点，检查起点是否还属于该迭代对象
        if field in topic:
            temp = {}                 # 子字段值字典
            for j in range(len(sub_fields)):               # 用于遍历当前目标对象内部的字段，由于存在可迭代对象，所以可能得_spans
                sub_field = sub_fields[j]    # 内部目标字段
                if profiles[sub_field]!=None and "数字" in profiles[sub_field]:   # 如果这个内部字段是可迭代的
                    temp[sub_field], spans = _read_iterable( ind+spansss, table, sub_field, entity_list, details, profiles[sub_field]["数字"]  )
                    spansss += spans
                else:                             # 如果这个内部字段不是可迭代的
                    temp[sub_field] = _2read( ind+spansss, table, entity_list, details )   # 读取该行
                    spansss += 1
            # 当前迭代轮次结算
            ind += spansss
            ret[index] = temp
            index += 1
        else:
            break
    return ret, ind-i

# 读取类数据
def  _read_class( i, table, lens,  sub_fields, entity_list, details ):
    '''
    param: i: 当前行号
    param: col: 当前entity对应的原文列号
    param: table: 全表
    param: lens: 类对象长度
    param: field: 类对象在常数字典中的名字（取自真实字段一部分）
    param: sub_fields: 可迭代对象的子字段

    return: ret
    '''
    ret = {}
    for j in range(i, i+lens):         # 遍历一个对象范围，填充temp字典  
        sub_field = sub_fields[j-i]
        ret[sub_field] = _2read( j, table, entity_list, details )   # 读取该行
    return ret

# 支持三部分读取的通用部分                 
def block_reader(start_row, end_row, entity_list, details, profiles, table):
    ret = {}
    iterables = [ ]
    classes = []
    for key in profiles.keys():      # 按顺序获取该block中所有可迭代对象
        if profiles[key] !=None:
            if "数字" in profiles[key]:
                iterables.append( key )
            else:
                classes.append( key )
    index_iter  = 0
    index_class = 0
    i = start_row
    while i<end_row:
        field = table.iloc[i,1]      # 实际字段名
        if pd.isnull(field):
            break
        iter_name = "<TEMP>" if index_iter == len(iterables) else iterables[index_iter]
        class_name = "<TEMP>" if index_class == len(classes) else classes[index_class]
        # 非可迭代字段，直接获取值
        if field in profiles:        # 字段名就是表格字段，说明不是类对象也不是可迭代
            ret[field] = _2read(i, table, entity_list, details)
            # 特定于诉讼情况模块
            if field == "【诉讼请求原文】【法院认为及判决结果原文】":
                if table.iloc[i+1,1] != "是否变更诉讼请求":
                    ret["是否变更诉讼请求"] = _2read(i, table, entity_list, details)
                    for key in ret["是否变更诉讼请求"].keys():
                        ret["是否变更诉讼请求"][key] = {
                        _CONTENTS[0]: None,
                        _CONTENTS[1]: None
                    }
            i += 1
        elif class_name in field:  # 不可迭代的类
            field = class_name
            # 特定于诉讼情况模块
            if field=="需返回债权实现费用":
                sub_fields = list(profiles[field]["起诉前"].keys())
                lens = len(sub_fields)
                ret["需返回债权实现费用"] = { "起诉前":{}, "起诉后":{}}
                for entity in entity_list:
                    ret["需返回债权实现费用"]["起诉前"] = _read_class( i, table, lens, sub_fields, entity_list, details )
                    ret["需返回债权实现费用"]["起诉后"] = _read_class( i+2, table, lens, sub_fields, entity_list, details )
                i += 2*lens
            else:
                sub_fields = list(profiles[field].keys())
                lens = len(sub_fields)
                ret[field] = {}
                for entity in entity_list:
                    ret[field] = _read_class( i, table, lens, sub_fields , entity_list, details)
                i += lens
            index_class += 1
        elif iter_name in field:
            # 按顺序获取当前可迭代字段
            field = iter_name
            ret[field], spans = _read_iterable( i, table, field, entity_list, details, profiles[field]["数字"] )
            i += spans
            index_iter += 1
    return ret

################################################读取工具#############################################################
# 读取Datacell中原告诉请部分的函数
def read_propose( start_row, end_row, table, entity_info ):
    entity_list = list(entity_info.keys())
    details = entity_info 
    profiles = _STRUCTUER[3][1]         # block常数字典结构
    return block_reader(start_row, end_row, entity_list, details, profiles, table)

# 读取Datacell中事实与抗辩部分的函数
def read_reality( start_row, end_row, table, entity_info ):
    entity_list = list(entity_info.keys())
    details = entity_info 
    profiles = _STRUCTUER[4][1]         # block常数字典结构
    return block_reader(start_row, end_row, entity_list, details, profiles, table)

# 读取Datacell中特殊部分的函数
def read_special( start_row, end_row, table, entity_info ):
    entity_list = list(entity_info.keys())
    details = entity_info    
    profiles = _STRUCTUER[5][1]         # block常数字典结构

    ret = {}
    classes = []
    for key in profiles.keys():      # 按顺序获取该block中所有可迭代对象
        classes.append( key )
    index_class = 0
    i = start_row
    while i<end_row:
        field = table.iloc[i,0]      # 实际字段名
        if field in classes:
            ret[field] = {}
            # 非可迭代字段，直接获取值
            sub_fields = list(profiles[field].keys())
            lens = len(sub_fields)
            for j in range(lens):
                sub_field = sub_fields[j]
                ret[field][sub_field] = _2read( i+j, table, entity_list, details )
            i += lens
            index_class += 1
    return ret

# 读取Datacell的函数
def get_DataCell( entity_info, table):
    json_table = OrderedDict()
    start_row = 0
    end_row = 0

    split_index = []
    for i in range( len(table) ):
        if table.iloc[i,1] == "【诉讼请求原文】【法院认为及判决结果原文】":
            start_row = i
        elif table.iloc[i, 1] == "【事实与理由原文】【辩称原文】【法院认定事实原文】":
            end_row = i
            split_index.append( end_row - start_row )
            json_table[_STRUCTUER[3][0]] = read_propose( start_row, end_row, table, entity_info )
            start_row = i
        elif table.iloc[i, 0] == "夫妻共同债务":
            end_row = i
            split_index.append( end_row - start_row )
            json_table[ _STRUCTUER[4][0]  ] = read_reality( start_row, end_row, table, entity_info )
            start_row = i
        elif table.iloc[i, 0] == "利率调整、认定":
            end_row = i
            split_index.append( end_row - start_row )
            json_table[ _STRUCTUER[5][0]  ] = read_special( start_row, end_row, table, entity_info )
            break
    return json_table, split_index



# 读取Datacell的函数：3_times
def get_DataCell_simple( entity_info, table):
    """
    # rows: 0是实体名字，2-31是是否变更诉讼请求，33-189借款目的与用途, 192-210夫妻共同债务，210结尾
    entity_info: 字典，type:[name, col_num]
    """
    json_table = OrderedDict()
    for i in range( 2, 190):
        if (i >=2 and i <=31) or (i >=33 and i <=189):    # 诉讼请求
            field_name = table.iloc[i, 1]
            json_table[field_name] = {}
            for entity_type in entity_info.keys():
                colu_num = entity_info[ entity_type ][1]
                raw_text = table.iloc[i, colu_num]
                value = _slot_reader( field_name, table.iloc[i, colu_num+1] )
                if pd.isna( raw_text ):
                    raw_text = "nan"
                json_table[field_name][entity_type]={
                    "原文": raw_text,
                    "取值": filter_value( value, field_name),
                }
    """
    specials = read_special( 192, 210, table, entity_info )
    json_table["法院对夫妻债务的认定"] = specials["夫妻共同债务"]["法院认定"]
    json_table["法院对砍头息的认定"] = specials["砍头息"]["法院认定"]
    json_table["法院对公司为股东担保的效力的认定"] = specials["公司为股东担保"]["法院认定"]
    json_table["债权取得类型"] = specials["债权/债务非原始取得"]["债权取得类型"]
    json_table["法院对主体资格与合同效力的认定"] = specials["出借人主体资格问题"]["法院认定"]
    json_table["法院对职业放贷人的认定"] = specials["职业放贷人"]["法院对效力的认定"]
    json_table["法院对是否属于互联网平台责任的认定"] = specials["互联网平台责任"]["法院认定"]
    json_table["法院对民事案件的处理程序"] = specials["民刑交叉"]["法院处理程序"]
    """
    return json_table




# 读取FirstColumn的函数
def get_FirstColumn( entity ):
    temp = {}
    for key in entity.keys():
        role_type = entity[key]['角色类型']
        role_column_num = entity[key]['列号']
        role_name = key
        if role_type =="法院" or role_type =="出借人（原告）" or role_column_num == 8:
            temp_role_type = role_type
        else:
            if role_column_num == 11:
                temp_role_type = role_type+"_2"
            elif role_column_num == 14:
                temp_role_type = role_type+"_3"
        temp[temp_role_type] = [role_name, role_column_num]
    return temp
    

if __name__ == "__main__":
    entity = {'法院': ['安徽省合肥市包河区人民法院', 2], '出借人（原告）': ['卢江平', 5], '借款人（被告）': ['刘维辉', 8]}