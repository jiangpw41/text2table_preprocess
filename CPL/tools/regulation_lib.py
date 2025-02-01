import re

# 创建一个小的字符集来匹配年份、月份和日期  
year_chars = r'一二三四五六七八九十〇O零'  
month_chars = r'元一二三四五六七八九十'  
day_chars = month_chars  

regulations = {
    "Block" : [ 
        re.compile(r'(\d{4})(.{1,20})号\\n', re.DOTALL),       # 案号匹配，全部
        re.compile(r'\\n附(.{0,30})(\\n|：)', re.DOTALL),        # 附录部分分隔符
        re.compile(r'清单\\n', re.DOTALL)                   # 一个匹配
        ],
    "Subblock":[
        re.compile( r'，(男|女)(，|。)'),                    # Total: 851, zero 325, multi 500
        re.compile( r'审理终结。'),                       # Total: 851, zero 64, multi 0
        re.compile(r'(原告|申请人)(.{2,20})(提起诉讼|诉称|请求|申请)', re.DOTALL),     # 第一块
        re.compile(r'^原告(.*?)诉讼请求', re.DOTALL),                     # 第一块
        re.compile(r'^(?!.*。).*$'),                    # 不存在句号的单独句子
        re.compile(r'^(?!.*，).*$'),                    # 不存在逗号号的单独句子
        re.compile(r'^[^。]*。$') ,                      # 只存在句尾一个句号的句子
        re.compile(r'^.{0,10}：(.*)$') ,        # 句子中冒号前最多是个字符
        "如不服本判决",                      # Total: 851, zero 27, multi 0
        "判决如下：",                         # Total: 851, zero 21, multi 0
        "事实和理由：",                        # Total: 851, zero 661, multi 0
    ],
    "Element" : [
        re.compile(rf'([{year_chars}]+年)([{month_chars}]+月)([{day_chars}]+日)(\\n|\\)') ,              # 末尾年月日匹配，Total: 851, zero 0, multi 0
        re.compile(r'\d{4}年'),
        re.compile(r'([1-9]|1[0-2])月')
    ]
}
    
_SEPARATORS = [ 
    [
        regulations["Block"][0], 
        regulations["Block"][1],
        regulations["Block"][2],
        regulations["Element"][0]
    ], 
    [
        regulations["Subblock"][1],
        regulations["Subblock"][2],
        regulations["Subblock"][5],
        regulations["Subblock"][6],
        regulations["Subblock"][7],
        regulations["Subblock"][4],
        
    ] 
]
