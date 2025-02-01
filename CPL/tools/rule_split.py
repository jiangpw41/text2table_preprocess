import sys
import os
import json
from typing import List
import re

from wayne_utils import load_data, save_data, get_ROOT_PATH

_ROOT_PATH = get_ROOT_PATH( 2, __file__)
from .regulation_lib import _SEPARATORS


def Firstlevel(original_string:str, separators:list = _SEPARATORS, index = None):  
    _SPECIAL_SEPARATOR = "<SJTU_IEEE_LAW>"
    ret = {}

    # 分割标题
    temp = list( filter(None, original_string.split("###") ))
    ret["标题"] = temp[0]
    original_string = temp[1]

    # 分隔正文与标题
    separator = separators[0][0]
    match = separator.search(original_string)
    if match:
        rep = match.group(0) + _SPECIAL_SEPARATOR
        original_string = original_string.replace(match.group(0) , rep, 1)
    else:
        print(f"{index} part {0} fail")
    
    # 插入附录分隔符
    separator = separators[0][3]
    match = separator.search(original_string)
    end_index = match.end()  # 获取匹配项结束索引（不包含）
    target_sep = "\\n"
    before = original_string[:end_index]
    rest =  original_string[end_index:]
    rest_lists = list( filter(None, rest.split( target_sep ) ))
    if len(rest_lists)==0:
        before = before
        rest_lists = []
    elif len( rest_lists ) == 1:
        line = rest_lists[0]
        flag = 0
        if len(line) > 10 or "附" in line or "本息" in line or "：" in line:
            flag = 1
        else:
            match_1 = _SEPARATORS[1][2].search(line)
            match_2 = _SEPARATORS[1][5].search(line)
            if match_1 and match_2:
                before = before+line
                rest_lists = []
            else:
                flag = 1
        if flag == 1:
            before = before
            rest_lists = rest_lists
    else:
        fis = 0
        for i in range(2):
            line = rest_lists[i]
            if len(line) > 10 or "附" in line or "本息" in line or "：" in line:
                break
            else:
                match_1 = _SEPARATORS[1][2].search(rest_lists[i])
                match_2 = _SEPARATORS[1][5].search(rest_lists[i])
                if match_1 and match_2:
                    fis += 1
                    continue
                else:
                    break
        before = before + "\\n".join(rest_lists[: fis])
        rest_lists = rest_lists[fis:]

    splited = list( filter(None, before.split(_SPECIAL_SEPARATOR) ))
    ret["开头"] = list( filter(None, splited[0].split("\\n") ))
    ret["正文"] = list( filter(None, splited[1].split("\\n") ))
    if "原告王星，男，" in ret["正文"][0]:
        temp = []
        main_core = ret["正文"][0].split("。")
        for line in main_core:
            if line.strip()!="":
                temp.append(line+"。" )
        temp.extend( ret["正文"][1:])
        ret["正文"] = temp
    ret["附录"] = rest_lists
    return ret

def tails( lists ):
    lens = len(lists)
    sep = _SEPARATORS[1][5]
    divider = 0

    ret = []
    for i in range(lens):
        index = lens-i-1
        line = lists[index]
        match = sep.search(line)
        if match:
            if line!="\n":
                ret.append( line )
            continue
        else:
            divider = index
            break
    ret2 = []
    for i in range( len(ret)):
        index = len(ret)-i-1
        ret2.append(ret[index])
    return lists[0:divider+1], ret2

def Secondlevel( data, seps=_SEPARATORS ):
    sep_1 =  seps[1][0]
    _zero = []
    ret = {}

    # 正文初始程序信息
    for i in range(len(data)):
    #for i in range(187,188):
        texts = data[ str(i) ]["正文"]
        _target = None
        for j in range( len(texts) ):
            match = sep_1.search(texts[j])
            if match:
                _target = j
                break
        if _target == None:
            _zero.append(i)
        else:
            # re1, tailss = 
            if _target==0:
                # 说明正文全在一行了
                temp_string = texts[0]
                temp_string = temp_string.replace( "？", "")
                temp_string = temp_string.replace( "。", "。<IIII>")
                temp_list = temp_string.split("<IIII>")
                for k in range( len(temp_list) ):
                    sub_string = temp_list[k]
                    match = sep_1.search(sub_string)
                    if match:
                        procedures = temp_list[:k+1]
                        restsss = temp_list[k+1:]
                        restsss.extend( texts[1:] )
                        zhong, tailss = tails( restsss )
            else:
                procedures = texts[0:_target+1]
                zhong, tailss = tails( texts[_target+1:] )

            ret[i] = {
                "程序信息" : procedures,
                "申辩证" : zhong,
                "末尾信息": tailss
            }
            data[ str(i) ]["正文"] = ret[i]
    # 末尾信息
    no_dou = seps[1][2]
    only_end = seps[1][3]
    only_mao = seps[1][4]
    no_ju = seps[1][5]
    indexs = _zero
    error = 0
    for i in indexs:
        parts = data[str(i)]["正文"]
        for j in range(len(parts)):
            line = parts[j]
            num_ju = line.count("。")
            num_court = line.count("本院认为")
            match_1 = only_end.search(line)  # 只有末尾有句号
            match_2 = only_mao.search(line)  # 只有一个冒号
            match_3 = no_dou.search(line)  # 没有逗号
            match_4 = no_ju.search(line)  # 没有句号
            if match_2:      # 冒号开头不超过10个字符
                continue
            else:
                if match_3 and match_4:   # 没有逗号也没有句号
                    continue
                elif match_1 and num_court==0:     # 只有末尾句号也成立
                    continue
                elif j==0 and num_ju==26:
                    lists = line.split("。")
                    head = lists[:7]
                    restss = lists[7:]
                    tail = parts[1:]
                    ret[i] = {
                        "程序信息" : head,
                        "申辩证" : restss,
                        "末尾信息" : tail
                    }
                    data[ str(i) ]["正文"] = ret[i]
                    break
                else:
                    divider = j
                    re1, re2 = tails( parts[j:] )
                    ret[i] = {
                        "程序信息" : parts[:j],
                        "申辩证" : re1,
                        "末尾信息" : re2
                    }
                    data[ str(i) ]["正文"] = ret[i]
                    break
        if divider==0:
            print(f"error {i}")
    return data

def SecModifiy( jsons_all ):
    new_jsons_all_new = []
    for i in range( len(jsons_all) ):
        temp_dict = {
            "标题" : jsons_all[ str(i) ]["标题"],
            "开头" : jsons_all[ str(i) ]["开头"],
            "附录" : jsons_all[ str(i) ]["附录"],
            "正文" : {},
        }
        current_json_core = jsons_all[ str(i) ]["正文"]
        new_procedure = []
        new_argue = []
        new_tail = []
        # 处理程序信息
        match_word = re.compile(r'\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:万)?元')
        for j in range(len(current_json_core["程序信息"])):
            matched_words = re.findall(match_word, current_json_core["程序信息"][j])
            if len(matched_words)>0:
                new_procedure = current_json_core["程序信息"][ : j]
                new_argue = current_json_core["程序信息"][ j: ]
                break
            else:
                new_procedure.append( current_json_core["程序信息"][j] )
        temp_dict["正文"]["程序信息"] = new_procedure
        # 处理申诉
        for j in range(len(current_json_core["申辩证"])):
            if "受理费" in current_json_core["申辩证"][j] and j >= len(current_json_core["申辩证"])-4:
                new_tail = current_json_core["申辩证"][ j: ]
                break
            else:
                new_argue.append( current_json_core["申辩证"][j] )
        temp_dict["正文"]["申辩证"] = new_argue
        new_tail.extend( current_json_core["末尾信息"] )
        temp_dict["正文"]["末尾信息"] = new_tail
        new_jsons_all_new.append( temp_dict )
    return new_jsons_all_new

def Thirdlevel( sec_json ):
    defandent = {
        "辩称":[],
        "答辩":[],
        "抗辩":[],
        "辩解":[],
    }
    court = {
        "本院认为":[],
        "认定":["辩称"],
        "查明":["辩称"],
        "经审查":[]
        
    }
    orders = [ defandent, court]
    split_list = []
    # 遍历每一份文档
    for i in range(  len(sec_json) ):
        texts = sec_json[i]["正文"]["申辩证"]
        temp = {}
        split_index = [ None, None ]
        start_index = 0                 # 每次遍角色历开始的序号
        # 遍历每一份文档的每句，需要处理原被告可能的缺失
        for j in range( len(texts )):
            if start_index == 2:        # 当开始序号=2时，说明角色遍历已经完成
                break
            line = texts[j]
            # 遍历两个角色
            for current_index in range( start_index, 2):
                current_entity = orders[ current_index ]
                for may_word in current_entity.keys():
                    if may_word in line:
                        flag = 0
                        for ban_word in current_entity[may_word]:
                            if ban_word in line:        # 有冲突词，匹配失败
                                flag=1
                                break
                        if flag==0:
                            # 没有禁用词
                            split_index[current_index] = j
                            start_index = current_index +1
                            break
        if split_index[1] == None:
            raise Exception( f"""第{i}份文档没有法院判决{split_index}""")
        temp["原告"] = texts[ : split_index[0]] if split_index[0]!=None else texts[0: split_index[1]]
        temp["被告"] = texts[ split_index[0]: split_index[1]] if split_index[0]!=None else []
        temp["法院"] = texts[ split_index[1]: ]
        sec_json[i]["正文"]["申辩证"] = temp
    return sec_json

def check( data, sep=_SEPARATORS[0][3]):
    _zero = 0
    _multi = 0
    for i in range(len(data)):
    #for i in range(540,541):
        count = 0
        matches = sep.finditer(data[i])  
        for match in matches:  
            count += 1
        if count == 0:
            _zero += 1
        if count > 1:
            _multi += 1
        print(f"Index {i} count {count}")
    print(f" _zero {_zero} _multi {_multi}")

def cpl_text_ruled_processor( ):
    #（1）路径检查与texts加载
    data_path = os.path.join(_ROOT_PATH, "pairs/texts.text")
    if not os.path.exists(data_path):  
        raise FileNotFoundError(f"Directory '{data_path}' does not exist.")
    dirs = os.path.join( _ROOT_PATH, "data/ruled_texts")
    if not os.path.exists(dirs):  
        os.makedirs(dirs)
    texts = load_data( data_path, "text" )

    #（2）一级拆分：拆分标题、开头、正文、附录
    saves = {}
    for i in range(len(texts)):
        saves[i] = Firstlevel(texts[i], _SEPARATORS, i)
    save_data( saves, os.path.join( dirs, 'texts_splited_A.json'))

    #（3）二级拆分：拆分正文为程序、申辩证、末尾信息
    data = load_data( os.path.join( dirs, 'texts_splited_A.json'), "json" )
    ret = Secondlevel( data )
    saves = SecModifiy( ret )
    save_data( saves, os.path.join( dirs, 'texts_splited_B.json'))

    #（4）三级拆分：拆分申辩证
    ret = Thirdlevel( saves )
    save_data( ret, os.path.join( dirs, 'texts_splited_C.json'))

if __name__ == "__main__":
    cpl_text_ruled_processor( )