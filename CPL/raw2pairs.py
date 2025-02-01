from wayne_utils import load_data, save_data, _PUNCATUATION_EN, _PUNCATUATION_ZH
import sys
import pandas as pd
import os
from tqdm import tqdm

_ROOT_PATH = "/home/jiangpeiwen2/jiangpeiwen2/text2table_preprocess/CPL"

# 列表出所有的文本和表格路径
first_data_path = os.path.join( _ROOT_PATH, "raw/FirstCollection")
second_data_path = os.path.join( _ROOT_PATH, "raw/SecondCollection")
first_doc_file_list = os.listdir( os.path.join(first_data_path, "doc") )
first_excel_file_list = os.listdir( os.path.join(first_data_path, "excel") )
second_doc_file_list = os.listdir( os.path.join(second_data_path, "doc") )
second_excel_file_list = os.listdir( os.path.join(second_data_path, "excel") )



def get_sorted_file_names( file_list, target_path ):
    """对文件名列表根据文件名进行排序
    param: file_list, 文件列表
    param: target_path, 根目录，可与文件名组合成完整路径
    output: list_sorted, 排序完毕的返回文件名列表
    """
    # 用.分隔符获取每个文件名的编号并Int化
    split_list = []
    for i in range(len(file_list)):
        temp = file_list[i].split(".")
        temp[0] = int(temp[0])
        split_list.append( temp )
    # 根据文件名编号对整个列表进行排序，并将编号变回字符串并与文件名合并
    list_sorted = sorted(split_list, key=lambda x: x[0])
    for i in range(len(list_sorted)):
        list_sorted[i][0] = str(list_sorted[i][0])
        list_sorted[i] = ".".join(list_sorted[i])
    # 对排序重组后的列表中的每个文件名进行存在性检查
    for i in range(len(list_sorted)):
        total_path = os.path.join(target_path, list_sorted[i] )
        if not os.path.exists(total_path):
            raise Exception(f"Some problems on {i}: {total_path}")
    return list_sorted

def get_file_name_pairs():
    """获取文本、表格文件名对"""
    sorted_first_doc_list = get_sorted_file_names(first_doc_file_list, os.path.join(first_data_path, "doc") )
    sorted_first_excel_list = get_sorted_file_names(first_excel_file_list, os.path.join(first_data_path, "excel") )
    sorted_second_doc_list = get_sorted_file_names(second_doc_file_list, os.path.join(second_data_path, "doc") )
    sorted_second_excel_list = get_sorted_file_names(second_excel_file_list, os.path.join(second_data_path, "excel") )

    text_data_pairs_1 = []
    for i in range( len(sorted_first_doc_list) ):
        text_data_pairs_1.append( (sorted_first_doc_list[i], sorted_first_excel_list[i]) )
    text_data_pairs_2 = []
    for i in range( len(sorted_second_doc_list) ):
        text_data_pairs_2.append( (sorted_second_doc_list[i], sorted_second_excel_list[i]) )
    return text_data_pairs_1, text_data_pairs_2

def get_data_pair( ):
    """获取两个子集850分数据对"""
    text_data_pairs_1, text_data_pairs_2 = get_file_name_pairs()
    file_name_pair = []
    data_pair = []
    for i, lists in enumerate( [text_data_pairs_1, text_data_pairs_2]):
        
        prefix_path = os.path.join(_ROOT_PATH, f"raw/FirstCollection") if i == 0 else os.path.join(_ROOT_PATH, f"raw/SecondCollection")
        for j in tqdm( range(len(lists)), desc = f"处理第{i}次采集的数据集"):
            file_name_pair.append( (lists[j][0], lists[j][1]))
            text = load_data( os.path.join( prefix_path, f"doc/{lists[j][0]}" ), "docx")
            table = load_data( os.path.join( prefix_path, f"excel/{lists[j][1]}"), "excel")
            data_pair.append( (text, table))
    return data_pair, file_name_pair

data_pair, file_name_pair = get_data_pair( )

"""
过滤非单笔交易，剩下703份
"""
def get_court_name( text_list ):
    "从文本获取法庭名"
    court_name = {}
    no_name = []
    for i in range(len(text_list)):
        splits = text_list[i].split("\\n")
        flag=0
        for j in range(9):
            if "法院" in splits[j]:
                name = splits[j]
                if "审理法院：" in name:
                    name = name[5:]
                elif "民事判决书" in name:
                    name = name[:-5]
                elif "中华人民共和国" in name:
                    name = name[7:]
                
                if name.startswith("合肥市"):
                    name = "安徽省"+name
                court_name[i] = name
                flag=1
                break
        if flag==0:
            no_name.append( i )
    court_name[561] = "浙江省温州市中级人民法院"
    court_name[562] = "安徽省合肥市中级人民法院"
    court_name[793] = "浙江省温州市中级人民法院"
    return court_name

def get_names_from_excel( table ):
    """从表格中获取entity名称"""
    role_map = {
        "出借人（原告）姓名或名称": (0, "出借人（原告）"),
        "借款人（被告）姓名或名称": (1, "借款人（被告）"),
        "担保人（被告）姓名或名称": (2, "担保人（被告）"),
        "【其他诉讼参与人】姓名或名称": (3, "其他诉讼参与人")
        }
    # 除了法院，其他都有“：”：[703, 695, 121, 55]
    count = [0, 0, 0, 0]
    ret = []
    for j in range(2, len(table.iloc[0]), 3 ):
        if j ==2:
            ret.append( ("法院", table.iloc[0, j+1]))
        else:
            fields = table.iloc[0, j].split("：")
            filed_name = role_map[fields[0]][1]
            field_index = role_map[fields[0]][0]
            if fields[1]!="":
                # 说明名字和字段在一起了
                ret.append( (filed_name, fields[1]))
                count[field_index] +=1
            elif not pd.isna(table.iloc[0, j+1]):
                # 如果名字不在一起但在后一格
                ret.append( (filed_name, table.iloc[0, j+1]))
                count[field_index] +=1
    return ret, count

def single_lending_filter( data_pair, file_name_pair ):
    """过滤其中147份没有原告姓名的（说明不是单次单笔），剩下703份"""
    filter_pairs = []
    filter_pairs_names = []
    multi_lending_index = []
    # 法院列2，原告列5，被告列8，担保11，其他14
    for i in range(len(data_pair)):
        table = data_pair[i][1]
        
        if not pd.isna(table.iloc[0, 6]):                   # 原告姓名与字段分开的638
            # 如果原告名在相邻格
            filter_pairs.append( data_pair[i] )
            filter_pairs_names.append( file_name_pair[i] )
        else:
            # 判断是否在同一格
            string_name = table.iloc[0, 5].split("：")      # 没有原告姓名的147
            if string_name[1]!="":
                # 原告姓名与字段一个格子的65
                filter_pairs.append( data_pair[i] )
            else:
                multi_lending_index.append( i )
                filter_pairs_names.append( file_name_pair[i] )
    return filter_pairs, multi_lending_index, filter_pairs_names

filter_pairs, multi_lending_index, filter_pairs_names =  single_lending_filter( data_pair, file_name_pair )      # 703, 143，万一以后要处理非单笔可以直接索引
# first_column, count = get_names_from_excel( filter_pairs[0][1] )


"""
处理并保存文本和表格
"""

# 处理并保存文本
def docx_processor( text_table_pair, filter_pairs_names, save_path ):
    text_list = []
    with open( save_path, 'w') as file:
        for i in range( len(text_table_pair) ):
            text = text_table_pair[i][0]
            text = text.replace(" ", "").replace("\u3000", "").replace("\n\n\n", "\n").replace("\n\n", "\n").replace("\n", "\\n") # 特殊字符串清洗
            for p in range( len(_PUNCATUATION_EN) ):                                # 英字符转中
                text = text.replace(_PUNCATUATION_EN[p], _PUNCATUATION_ZH[p])
            if i<len(text_table_pair)-1:
                file.write(filter_pairs_names[i][0]+"###"+text + '\n')
            else:
                file.write(filter_pairs_names[i][0]+"###"+text )   
            text_list.append( text )
    return text_list
text_save_path = os.path.join(_ROOT_PATH, f"raw/texts.text")
text_list = docx_processor( filter_pairs, filter_pairs_names, text_save_path )

# 处理表格
from tools.excel_reader import get_FirstColumn, get_DataCell_simple
def excel_processor( text_table_pair, json_data):
    new_table_list = {}
    new_table_split_index_list = {}
    for i in tqdm( range(len(text_table_pair)), desc=f"Constructing json"):
        entity = json_data[str(i)]
        table = text_table_pair[i][1]
        single_dict = {}
        single_dict[ "first_column"] = get_FirstColumn( entity )
        single_dict[ "data_cell"] = get_DataCell_simple( single_dict[ "first_column"], table)
        new_table_list[i] = single_dict
        # new_table_split_index_list[i] = split_index
    save_data( new_table_list, os.path.join(_ROOT_PATH, f"pairs/tables.json") )
    return new_table_list # , new_table_split_index_list

entity_json_data = load_data( os.path.join( _ROOT_PATH, "raw/entity_name_703.json"), "json")
new_table_list = excel_processor( filter_pairs, entity_json_data)